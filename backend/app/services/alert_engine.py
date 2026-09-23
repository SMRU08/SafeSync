"""
alert_engine.py — RAKSHYA VISION Phase 7
Smart Alert Management, Incident Generation, Deduplication, Cooldown, and Escalation Engine.
Integrates RiskEngine and EventBroadcaster with database persistence.
"""

import os
import yaml
import uuid
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

try:
    from app.ai.risk.schemas import (
        EventType,
        RiskLevel,
        AlarmPriority,
        IncidentStatus,
        AlertStatus,
        NormalizedSafetyEvent,
        RiskScoreBreakdown,
        IncidentSchema,
        AlertSchema,
        RiskSummaryResponse,
    )
    from app.services.risk_engine import RiskEngine
    from app.services.event_broadcaster import broadcaster
    from app.models.risk_alert import Incident, Alert, AlertHistory
    from app.models.evidence import EvidenceItem
    from app.services.alert_providers.registry import ProviderRegistry
    from app.services.alert_providers.base import AlertNotificationPayload
    from app.services.evidence_manager import EvidenceManager
    from app.services.metrics import MetricsCollector
except ImportError:
    from backend.app.ai.risk.schemas import (
        EventType,
        RiskLevel,
        AlarmPriority,
        IncidentStatus,
        AlertStatus,
        NormalizedSafetyEvent,
        RiskScoreBreakdown,
        IncidentSchema,
        AlertSchema,
        RiskSummaryResponse,
    )
    from backend.app.services.risk_engine import RiskEngine
    from backend.app.services.event_broadcaster import broadcaster
    from backend.app.models.risk_alert import Incident, Alert, AlertHistory
    from backend.app.models.evidence import EvidenceItem
    from backend.app.services.alert_providers.registry import ProviderRegistry
    from backend.app.services.alert_providers.base import AlertNotificationPayload
    from backend.app.services.evidence_manager import EvidenceManager
    from backend.app.services.metrics import MetricsCollector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_ALERT_POLICY = os.path.join(ROOT, "configs", "alert_policy.yaml")
log = logging.getLogger(__name__)


def load_alert_policy(policy_path: Optional[str] = None) -> Dict[str, Any]:
    path = policy_path or DEFAULT_ALERT_POLICY
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


