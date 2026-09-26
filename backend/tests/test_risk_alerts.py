"""
test_risk_alerts.py — SafeSync Phase 7 Tests
Comprehensive automated test suite for Safety Risk Analysis and Smart Alerts.
Covers:
  - Event normalizer (confirmed vs UNKNOWN PPE states)
  - MANDATORY TEST: UNKNOWN state MUST NOT become a violation
  - Explainable deterministic risk scoring
  - Incident generation and alert prioritization
  - Deduplication and cooldown suppression
  - Severity escalation on prolonged persistence
  - Multi-hazard simultaneous incident handling
  - Alert acknowledgement, resolution, and dismissal
  - Database persistence and live /api/risk/summary querying
"""

import json
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import engine, Base, SessionLocal
from app.ai.risk.schemas import (
    EventType,
    RiskLevel,
    IncidentStatus,
    AlertStatus,
    NormalizedSafetyEvent,
)
from app.services.risk_engine import RiskEngine
from app.services.alert_engine import AlertEngine
from app.services.event_normalizer import EventNormalizer
from app.models.risk_alert import Incident, Alert, AlertHistory
from app.ai.compliance.schemas import (
    ComplianceAnalysisResponse,
    WorkerTrack,
    WorkerBoundingBox,
    PPEObservation,
    PPEState,
    PPEItemType,
    OverallComplianceState,
)
from app.ai.hazards.schemas import (
    HazardAnalysisResponse,
    HazardEventDetail,
    HazardBoundingBox,
    HazardState,
    HazardType,
    HazardRelationship,
)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def risk_engine():
    return RiskEngine()


@pytest.fixture
def alert_engine(risk_engine):
    return AlertEngine(risk_engine=risk_engine)


def make_test_event(
    event_type: EventType = EventType.MISSING_HELMET,
    track_id: int = 12,
    duration: float = 0.0,
    camera_id: str = "camera_01",
    zone_id: str = "production_floor",
) -> NormalizedSafetyEvent:
    return NormalizedSafetyEvent(
        event_id="test-uuid-1234",
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        camera_id=camera_id,
        zone_id=zone_id,
        track_id=track_id,
        confidence=0.88,
        duration_seconds=duration,
        source="compliance",
    )


# ─── 1-4. Confirmed Missing PPE Tests ────────────────────────────────────────

def test_confirmed_missing_helmet_generates_event(alert_engine, db):
    ev = make_test_event(EventType.MISSING_HELMET, track_id=12)
    alert, incident, action = alert_engine.process_event(ev, db=db)
    assert action == "CREATED"
    assert alert is not None
    assert alert.event_type == EventType.MISSING_HELMET
    assert alert.severity in [RiskLevel.MEDIUM, RiskLevel.HIGH]
    assert "Worker #12" in alert.message
    assert incident.status == IncidentStatus.OPEN


def test_confirmed_missing_vest_generates_event(alert_engine, db):
    ev = make_test_event(EventType.MISSING_SAFETY_VEST, track_id=15)
    alert, incident, action = alert_engine.process_event(ev, db=db)
    assert action == "CREATED"
    assert alert.event_type == EventType.MISSING_SAFETY_VEST
    assert "Worker #15" in alert.message


def test_confirmed_missing_gloves_generates_event(alert_engine, db):
    ev = make_test_event(EventType.MISSING_GLOVES, track_id=20)
    alert, incident, action = alert_engine.process_event(ev, db=db)
    assert action == "CREATED"
    assert alert.event_type == EventType.MISSING_GLOVES


def test_confirmed_missing_footwear_generates_event(alert_engine, db):
    ev = make_test_event(EventType.MISSING_SAFETY_FOOTWEAR, track_id=22)
    alert, incident, action = alert_engine.process_event(ev, db=db)
    assert action == "CREATED"
    assert alert.event_type == EventType.MISSING_SAFETY_FOOTWEAR


# ─── 5. MANDATORY TEST: UNKNOWN State MUST NOT Become Violation ──────────────

def test_unknown_ppe_state_never_generates_violation():
    """
    CRITICAL QUALITY GATE:
    When a worker has helmet = UNKNOWN (e.g. occluded head or border clipping),
    it MUST NOT be converted into a MISSING_HELMET event.
    Only confirmed ABSENT state can generate violation events.
    """
    worker_unknown = WorkerTrack(
        track_id=101,
        bbox=WorkerBoundingBox(x1=50, y1=50, x2=150, y2=250),
        confidence=0.85,
        ppe={"helmet": PPEState.UNKNOWN, "safety_vest": PPEState.PRESENT},
        ppe_details={
            "helmet": PPEObservation(item_type=PPEItemType.HELMET, state=PPEState.UNKNOWN, is_occluded=True),
            "safety_vest": PPEObservation(item_type=PPEItemType.SAFETY_VEST, state=PPEState.PRESENT),
        },
        overall_status=OverallComplianceState.UNKNOWN,
    )
    compliance_resp = ComplianceAnalysisResponse(
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        workers=[worker_unknown],
    )

    events = EventNormalizer.from_compliance_response(compliance_resp)
    # MUST BE ZERO: UNKNOWN and PRESENT do not create violations!
    assert len(events) == 0, f"Expected 0 violations for UNKNOWN PPE, got {len(events)}"


