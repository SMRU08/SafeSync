#!/usr/bin/env python3
"""
cleanup_retention.py — SafeSync Phase 10 Step 4
Database Retention Cleanup & Maintenance Utility

Safely removes historical records exceeding retention thresholds without deleting:
- Active incidents (OPEN, ACKNOWLEDGED)
- Unresolved hazard events (SUSPECTED, CONFIRMED)
- Active worker tracks (is_active == True)

Supports:
- --dry-run (default): Simulates cleanup, prints records that would be removed
- --execute: Performs safe deletion in a single transaction with rollback on error
- --days <N>: Overrides all retention windows (for testing or emergency pruning)
- --vacuum: Optionally runs PRAGMA incremental_vacuum or VACUUM after cleanup
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Setup path so script can import app modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from app.config import get_settings
    from app.database.session import get_db, engine, Base
    from app.models.risk_alert import Incident, Alert, AlertHistory
    from app.models.hazard import HazardEvent, HazardObservation
    from app.models.compliance import WorkerTracking, PPEObservation, ComplianceObservation
    from app.models.evidence import EvidenceItem
    from app.services.evidence_manager import EvidenceManager
except ImportError:
    from backend.app.config import get_settings
    from backend.app.database.session import get_db, engine, Base
    from backend.app.models.risk_alert import Incident, Alert, AlertHistory
    from backend.app.models.hazard import HazardEvent, HazardObservation
    from backend.app.models.compliance import WorkerTracking, PPEObservation, ComplianceObservation
    from backend.app.models.evidence import EvidenceItem
    from backend.app.services.evidence_manager import EvidenceManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("cleanup_retention")


def parse_args():
    parser = argparse.ArgumentParser(
        description="SafeSync Safe Database Retention Cleanup"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Simulate cleanup and print eligible counts without deleting (default: True)"
    )
    group.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Execute database deletion within a strict transaction"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Override all retention windows to N days (default: read from production.yaml)"
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        default=False,
        help="Run VACUUM on SQLite database after execution"
    )
    return parser.parse_args()


def get_retention_policy(override_days: int = None) -> dict:
    """Reads retention rules from config or applies CLI override."""
    settings = get_settings()
    ret_cfg = settings.raw_config.get("retention", {})

    incidents_days = override_days or ret_cfg.get("incidents_days", 30)
    alerts_days = override_days or ret_cfg.get("alerts_days", 30)
    alert_history_days = override_days or ret_cfg.get("alert_history_days", 90)
    hazard_events_days = override_days or ret_cfg.get("hazard_events_days", 30)
    worker_days = override_days or ret_cfg.get("worker_compliance_events_days", 30)

    now = datetime.now(timezone.utc)
    return {
        "incidents_cutoff": now - timedelta(days=incidents_days),
        "alerts_cutoff": now - timedelta(days=alerts_days),
        "alert_history_cutoff": now - timedelta(days=alert_history_days),
        "hazard_events_cutoff": now - timedelta(days=hazard_events_days),
        "worker_cutoff": now - timedelta(days=worker_days),
        "incidents_days": incidents_days,
        "alerts_days": alerts_days,
        "alert_history_days": alert_history_days,
        "hazard_events_days": hazard_events_days,
        "worker_days": worker_days,
    }


def analyze_candidates(session, policy):
    """
    Finds records eligible for deletion according to strict safety rules:
    - Incidents: resolved or dismissed only, older than cutoff
    - Alerts: resolved or dismissed only, older than cutoff
    - AlertHistory: older than cutoff
    - HazardEvents: CLEARED or NO_HAZARD only, older than cutoff
    - WorkerTracking: inactive only, older than cutoff
    """
    # 1. Incidents
    eligible_incidents = session.query(Incident).filter(
        Incident.created_at < policy["incidents_cutoff"],
        Incident.status.in_(["RESOLVED", "DISMISSED"])
    ).all()
    eligible_incident_ids = [inc.incident_id for inc in eligible_incidents]

    # Active incidents that MUST be preserved
    active_incidents_count = session.query(Incident).filter(
        Incident.status.in_(["OPEN", "ACKNOWLEDGED"])
    ).count()

    # 2. Alerts: either linked to eligible incidents OR resolved/dismissed older than cutoff
    eligible_alerts = session.query(Alert).filter(
        Alert.created_at < policy["alerts_cutoff"],
        Alert.status.in_(["RESOLVED", "DISMISSED"])
    ).all()
    eligible_alert_ids = [a.alert_id for a in eligible_alerts]

    # 3. Alert History
    eligible_history = session.query(AlertHistory).filter(
        AlertHistory.timestamp < policy["alert_history_cutoff"]
    ).all()

    # 4. Hazard Events (and child observations)
    eligible_hazards = session.query(HazardEvent).filter(
        HazardEvent.last_seen < policy["hazard_events_cutoff"],
        HazardEvent.state.in_(["CLEARED", "NO_HAZARD"])
    ).all()
    eligible_hazard_pks = [h.id for h in eligible_hazards]

    active_hazards_count = session.query(HazardEvent).filter(
        HazardEvent.state.in_(["SUSPECTED", "CONFIRMED"])
    ).count()

    # Child hazard observations
    eligible_hazard_obs_count = 0
    if eligible_hazard_pks:
        eligible_hazard_obs_count = session.query(HazardObservation).filter(
            HazardObservation.hazard_event_id.in_(eligible_hazard_pks)
        ).count()

    # 5. Worker Tracking & Compliance Observations
    eligible_workers = session.query(WorkerTracking).filter(
        WorkerTracking.last_seen < policy["worker_cutoff"],
        WorkerTracking.is_active == False  # noqa: E712
    ).all()
    eligible_worker_pks = [w.id for w in eligible_workers]

    active_workers_count = session.query(WorkerTracking).filter(
        WorkerTracking.is_active == True  # noqa: E712
    ).count()

    eligible_compliance_obs_count = 0
    if eligible_worker_pks:
        eligible_compliance_obs_count = session.query(ComplianceObservation).filter(
            ComplianceObservation.worker_tracking_id.in_(eligible_worker_pks)
        ).count()

    # Oldest timestamps
    oldest_incident = session.query(Incident.created_at).order_by(Incident.created_at.asc()).first()
    oldest_alert = session.query(Alert.created_at).order_by(Alert.created_at.asc()).first()
    oldest_hazard = session.query(HazardEvent.last_seen).order_by(HazardEvent.last_seen.asc()).first()

    return {
        "eligible_incidents": eligible_incidents,
        "eligible_incident_ids": eligible_incident_ids,
        "active_incidents_count": active_incidents_count,
        "eligible_alerts": eligible_alerts,
        "eligible_alert_ids": eligible_alert_ids,
        "eligible_history_count": len(eligible_history),
        "eligible_history": eligible_history,
        "eligible_hazards": eligible_hazards,
        "eligible_hazard_pks": eligible_hazard_pks,
        "active_hazards_count": active_hazards_count,
        "eligible_hazard_obs_count": eligible_hazard_obs_count,
        "eligible_workers": eligible_workers,
        "eligible_worker_pks": eligible_worker_pks,
        "active_workers_count": active_workers_count,
        "eligible_compliance_obs_count": eligible_compliance_obs_count,
        "oldest_incident": oldest_incident[0] if oldest_incident else None,
        "oldest_alert": oldest_alert[0] if oldest_alert else None,
        "oldest_hazard": oldest_hazard[0] if oldest_hazard else None,
    }


def run_cleanup(execute: bool = False, override_days: int = None, vacuum: bool = False, session_override=None):
    """
    Main retention cleanup workflow.
    If session_override is provided, uses that session; otherwise acquires from get_db().
    """
    policy = get_retention_policy(override_days)
    mode = "EXECUTE" if execute else "DRY-RUN"

    logger.info("=" * 60)
    logger.info(f"SafeSync RETENTION CLEANUP — MODE: {mode}")
    logger.info("=" * 60)
    logger.info(f"Policy: Incidents={policy['incidents_days']}d, Alerts={policy['alerts_days']}d, "
                f"History={policy['alert_history_days']}d, Hazards={policy['hazard_events_days']}d, "
                f"Workers={policy['worker_days']}d")

    close_session_at_end = False
    if session_override is not None:
        session = session_override
    else:
        session_gen = get_db()
        session = next(session_gen)
        close_session_at_end = True

    try:
        candidates = analyze_candidates(session, policy)

        logger.info(f"Candidates for cleanup:")
        logger.info(f"  • Resolved/Dismissed Incidents: {len(candidates['eligible_incidents'])} (Preserved Active: {candidates['active_incidents_count']})")
        logger.info(f"  • Resolved/Dismissed Alerts:    {len(candidates['eligible_alerts'])}")
        logger.info(f"  • Alert History Logs:           {candidates['eligible_history_count']}")
        logger.info(f"  • Cleared Hazard Events:        {len(candidates['eligible_hazards'])} (Preserved Active: {candidates['active_hazards_count']})")
        logger.info(f"  • Hazard Child Observations:    {candidates['eligible_hazard_obs_count']}")
        logger.info(f"  • Inactive Worker Tracks:       {len(candidates['eligible_workers'])} (Preserved Active: {candidates['active_workers_count']})")
        logger.info(f"  • Compliance Child Observations:{candidates['eligible_compliance_obs_count']}")

        if candidates["oldest_incident"]:
            logger.info(f"Oldest incident timestamp: {candidates['oldest_incident']}")
        if candidates["oldest_alert"]:
            logger.info(f"Oldest alert timestamp:    {candidates['oldest_alert']}")

        total_eligible = (
            len(candidates["eligible_incidents"]) +
            len(candidates["eligible_alerts"]) +
            candidates["eligible_history_count"] +
            len(candidates["eligible_hazards"]) +
            candidates["eligible_hazard_obs_count"] +
            len(candidates["eligible_workers"]) +
            candidates["eligible_compliance_obs_count"]
        )

        if not execute:
            logger.info("DRY-RUN completed. No database records were modified or deleted.")
            return {
                "status": "dry_run_complete",
                "total_eligible": total_eligible,
                "candidates": candidates
            }

        if total_eligible == 0:
            logger.info("No eligible records found matching retention criteria. Database clean.")
            return {
                "status": "no_records_eligible",
                "total_deleted": 0
            }

        # Safe Deletion in reverse dependency order
        # 1. Alert History
        if candidates["eligible_history"]:
            for h in candidates["eligible_history"]:
                session.delete(h)

        # 2. Alerts
        if candidates["eligible_alerts"]:
            for a in candidates["eligible_alerts"]:
                session.delete(a)

        # 3. Incidents (cascades any remaining child alerts and evidence items)
        if candidates["eligible_incidents"]:
            ev_mgr = EvidenceManager.get_instance()
            for inc in candidates["eligible_incidents"]:
                for ev in inc.evidence_items:
                    try:
                        p = ev_mgr.resolve_secure_path(ev.file_path)
                        if p.is_file():
                            p.unlink()
                    except Exception as ev_err:
                        logger.warning("Could not unlink evidence file %s: %s", ev.file_path, ev_err)
                session.delete(inc)

        # 4. Hazard Events (cascades HazardObservation via ORM cascade="all, delete-orphan")
        if candidates["eligible_hazards"]:
            for h in candidates["eligible_hazards"]:
                session.delete(h)

        # 5. Worker Tracking (cascades ComplianceObservation via ORM cascade="all, delete-orphan")
        if candidates["eligible_workers"]:
            for w in candidates["eligible_workers"]:
                session.delete(w)

        session.commit()
        logger.info(f"SUCCESS: Committed deletion of {total_eligible} eligible records.")

        if vacuum:
            logger.info("Executing SQLite VACUUM to reclaim storage...")
            session.execute("VACUUM;")
            logger.info("SQLite VACUUM complete.")

        return {
            "status": "success",
            "total_deleted": total_eligible
        }

    except Exception as exc:
        session.rollback()
        logger.error(f"ERROR during retention cleanup: {exc}", exc_info=True)
        raise
    finally:
        if close_session_at_end:
            session.close()


if __name__ == "__main__":
    args = parse_args()
    execute_flag = args.execute and not args.dry_run
    run_cleanup(
        execute=execute_flag,
        override_days=args.days,
        vacuum=args.vacuum
    )
