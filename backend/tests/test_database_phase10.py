"""
test_database_phase10.py — RAKSHYA VISION Phase 10 Step 4
Automated Test Suite for SQLite WAL Mode, Pragmas, Health Checks,
and Retention Cleanup Logic.

Uses isolated, temporary SQLite test databases and ensures no corruption or leakage
to production `rakshya_vision.db`.
"""

import os
import tempfile
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database.session import Base, get_sqlite_pragmas, check_database_health
from app.models.risk_alert import Incident, Alert, AlertHistory
from app.models.hazard import HazardEvent, HazardObservation
from app.models.compliance import WorkerTracking, ComplianceObservation
from scripts.cleanup_retention import get_retention_policy, analyze_candidates, run_cleanup


@pytest.fixture
def temp_db():
    """Creates a temporary sqlite file database for testing WAL and pragmas."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_wal.db")
    db_url = f"sqlite:///{db_path}"

    test_engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False, "timeout": 15},
    )

    # Attach the same PRAGMA connect listener as session.py
    from sqlalchemy import event

    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.close()

    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    yield {
        "engine": test_engine,
        "session": session,
        "path": db_path,
        "url": db_url
    }

    session.close()
    test_engine.dispose()
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass


def test_sqlite_wal_pragmas_enabled(temp_db):
    """Verifies that journal_mode is WAL, foreign_keys=ON, busy_timeout=5000, and synchronous=NORMAL."""
    pragmas = get_sqlite_pragmas(temp_db["engine"])
    assert pragmas["journal_mode"].lower() == "wal"
    assert pragmas["foreign_keys"] == 1
    assert pragmas["busy_timeout"] == 5000
    assert pragmas["synchronous"] in ("NORMAL", 1)


def test_database_health_check_healthy(temp_db):
    """Verifies that check_database_health returns status healthy on valid database."""
    health = check_database_health(temp_db["engine"])
    assert health["status"] == "healthy"
    assert health["dialect"] == "sqlite"
    assert health["can_query"] is True
    assert "incidents" in health["tables_available"]
    assert "alerts" in health["tables_available"]
    assert health["pragmas"]["journal_mode"].lower() == "wal"


def test_foreign_keys_enforcement(temp_db):
    """Verifies that foreign key constraints are strictly enforced in SQLite."""
    session = temp_db["session"]
    with pytest.raises(Exception):
        # Insert alert with non-existent incident_id
        orphan_alert = Alert(
            alert_id="ALERT-TEST-ORPHAN",
            incident_id="NON-EXISTENT-INCIDENT-ID",
            severity="HIGH",
            title="Orphan Alert",
            message="Testing FK enforcement",
            camera_id="cam1",
            zone_id="zone1",
            event_type="NO_HARDHAT",
            status="ACTIVE"
        )
        session.add(orphan_alert)
        session.commit()
    session.rollback()


def test_retention_policy_defaults():
    """Verifies default retention thresholds from production config or overrides."""
    policy = get_retention_policy()
    assert policy["incidents_days"] > 0
    assert policy["alerts_days"] > 0
    assert policy["hazard_events_days"] > 0
    assert policy["worker_days"] > 0
    assert policy["alert_history_days"] > 0

    override_policy = get_retention_policy(override_days=7)
    assert override_policy["incidents_days"] == 7
    assert override_policy["alerts_days"] == 7


def test_active_incidents_never_cleaned_up(temp_db):
    """Verifies that OPEN and ACKNOWLEDGED incidents are never deleted, even if very old."""
    session = temp_db["session"]
    old_time = datetime.now(timezone.utc) - timedelta(days=120)

    # Insert old OPEN incident
    inc_open = Incident(
        incident_id="INC-OLD-OPEN",
        status="OPEN",
        event_types="NO_HARDHAT",
        camera_id="cam1",
        risk_score=90,
        risk_level="HIGH",
        created_at=old_time,
        updated_at=old_time
    )
    # Insert old ACKNOWLEDGED incident
    inc_ack = Incident(
        incident_id="INC-OLD-ACK",
        status="ACKNOWLEDGED",
        event_types="SMOKE_DETECTED",
        camera_id="cam1",
        risk_score=75,
        risk_level="MEDIUM",
        created_at=old_time,
        updated_at=old_time
    )
    # Insert old RESOLVED incident (eligible)
    inc_res = Incident(
        incident_id="INC-OLD-RESOLVED",
        status="RESOLVED",
        event_types="NO_VEST",
        camera_id="cam1",
        risk_score=50,
        risk_level="LOW",
        created_at=old_time,
        updated_at=old_time,
        resolved_at=old_time
    )
    session.add_all([inc_open, inc_ack, inc_res])
    session.commit()

    policy = get_retention_policy(override_days=30)
    candidates = analyze_candidates(session, policy)

    # Only the resolved incident should be eligible
    eligible_ids = [inc.incident_id for inc in candidates["eligible_incidents"]]
    assert "INC-OLD-RESOLVED" in eligible_ids
    assert "INC-OLD-OPEN" not in eligible_ids
    assert "INC-OLD-ACK" not in eligible_ids
    assert candidates["active_incidents_count"] >= 2


def test_unresolved_hazards_never_cleaned_up(temp_db):
    """Verifies that SUSPECTED and CONFIRMED hazard events are never deleted, even if older than cutoff."""
    session = temp_db["session"]
    old_time = datetime.now(timezone.utc) - timedelta(days=90)

    h_suspected = HazardEvent(
        event_id="HAZARD-OLD-SUSP",
        hazard_type="fire",
        state="SUSPECTED",
        first_seen=old_time,
        last_seen=old_time
    )
    h_confirmed = HazardEvent(
        event_id="HAZARD-OLD-CONF",
        hazard_type="smoke",
        state="CONFIRMED",
        first_seen=old_time,
        last_seen=old_time
    )
    h_cleared = HazardEvent(
        event_id="HAZARD-OLD-CLEAR",
        hazard_type="smoke",
        state="CLEARED",
        first_seen=old_time,
        last_seen=old_time
    )
    session.add_all([h_suspected, h_confirmed, h_cleared])
    session.commit()

    policy = get_retention_policy(override_days=30)
    candidates = analyze_candidates(session, policy)

    eligible_pks = candidates["eligible_hazard_pks"]
    assert h_cleared.id in eligible_pks
    assert h_suspected.id not in eligible_pks
    assert h_confirmed.id not in eligible_pks
    assert candidates["active_hazards_count"] >= 2


def test_dry_run_does_not_delete_records(temp_db):
    """Verifies that running cleanup in dry-run mode leaves all records intact."""
    session = temp_db["session"]
    old_time = datetime.now(timezone.utc) - timedelta(days=60)

    inc = Incident(
        incident_id="INC-DRY-RUN",
        status="RESOLVED",
        event_types="NO_HARDHAT",
        camera_id="cam1",
        created_at=old_time,
        updated_at=old_time
    )
    session.add(inc)
    session.commit()

    res = run_cleanup(execute=False, override_days=30, session_override=session)
    assert res["status"] == "dry_run_complete"

    # Verify record still exists
    persisted = session.query(Incident).filter_by(incident_id="INC-DRY-RUN").first()
    assert persisted is not None


def test_execute_deletes_eligible_records_safely(temp_db):
    """Verifies that execute mode removes eligible records and their child relations."""
    session = temp_db["session"]
    old_time = datetime.now(timezone.utc) - timedelta(days=60)

    inc = Incident(
        incident_id="INC-EXEC-DEL",
        status="RESOLVED",
        event_types="NO_HARDHAT",
        camera_id="cam1",
        created_at=old_time,
        updated_at=old_time
    )
    session.add(inc)
    session.commit()

    alt = Alert(
        alert_id="ALT-EXEC-DEL",
        incident_id="INC-EXEC-DEL",
        severity="HIGH",
        title="Test Alert",
        message="Message",
        camera_id="cam1",
        event_type="NO_HARDHAT",
        status="RESOLVED",
        created_at=old_time
    )
    hist = AlertHistory(
        alert_id="ALT-EXEC-DEL",
        incident_id="INC-EXEC-DEL",
        action="RESOLVED",
        reason="Test",
        timestamp=old_time
    )
    session.add_all([alt, hist])
    session.commit()

    res = run_cleanup(execute=True, override_days=30, session_override=session)
    assert res["status"] == "success"

    # Verify deleted
    assert session.query(Incident).filter_by(incident_id="INC-EXEC-DEL").first() is None
    assert session.query(Alert).filter_by(alert_id="ALT-EXEC-DEL").first() is None
    assert session.query(AlertHistory).filter_by(alert_id="ALT-EXEC-DEL").first() is None


def test_recent_records_preserved(temp_db):
    """Verifies that resolved incidents newer than the retention cutoff are strictly preserved."""
    session = temp_db["session"]
    recent_time = datetime.now(timezone.utc) - timedelta(days=5)

    inc = Incident(
        incident_id="INC-RECENT",
        status="RESOLVED",
        event_types="NO_HARDHAT",
        camera_id="cam1",
        created_at=recent_time,
        updated_at=recent_time
    )
    session.add(inc)
    session.commit()

    res = run_cleanup(execute=True, override_days=30, session_override=session)
    assert session.query(Incident).filter_by(incident_id="INC-RECENT").first() is not None


def test_database_functional_after_cleanup(temp_db):
    """Verifies that insertions and reads continue working seamlessly after a retention purge."""
    session = temp_db["session"]
    old_time = datetime.now(timezone.utc) - timedelta(days=60)

    inc_old = Incident(
        incident_id="INC-OLD-1",
        status="RESOLVED",
        event_types="NO_HARDHAT",
        created_at=old_time,
        updated_at=old_time
    )
    session.add(inc_old)
    session.commit()

    run_cleanup(execute=True, override_days=30, session_override=session)

    # Insert a new incident post-cleanup
    inc_new = Incident(
        incident_id="INC-POST-CLEANUP",
        status="OPEN",
        event_types="FIRE_DETECTED",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    session.add(inc_new)
    session.commit()

    found = session.query(Incident).filter_by(incident_id="INC-POST-CLEANUP").first()
    assert found is not None
    assert found.status == "OPEN"


def test_inactive_workers_cleaned_up_and_active_preserved(temp_db):
    """Verifies that inactive workers older than cutoff are cleaned up while active workers are preserved."""
    session = temp_db["session"]
    old_time = datetime.now(timezone.utc) - timedelta(days=60)

    w_active = WorkerTracking(
        track_id=101,
        session_id="sess_active",
        first_seen=old_time,
        last_seen=old_time,
        is_active=True
    )
    w_inactive = WorkerTracking(
        track_id=102,
        session_id="sess_inactive",
        first_seen=old_time,
        last_seen=old_time,
        is_active=False
    )
    session.add_all([w_active, w_inactive])
    session.commit()

    c_obs = ComplianceObservation(
        worker_tracking_id=w_inactive.id,
        track_id=102,
        overall_status="NON_COMPLIANT",
        helmet_status="ABSENT",
        vest_status="PRESENT",
        gloves_status="UNKNOWN",
        footwear_status="UNKNOWN"
    )
    session.add(c_obs)
    session.commit()

    policy = get_retention_policy(override_days=30)
    candidates = analyze_candidates(session, policy)

    assert w_inactive.id in candidates["eligible_worker_pks"]
    assert w_active.id not in candidates["eligible_worker_pks"]
    assert candidates["active_workers_count"] >= 1

    # Execute cleanup
    run_cleanup(execute=True, override_days=30, session_override=session)

    assert session.query(WorkerTracking).filter_by(track_id=101).first() is not None
    assert session.query(WorkerTracking).filter_by(track_id=102).first() is None
    assert session.query(ComplianceObservation).filter_by(track_id=102).first() is None


def test_transaction_rollback_on_error(temp_db):
    """Verifies that failures during cleanup cleanly rollback without partial deletions."""
    session = temp_db["session"]
    old_time = datetime.now(timezone.utc) - timedelta(days=60)

    inc = Incident(
        incident_id="INC-ROLLBACK-TEST",
        status="RESOLVED",
        event_types="NO_HARDHAT",
        created_at=old_time,
        updated_at=old_time
    )
    session.add(inc)
    session.commit()

    # Monkeypatch session.commit to simulate mid-transaction failure
    original_commit = session.commit

    def faulty_commit():
        raise RuntimeError("Simulated mid-transaction failure")

    session.commit = faulty_commit

    with pytest.raises(RuntimeError, match="Simulated mid-transaction failure"):
        run_cleanup(execute=True, override_days=30, session_override=session)

    session.commit = original_commit

    # Record must still be present because of rollback
    persisted = session.query(Incident).filter_by(incident_id="INC-ROLLBACK-TEST").first()
    assert persisted is not None


def test_custom_database_url_support(monkeypatch, tmp_path):
    """Verifies engine creation and initialization against custom DATABASE_URL."""
    custom_db = tmp_path / "custom_prod.db"
    custom_url = f"sqlite:///{custom_db}"
    monkeypatch.setenv("DATABASE_URL", custom_url)

    from app.config import Settings
    custom_settings = Settings()
    assert custom_settings.DATABASE_URL == custom_url

    test_eng = create_engine(custom_url)
    Base.metadata.create_all(bind=test_eng)
    health = check_database_health(test_eng)
    assert health["status"] in ("healthy", "degraded")
    assert health["dialect"] == "sqlite"
    test_eng.dispose()