def test_confirmed_absent_ppe_state_generates_violation():
    """
    Counterpart test: Confirmed ABSENT state MUST generate violation.
    """
    worker_absent = WorkerTrack(
        track_id=102,
        bbox=WorkerBoundingBox(x1=50, y1=50, x2=150, y2=250),
        confidence=0.85,
        ppe={"helmet": PPEState.ABSENT, "safety_vest": PPEState.PRESENT},
        ppe_details={
            "helmet": PPEObservation(item_type=PPEItemType.HELMET, state=PPEState.ABSENT, consecutive_missed=6),
            "safety_vest": PPEObservation(item_type=PPEItemType.SAFETY_VEST, state=PPEState.PRESENT),
        },
        overall_status=OverallComplianceState.NON_COMPLIANT,
    )
    compliance_resp = ComplianceAnalysisResponse(
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        workers=[worker_absent],
    )

    events = EventNormalizer.from_compliance_response(compliance_resp)
    assert len(events) == 1
    assert events[0].event_type == EventType.MISSING_HELMET
    assert events[0].track_id == 102


# ─── 6-7. Confirmed Environmental Hazards Tests ───────────────────────────────

def test_confirmed_fire_generates_high_or_critical_alert(alert_engine, db):
    ev = NormalizedSafetyEvent(
        event_id="fire-ev-1",
        event_type=EventType.FIRE_DETECTED,
        timestamp=datetime.now(timezone.utc).isoformat(),
        camera_id="camera_01",
        zone_id="production_floor",
        confidence=0.88,
        hazard_event_id="HAZARD-0001",
        source="hazard",
    )
    alert, incident, action = alert_engine.process_event(ev, db=db)
    assert action == "CREATED"
    assert alert.severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    assert "active flame combustion" in alert.message


def test_confirmed_smoke_generates_alert(alert_engine, db):
    ev = NormalizedSafetyEvent(
        event_id="smoke-ev-1",
        event_type=EventType.SMOKE_DETECTED,
        timestamp=datetime.now(timezone.utc).isoformat(),
        camera_id="camera_02",
        zone_id="storage_area",
        confidence=0.72,
        hazard_event_id="HAZARD-0002",
        source="hazard",
    )
    alert, incident, action = alert_engine.process_event(ev, db=db)
    assert action == "CREATED"
    assert alert.event_type == EventType.SMOKE_DETECTED
    assert alert.severity in [RiskLevel.MEDIUM, RiskLevel.HIGH]


# ─── 8-10. Deduplication and Cooldown Suppression Tests ───────────────────────

def test_alert_cooldown_suppresses_rapid_duplicate_alerts(alert_engine, db):
    ev = make_test_event(EventType.MISSING_HELMET, track_id=44)

    # First occurrence -> CREATED
    alert1, inc1, action1 = alert_engine.process_event(ev, db=db)
    assert action1 == "CREATED"
    assert alert1 is not None

    # Immediate next frame occurrence for same worker -> COOLDOWN_SUPPRESSED
    alert2, inc2, action2 = alert_engine.process_event(ev, db=db)
    assert action2 == "COOLDOWN_SUPPRESSED"
    assert alert2 is None
    assert inc2.incident_id == inc1.incident_id


def test_alert_deduplication_updates_same_incident(alert_engine, db):
    ev = make_test_event(EventType.MISSING_SAFETY_VEST, track_id=55)
    alert1, inc1, _ = alert_engine.process_event(ev, db=db)

    # Multiple subsequent occurrences
    for _ in range(5):
        _, inc_sub, act = alert_engine.process_event(ev, db=db)
        assert act == "COOLDOWN_SUPPRESSED"
        assert inc_sub.incident_id == inc1.incident_id


# ─── 11. Severity Escalation Test ─────────────────────────────────────────────