class AlertEngine:
    """
    Coordinates incident management, alert prioritization, deduplication, cooldowns, and escalation.
    """

    def __init__(
        self,
        risk_engine: Optional[RiskEngine] = None,
        alert_policy_path: Optional[str] = None,
    ):
        self.risk_engine = risk_engine or RiskEngine()
        self.policy = load_alert_policy(alert_policy_path)
        self.cooldowns = self.policy.get("cooldown_seconds", {
            "missing_helmet": 60,
            "missing_safety_vest": 60,
            "missing_gloves": 90,
            "missing_safety_footwear": 90,
            "smoke": 45,
            "fire": 30,
            "multiple_hazards": 30,
            "default": 60,
        })
        self.escalation_cfg = self.policy.get("escalation", {})
        self.escalation_enabled = bool(self.escalation_cfg.get("enabled", True))
        self.escalation_persistence_sec = float(self.escalation_cfg.get("persistence_threshold_seconds", 30.0))

        # In-memory tracking for deduplication & cooldowns
        # Map: deduplication_key -> (incident_id, alert_id, last_alert_time, current_severity)
        self._active_alerts_cache: Dict[str, Dict[str, Any]] = {}

    def _get_cooldown_for_event(self, event_type: EventType) -> float:
        mapping = {
            EventType.MISSING_HELMET: "missing_helmet",
            EventType.MISSING_SAFETY_VEST: "missing_safety_vest",
            EventType.MISSING_GLOVES: "missing_gloves",
            EventType.MISSING_SAFETY_FOOTWEAR: "missing_footwear",
            EventType.SMOKE_DETECTED: "smoke",
            EventType.FIRE_DETECTED: "fire",
            EventType.MULTIPLE_HAZARDS: "multiple_hazards",
        }
        key = mapping.get(event_type, "default")
        return float(self.cooldowns.get(key, self.cooldowns.get("default", 60)))

    def _make_dedup_key(self, event: NormalizedSafetyEvent) -> str:
        target = f"worker_{event.track_id}" if event.track_id is not None else f"hazard_{event.hazard_event_id or 'env'}"
        return f"{event.event_type.value}:{event.camera_id}:{target}"

    def _get_priority_for_event(self, event: NormalizedSafetyEvent, risk: RiskScoreBreakdown) -> Tuple[AlarmPriority, bool]:
        """
        Determines the alert priority (P0-P3) and whether an audible siren should be sounded.
        - P0 (CRITICAL): Confirmed Fire, Dual/Multi-Hazard Emergency (Audible Siren = True)
        - P1 (HIGH): Confirmed Smoke Plume (Audible Siren = True)
        - P2 (MEDIUM): Confirmed PPE Violation (Visual Dashboard Alert, Audible Siren = False)
        - P3 (LOW): Camera Offline, System Advisory (Audible Siren = False)
        """
        if event.details and "priority" in event.details:
            try:
                p_enum = AlarmPriority(event.details["priority"])
                is_audible = bool(event.details.get("audible", p_enum in (AlarmPriority.P0, AlarmPriority.P1)))
                return p_enum, is_audible
            except Exception:
                pass

        if event.event_type in (EventType.FIRE_DETECTED, EventType.MULTIPLE_HAZARDS):
            return AlarmPriority.P0, True
        elif event.event_type == EventType.SMOKE_DETECTED:
            if event.duration_seconds >= 10.0 or risk.risk_level == RiskLevel.CRITICAL:
                return AlarmPriority.P0, True
            return AlarmPriority.P1, True
        elif event.event_type in (
            EventType.MISSING_HELMET,
            EventType.MISSING_SAFETY_VEST,
            EventType.MISSING_GLOVES,
            EventType.MISSING_SAFETY_FOOTWEAR,
            EventType.PPE_VIOLATION,
        ):
            return AlarmPriority.P2, False
        elif event.event_type in (EventType.CAMERA_FAILURE, EventType.SYSTEM_FAILURE):
            return AlarmPriority.P3, False
        return AlarmPriority.P3, False

    def compose_alert_message(self, event: NormalizedSafetyEvent, risk_breakdown: RiskScoreBreakdown) -> Tuple[str, str]:
        """
        Synthesizes human-readable alert title and message.
        """
        zone_str = f" in {event.zone_id}" if event.zone_id and event.zone_id != "UNKNOWN" else ""
        cam_str = f" on {event.camera_id}" if event.camera_id else ""

        if event.event_type == EventType.MISSING_HELMET:
            title = "PPE Compliance — Missing Helmet"
            msg = f"Confirmed missing helmet detected for Worker #{event.track_id}{zone_str}{cam_str}."
        elif event.event_type == EventType.MISSING_SAFETY_VEST:
            title = "PPE Compliance — Missing Safety Vest"
            msg = f"Confirmed missing safety vest detected for Worker #{event.track_id}{zone_str}{cam_str}."
        elif event.event_type == EventType.MISSING_GLOVES:
            title = "PPE Compliance — Missing Protective Gloves"
            msg = f"Confirmed missing gloves detected for Worker #{event.track_id}{zone_str}{cam_str}."
        elif event.event_type == EventType.MISSING_SAFETY_FOOTWEAR:
            title = "PPE Compliance — Missing Safety Footwear"
            msg = f"Confirmed missing footwear detected for Worker #{event.track_id}{zone_str}{cam_str}."
        elif event.event_type == EventType.FIRE_DETECTED:
            title = "Environmental Hazard — Fire Detected"
            msg = f"Confirmed active flame combustion detected{cam_str}{zone_str}."
        elif event.event_type == EventType.SMOKE_DETECTED:
            title = "Environmental Hazard — Smoke Detected"
            msg = f"Confirmed persistent smoke plume detected{cam_str}{zone_str}."
        elif event.event_type == EventType.MULTIPLE_HAZARDS:
            title = "Emergency Hazard — Multiple Simultaneous Hazards"
            msg = f"Multiple safety hazards detected concurrently{cam_str}{zone_str}."
        elif event.event_type == EventType.CAMERA_FAILURE:
            title = "System Advisory — Camera Failure"
            msg = f"Camera connectivity or feed failure on {event.camera_id}."
        else:
            title = f"Safety Advisory — {event.event_type.value}"
            msg = f"Safety event '{event.event_type.value}' observed{cam_str}{zone_str}."

        return title, msg

    def process_event(
        self,
        event: NormalizedSafetyEvent,
        db: Optional[Session] = None,
    ) -> Tuple[Optional[AlertSchema], Optional[IncidentSchema], str]:
        """
        Processes a normalized event through risk evaluation, incident grouping,
        cooldown checks, escalation logic, and persistence.

        Returns:
            - AlertSchema (if created or escalated)
            - IncidentSchema
            - action string ('CREATED', 'DEDUPLICATED', 'COOLDOWN_SUPPRESSED', 'ESCALATED')
        """
        now = datetime.now(timezone.utc)
        dedup_key = self._make_dedup_key(event)

        # 1. Evaluate Risk Score
        risk = self.risk_engine.evaluate(
            event_type=event.event_type,
            duration_seconds=event.duration_seconds,
            affected_workers_count=1 if event.track_id is not None else 0,
            zone_id=event.zone_id,
            is_multi_hazard=(event.event_type == EventType.MULTIPLE_HAZARDS),
        )

        # 2. Find or Create Incident
        db_incident: Optional[Incident] = None
        incident_id = str(uuid.uuid4())
        affected_list = [event.track_id] if event.track_id is not None else []

        if db is not None:
            # Look for existing open incident matching deduplication criteria
            cached = self._active_alerts_cache.get(dedup_key)
            if cached:
                db_incident = db.query(Incident).filter(
                    Incident.incident_id == cached["incident_id"],
                    Incident.status.in_(["OPEN", "ACKNOWLEDGED"])
                ).first()

            if db_incident:
                # Update existing incident
                incident_id = db_incident.incident_id
                db_incident.updated_at = now
                db_incident.risk_score = max(db_incident.risk_score, risk.risk_score)
                db_incident.risk_level = risk.risk_level.value
                db_incident.factors_json = json.dumps(risk.factors)
                try:
                    curr_tracks = json.loads(db_incident.affected_tracks)
                    if event.track_id is not None and event.track_id not in curr_tracks:
                        curr_tracks.append(event.track_id)
                        db_incident.affected_tracks = json.dumps(curr_tracks)
                        affected_list = curr_tracks
                except Exception:
                    pass
            else:
                # Create new incident
                db_incident = Incident(
                    incident_id=incident_id,
                    status=IncidentStatus.OPEN.value,
                    event_types=event.event_type.value,
                    camera_id=event.camera_id,
                    zone_id=event.zone_id,
                    affected_tracks=json.dumps(affected_list),
                    risk_score=risk.risk_score,
                    risk_level=risk.risk_level.value,
                    factors_json=json.dumps(risk.factors),
                    created_at=now,
                    updated_at=now,
                )
                db.add(db_incident)
                db.flush()
                broadcaster.broadcast("IncidentCreated", {
                    "incident_id": incident_id,
                    "event_type": event.event_type.value,
                    "camera_id": event.camera_id,
                    "zone_id": event.zone_id,
                    "risk_level": risk.risk_level.value,
                })
                try:
                    EvidenceManager.get_instance().capture_incident_evidence(
                        incident_id=incident_id,
                        camera_id=event.camera_id,
                        frame=None,
                        annotations={"risk_score": risk.risk_score, "event_type": event.event_type.value},
                        db=db,
                    )
                except Exception as ev_err:
                    log.debug("Fault-isolated evidence capture skipped: %s", ev_err)

                try:
                    MetricsCollector.get_instance().increment_counter(
                        "rakshya_incidents_total",
                        labels={"risk_level": risk.risk_level.value, "camera_id": event.camera_id},
                    )
                except Exception:
                    pass

        incident_schema = IncidentSchema(
            incident_id=incident_id,
            timestamp=now.isoformat(),
            camera_id=event.camera_id,
            zone_id=event.zone_id,
            event_types=[event.event_type],
            affected_tracks=affected_list,
            risk_score=risk.risk_score,
            risk_level=risk.risk_level,
            status=IncidentStatus.OPEN,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )

        # 3. Smart Alerting: Deduplication, Cooldown, and Escalation
        cached = self._active_alerts_cache.get(dedup_key)
        cooldown_sec = self._get_cooldown_for_event(event.event_type)

        if cached is not None:
            last_alert_time: datetime = cached["last_alert_time"]
            prev_severity: RiskLevel = cached["severity"]
            elapsed = (now - last_alert_time).total_seconds()

            # Check Escalation: if duration exceeds persistence threshold and severity upgrades
            is_escalation = False
            if self.escalation_enabled and event.duration_seconds >= self.escalation_persistence_sec:
                order = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}
                if order.get(risk.risk_level, 0) > order.get(prev_severity, 0):
                    is_escalation = True

            if is_escalation:
                # Escalation trigger!
                alert_id = cached["alert_id"]
                cached["severity"] = risk.risk_level
                cached["last_alert_time"] = now

                title, msg = self.compose_alert_message(event, risk)
                msg = f"[ESCALATED to {risk.risk_level.value}] {msg} (Persisted for {event.duration_seconds:.1f}s)"

                if db is not None:
                    db_alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
                    if db_alert:
                        db_alert.severity = risk.risk_level.value
                        db_alert.message = msg

                    hist = AlertHistory(
                        alert_id=alert_id,
                        incident_id=incident_id,
                        action="ESCALATED",
                        previous_level=prev_severity.value,
                        new_level=risk.risk_level.value,
                        reason=f"Event persisted for {event.duration_seconds:.1f}s exceeding threshold",
                        timestamp=now,
                    )
                    db.add(hist)
                    db.commit()

                priority, is_audible = self._get_priority_for_event(event, risk)
                escalated_alert = AlertSchema(
                    alert_id=alert_id,
                    incident_id=incident_id,
                    severity=risk.risk_level,
                    priority=priority,
                    is_audible=is_audible,
                    title=title,
                    message=msg,
                    camera_id=event.camera_id,
                    zone_id=event.zone_id,
                    event_type=event.event_type,
                    timestamp=now.isoformat(),
                    status=AlertStatus.ACTIVE,
                )
                broadcaster.broadcast("AlertEscalated", escalated_alert.model_dump())

                # Dispatch to external notification channels
                try:
                    ev_ref = None
                    if db is not None:
                        try:
                            ev_item = db.query(EvidenceItem).filter(EvidenceItem.incident_id == incident_id).first()
                            if ev_item:
                                ev_ref = f"/api/evidence/{ev_item.evidence_id}/download"
                        except Exception:
                            pass

                    ext_payload = AlertNotificationPayload(
                        incident_id=incident_id,
                        alert_id=alert_id,
                        camera_id=event.camera_id,
                        zone_id=event.zone_id,
                        event_type=event.event_type.value,
                        severity=risk.risk_level.value,
                        title=title,
                        message=msg,
                        timestamp=now.isoformat(),
                        affected_workers_count=len(affected_list),
                        evidence_reference=ev_ref,
                    )
                    ProviderRegistry.get_instance().dispatch_alert(ext_payload)
                except Exception as ext_err:
                    log.error("Failed to dispatch external alert notification: %s", ext_err)

                try:
                    MetricsCollector.get_instance().increment_counter(
                        "rakshya_alert_actions_total",
                        labels={"action": "ESCALATED"},
                    )
                except Exception:
                    pass

                return escalated_alert, incident_schema, "ESCALATED"

            # Check Cooldown
            if elapsed < cooldown_sec:
                # Within cooldown: suppress duplicate alert creation
                if db is not None:
                    hist = AlertHistory(
                        alert_id=cached["alert_id"],
                        incident_id=incident_id,
                        action="COOLDOWN_SUPPRESSED",
                        previous_level=prev_severity.value,
                        new_level=prev_severity.value,
                        reason=f"Suppressed duplicate alert within cooldown window ({elapsed:.1f}s < {cooldown_sec}s)",
                        timestamp=now,
                    )
                    db.add(hist)
                    db.commit()
                return None, incident_schema, "COOLDOWN_SUPPRESSED"

        # 4. Generate New Alert
        alert_id = str(uuid.uuid4())
        title, msg = self.compose_alert_message(event, risk)

        self._active_alerts_cache[dedup_key] = {
            "incident_id": incident_id,
            "alert_id": alert_id,
            "last_alert_time": now,
            "severity": risk.risk_level,
        }

        if db is not None:
            db_alert = Alert(
                alert_id=alert_id,
                incident_id=incident_id,
                severity=risk.risk_level.value,
                title=title,
                message=msg,
                camera_id=event.camera_id,
                zone_id=event.zone_id,
                event_type=event.event_type.value,
                status=AlertStatus.ACTIVE.value,
                created_at=now,
            )
            db.add(db_alert)

            hist = AlertHistory(
                alert_id=alert_id,
                incident_id=incident_id,
                action="CREATED",
                previous_level=None,
                new_level=risk.risk_level.value,
                reason="Initial alert generated from confirmed event",
                timestamp=now,
            )
            db.add(hist)
            db.commit()

        priority, is_audible = self._get_priority_for_event(event, risk)
        new_alert = AlertSchema(
            alert_id=alert_id,
            incident_id=incident_id,
            severity=risk.risk_level,
            priority=priority,
            is_audible=is_audible,
            title=title,
            message=msg,
            camera_id=event.camera_id,
            zone_id=event.zone_id,
            event_type=event.event_type,
            timestamp=now.isoformat(),
            status=AlertStatus.ACTIVE,
        )
        broadcaster.broadcast("AlertCreated", new_alert.model_dump())

        # Dispatch to external notification channels
        try:
            ev_ref = None
            if db is not None:
                try:
                    ev_item = db.query(EvidenceItem).filter(EvidenceItem.incident_id == incident_id).first()
                    if ev_item:
                        ev_ref = f"/api/evidence/{ev_item.evidence_id}/download"
                except Exception:
                    pass

            ext_payload = AlertNotificationPayload(
                incident_id=incident_id,
                alert_id=alert_id,
                camera_id=event.camera_id,
                zone_id=event.zone_id,
                event_type=event.event_type.value,
                severity=risk.risk_level.value,
                title=title,
                message=msg,
                timestamp=now.isoformat(),
                affected_workers_count=len(affected_list),
                evidence_reference=ev_ref,
            )
            ProviderRegistry.get_instance().dispatch_alert(ext_payload)
        except Exception as ext_err:
            log.error("Failed to dispatch external alert notification: %s", ext_err)

        try:
            MetricsCollector.get_instance().increment_counter(
                "rakshya_alerts_total",
                labels={"severity": risk.risk_level.value, "event_type": event.event_type.value},
            )
            MetricsCollector.get_instance().increment_counter(
                "rakshya_alert_actions_total",
                labels={"action": "CREATED"},
            )
        except Exception:
            pass

        return new_alert, incident_schema, "CREATED"

    def acknowledge_alert(self, alert_id: str, db: Session) -> AlertSchema:
        now = datetime.now(timezone.utc)
        db_alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if not db_alert:
            raise ValueError(f"Alert '{alert_id}' not found")

        db_alert.status = AlertStatus.ACKNOWLEDGED.value
        db_alert.acknowledged_at = now

        db_incident = db.query(Incident).filter(Incident.incident_id == db_alert.incident_id).first()
        if db_incident:
            db_incident.status = IncidentStatus.ACKNOWLEDGED.value
            db_incident.updated_at = now

        hist = AlertHistory(
            alert_id=alert_id,
            incident_id=db_alert.incident_id,
            action="ACKNOWLEDGED",
            previous_level=db_alert.severity,
            new_level=db_alert.severity,
            reason="Alert acknowledged by operator",
            timestamp=now,
        )
        db.add(hist)
        db.commit()

        result = AlertSchema(
            alert_id=db_alert.alert_id,
            incident_id=db_alert.incident_id,
            severity=RiskLevel(db_alert.severity),
            title=db_alert.title,
            message=db_alert.message,
            camera_id=db_alert.camera_id,
            zone_id=db_alert.zone_id,
            event_type=EventType(db_alert.event_type),
            timestamp=db_alert.created_at.isoformat(),
            status=AlertStatus.ACKNOWLEDGED,
            acknowledged_at=now.isoformat(),
        )
        broadcaster.broadcast("AlertUpdated", result.model_dump())
        try:
            MetricsCollector.get_instance().increment_counter(
                "rakshya_alert_actions_total",
                labels={"action": "ACKNOWLEDGED"}
            )
        except Exception:
            pass
        return result

    def resolve_alert(self, alert_id: str, db: Session) -> AlertSchema:
        now = datetime.now(timezone.utc)
        db_alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if not db_alert:
            raise ValueError(f"Alert '{alert_id}' not found")

        db_alert.status = AlertStatus.RESOLVED.value
        db_alert.resolved_at = now

        db_incident = db.query(Incident).filter(Incident.incident_id == db_alert.incident_id).first()
        if db_incident:
            db_incident.status = IncidentStatus.RESOLVED.value
            db_incident.resolved_at = now
            db_incident.updated_at = now

        # Clear from dedup cache
        for k, v in list(self._active_alerts_cache.items()):
            if v.get("alert_id") == alert_id or v.get("incident_id") == db_alert.incident_id:
                del self._active_alerts_cache[k]

        hist = AlertHistory(
            alert_id=alert_id,
            incident_id=db_alert.incident_id,
            action="RESOLVED",
            previous_level=db_alert.severity,
            new_level=db_alert.severity,
            reason="Alert and incident resolved",
            timestamp=now,
        )
        db.add(hist)
        db.commit()

        result = AlertSchema(
            alert_id=db_alert.alert_id,
            incident_id=db_alert.incident_id,
            severity=RiskLevel(db_alert.severity),
            title=db_alert.title,
            message=db_alert.message,
            camera_id=db_alert.camera_id,
            zone_id=db_alert.zone_id,
            event_type=EventType(db_alert.event_type),
            timestamp=db_alert.created_at.isoformat(),
            status=AlertStatus.RESOLVED,
            resolved_at=now.isoformat(),
        )
        broadcaster.broadcast("AlertUpdated", result.model_dump())
        broadcaster.broadcast("IncidentResolved", {"incident_id": db_alert.incident_id})
        try:
            MetricsCollector.get_instance().increment_counter(
                "rakshya_alert_actions_total",
                labels={"action": "RESOLVED"},
            )
        except Exception:
            pass
        return result

    def dismiss_alert(self, alert_id: str, db: Session) -> AlertSchema:
        now = datetime.now(timezone.utc)
        db_alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if not db_alert:
            raise ValueError(f"Alert '{alert_id}' not found")

        db_alert.status = AlertStatus.DISMISSED.value
        db_alert.resolved_at = now

        db_incident = db.query(Incident).filter(Incident.incident_id == db_alert.incident_id).first()
        if db_incident:
            db_incident.status = IncidentStatus.DISMISSED.value
            db_incident.resolved_at = now
            db_incident.updated_at = now

        for k, v in list(self._active_alerts_cache.items()):
            if v.get("alert_id") == alert_id:
                del self._active_alerts_cache[k]

        hist = AlertHistory(
            alert_id=alert_id,
            incident_id=db_alert.incident_id,
            action="DISMISSED",
            previous_level=db_alert.severity,
            new_level=db_alert.severity,
            reason="Alert dismissed by operator",
            timestamp=now,
        )
        db.add(hist)
        db.commit()

        result = AlertSchema(
            alert_id=db_alert.alert_id,
            incident_id=db_alert.incident_id,
            severity=RiskLevel(db_alert.severity),
            title=db_alert.title,
            message=db_alert.message,
            camera_id=db_alert.camera_id,
            zone_id=db_alert.zone_id,
            event_type=EventType(db_alert.event_type),
            timestamp=db_alert.created_at.isoformat(),
            status=AlertStatus.DISMISSED,
            resolved_at=now.isoformat(),
        )
        broadcaster.broadcast("AlertUpdated", result.model_dump())
        try:
            MetricsCollector.get_instance().increment_counter(
                "rakshya_alert_actions_total",
                labels={"action": "DISMISSED"},
            )
        except Exception:
            pass
        return result

    def get_risk_summary(self, db: Session) -> RiskSummaryResponse:
        active_alerts_count = db.query(Alert).filter(Alert.status == AlertStatus.ACTIVE.value).count()
        critical_count = db.query(Alert).filter(
            Alert.status == AlertStatus.ACTIVE.value,
            Alert.severity == RiskLevel.CRITICAL.value
        ).count()
        high_count = db.query(Alert).filter(
            Alert.status == AlertStatus.ACTIVE.value,
            Alert.severity == RiskLevel.HIGH.value
        ).count()
        med_count = db.query(Alert).filter(
            Alert.status == AlertStatus.ACTIVE.value,
            Alert.severity == RiskLevel.MEDIUM.value
        ).count()
        low_count = db.query(Alert).filter(
            Alert.status == AlertStatus.ACTIVE.value,
            Alert.severity == RiskLevel.LOW.value
        ).count()
        open_incidents_count = db.query(Incident).filter(
            Incident.status.in_([IncidentStatus.OPEN.value, IncidentStatus.ACKNOWLEDGED.value])
        ).count()

        return RiskSummaryResponse(
            active_alerts=active_alerts_count,
            critical=critical_count,
            high=high_count,
            medium=med_count,
            low=low_count,
            open_incidents=open_incidents_count,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