def test_severity_escalates_on_prolonged_persistence(alert_engine, db):
    ev_initial = make_test_event(EventType.MISSING_GLOVES, track_id=77, duration=0.0)
    alert_initial, _, act_init = alert_engine.process_event(ev_initial, db=db)
    assert act_init == "CREATED"
    init_sev = alert_initial.severity

    # Simulate event persisting for 40 seconds (exceeds escalation threshold of 30s)
    ev_persisted = make_test_event(EventType.MISSING_GLOVES, track_id=77, duration=40.0)
    alert_esc, _, act_esc = alert_engine.process_event(ev_persisted, db=db)
    assert act_esc == "ESCALATED"
    assert alert_esc is not None
    # Severity should have upgraded
    order = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}
    assert order[alert_esc.severity] > order[init_sev]


# ─── 12. Multiple Hazards Test ────────────────────────────────────────────────

def test_multiple_hazards_generates_high_risk(alert_engine, db):
    ev_multi = NormalizedSafetyEvent(
        event_id="multi-ev-1",
        event_type=EventType.MULTIPLE_HAZARDS,
        timestamp=datetime.now(timezone.utc).isoformat(),
        camera_id="camera_01",
        zone_id="electrical_room",
        confidence=0.85,
        source="hazard",
    )
    alert, incident, action = alert_engine.process_event(ev_multi, db=db)
    assert action == "CREATED"
    assert alert.severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]


# ─── 13. Multiple Workers Factor Scaling ──────────────────────────────────────

def test_risk_score_scales_with_affected_workers(risk_engine):
    score_1_worker = risk_engine.evaluate(EventType.MISSING_HELMET, affected_workers_count=1)
    score_3_workers = risk_engine.evaluate(EventType.MISSING_HELMET, affected_workers_count=3)
    assert score_3_workers.risk_score > score_1_worker.risk_score
    assert score_3_workers.factors["affected_workers_factor"] > score_1_worker.factors["affected_workers_factor"]


# ─── 14-16. Alert Lifecycle: Acknowledge, Resolve, Dismiss ────────────────────

def test_alert_lifecycle_acknowledge_resolve(alert_engine, db):
    ev = make_test_event(EventType.MISSING_HELMET, track_id=88)
    alert, incident, _ = alert_engine.process_event(ev, db=db)

    # Acknowledge
    ack_alert = alert_engine.acknowledge_alert(alert.alert_id, db)
    assert ack_alert.status == AlertStatus.ACKNOWLEDGED
    db_inc = db.query(Incident).filter(Incident.incident_id == incident.incident_id).first()
    assert db_inc.status == IncidentStatus.ACKNOWLEDGED.value

    # Resolve
    res_alert = alert_engine.resolve_alert(alert.alert_id, db)
    assert res_alert.status == AlertStatus.RESOLVED
    db_inc_resolved = db.query(Incident).filter(Incident.incident_id == incident.incident_id).first()
    assert db_inc_resolved.status == IncidentStatus.RESOLVED.value


def test_alert_lifecycle_dismiss(alert_engine, db):
    ev = make_test_event(EventType.MISSING_SAFETY_VEST, track_id=99)
    alert, incident, _ = alert_engine.process_event(ev, db=db)

    dism_alert = alert_engine.dismiss_alert(alert.alert_id, db)
    assert dism_alert.status == AlertStatus.DISMISSED


# ─── 17-18. System/Camera Failure & Nonexistent Alert 404 ─────────────────────

def test_camera_failure_event_processing(alert_engine, db):
    ev_cam = NormalizedSafetyEvent(
        event_id="cam-fail-1",
        event_type=EventType.CAMERA_FAILURE,
        timestamp=datetime.now(timezone.utc).isoformat(),
        camera_id="camera_04",
        source="system",
    )
    alert, incident, act = alert_engine.process_event(ev_cam, db=db)
    assert act == "CREATED"
    assert "Camera connectivity or feed failure" in alert.message


def test_api_nonexistent_alert_returns_404(client):
    res = client.get("/api/alerts/NON_EXISTENT_ALERT_UUID_9999")
    assert res.status_code == 404


# ─── 19-20. Database Persistence & Live /api/risk/summary ─────────────────────

def test_api_risk_summary_returns_actual_database_counts(client, alert_engine, db):
    # Process an event to ensure at least 1 active alert exists
    ev = make_test_event(EventType.MISSING_HELMET, track_id=120)
    alert_engine.process_event(ev, db=db)

    res = client.get("/api/risk/summary")
    assert res.status_code == 200
    data = res.json()
    assert "active_alerts" in data
    assert "open_incidents" in data
    assert data["active_alerts"] >= 1
    assert data["open_incidents"] >= 1


def test_api_list_alerts_and_incidents(client, alert_engine, db):
    res_alerts = client.get("/api/alerts?limit=10")
    assert res_alerts.status_code == 200
    assert isinstance(res_alerts.json(), list)

    res_inc = client.get("/api/incidents?limit=10")
    assert res_inc.status_code == 200
    assert isinstance(res_inc.json(), list)
