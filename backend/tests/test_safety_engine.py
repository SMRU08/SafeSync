"""
test_safety_engine.py — SafeSync Safety Intelligence Pipeline
Unit & Integration Tests for Centralized Safety Engine enforcing Rules 1 through 7:
- Rule 1: Confirmed Fire -> P0 CRITICAL, Audible Siren
- Rule 2: Confirmed Smoke -> P0/P1 Hazard, Audible Siren
- Rule 3: Multi-hazard escalation -> P0 CRITICAL
- Rule 4: Confirmed PPE violation -> P2 Visual Dashboard Alert, NO Siren
- Rule 5: UNKNOWN PPE state -> Strictly NO violation
- Rule 6: Camera offline -> P3 System Warning
- Rule 7: AI engine unavailable -> P3 System Warning
"""

import pytest
from datetime import datetime, timezone
from app.services.safety_engine import SafetyEngine, SafetyAssessment
from app.ai.risk.schemas import EventType, RiskLevel, AlarmPriority
from app.ai.compliance.schemas import (
    ComplianceAnalysisResponse,
    WorkerTrack,
    PPEState,
    PPEItemType,
    PPEObservation,
    WorkerBoundingBox,
    ComplianceSummary,
)
from app.ai.hazards.schemas import (
    HazardAnalysisResponse,
    HazardEventDetail,
    HazardState,
    HazardType,
    HazardRelationship,
    HazardBoundingBox,
)


@pytest.fixture
def safety_engine():
    return SafetyEngine()


def test_rule_1_confirmed_fire(safety_engine):
    """Rule 1: Confirmed fire must generate P0 CRITICAL event with audible siren."""
    hazard = HazardEventDetail(
        event_id="haz_fire_01",
        hazard_type=HazardType.FIRE,
        state=HazardState.CONFIRMED,
        camera_id="camera_01",
        zone_id="storage_area",
        confidence=0.88,
        bbox=HazardBoundingBox.from_xyxy(10, 10, 100, 100),
        first_seen=datetime.now(timezone.utc).isoformat(),
        last_seen=datetime.now(timezone.utc).isoformat(),
        duration_seconds=5.0,
        detection_count=10,
        average_confidence=0.85,
        max_confidence=0.92,
        persistence_ratio=0.9,
        frames_detected=10,
        frames_missed=0,
    )
    ev = safety_engine.enforce_rule_1_fire(hazard)
    assert ev is not None
    assert ev.event_type == EventType.FIRE_DETECTED
    assert ev.details["priority"] == AlarmPriority.P0.value
    assert ev.details["audible"] is True
    assert ev.details["rule"] == "RULE_1_FIRE"


def test_rule_2_confirmed_smoke(safety_engine):
    """Rule 2: Confirmed smoke must generate P1/P0 event with audible siren."""
    # Under 10s -> P1
    hazard_short = HazardEventDetail(
        event_id="haz_smoke_01",
        hazard_type=HazardType.SMOKE,
        state=HazardState.CONFIRMED,
        camera_id="camera_01",
        zone_id="production_floor",
        confidence=0.75,
        bbox=HazardBoundingBox.from_xyxy(50, 50, 200, 200),
        first_seen=datetime.now(timezone.utc).isoformat(),
        last_seen=datetime.now(timezone.utc).isoformat(),
        duration_seconds=4.0,
        detection_count=8,
        average_confidence=0.72,
        max_confidence=0.80,
        persistence_ratio=0.85,
        frames_detected=8,
        frames_missed=0,
    )
    ev_short = safety_engine.enforce_rule_2_smoke(hazard_short)
    assert ev_short is not None
    assert ev_short.event_type == EventType.SMOKE_DETECTED
    assert ev_short.details["priority"] == AlarmPriority.P1.value
    assert ev_short.details["audible"] is True

    # Over 10s persistent smoke -> P0 escalation
    hazard_long = HazardEventDetail(
        event_id="haz_smoke_02",
        hazard_type=HazardType.SMOKE,
        state=HazardState.CONFIRMED,
        camera_id="camera_01",
        zone_id="production_floor",
        confidence=0.82,
        bbox=HazardBoundingBox.from_xyxy(50, 50, 200, 200),
        first_seen=datetime.now(timezone.utc).isoformat(),
        last_seen=datetime.now(timezone.utc).isoformat(),
        duration_seconds=12.5,
        detection_count=25,
        average_confidence=0.80,
        max_confidence=0.88,
        persistence_ratio=0.95,
        frames_detected=25,
        frames_missed=0,
    )
    ev_long = safety_engine.enforce_rule_2_smoke(hazard_long)
    assert ev_long is not None
    assert ev_long.details["priority"] == AlarmPriority.P0.value


def test_rule_3_multi_hazard_escalation(safety_engine):
    """Rule 3: Dual fire and smoke must escalate to MULTIPLE_HAZARDS P0 emergency."""
    h_fire = HazardEventDetail(
        event_id="haz_01",
        hazard_type=HazardType.FIRE,
        state=HazardState.CONFIRMED,
        camera_id="camera_01",
        zone_id="electrical_room",
        confidence=0.91,
        bbox=HazardBoundingBox.from_xyxy(10, 10, 50, 50),
        first_seen=datetime.now(timezone.utc).isoformat(),
        last_seen=datetime.now(timezone.utc).isoformat(),
        duration_seconds=3.0,
        detection_count=6,
        average_confidence=0.9,
        max_confidence=0.91,
        persistence_ratio=0.9,
        frames_detected=6,
        frames_missed=0,
    )
    h_smoke = HazardEventDetail(
        event_id="haz_02",
        hazard_type=HazardType.SMOKE,
        state=HazardState.CONFIRMED,
        camera_id="camera_01",
        zone_id="electrical_room",
        confidence=0.85,
        bbox=HazardBoundingBox.from_xyxy(60, 60, 120, 120),
        first_seen=datetime.now(timezone.utc).isoformat(),
        last_seen=datetime.now(timezone.utc).isoformat(),
        duration_seconds=3.0,
        detection_count=6,
        average_confidence=0.85,
        max_confidence=0.88,
        persistence_ratio=0.9,
        frames_detected=6,
        frames_missed=0,
    )
    ev_multi = safety_engine.enforce_rule_3_multi_hazard([h_fire, h_smoke], "camera_01", "electrical_room")
    assert ev_multi is not None
    assert ev_multi.event_type == EventType.MULTIPLE_HAZARDS
    assert ev_multi.details["priority"] == AlarmPriority.P0.value
    assert ev_multi.details["audible"] is True


def test_rule_4_confirmed_ppe_violation(safety_engine):
    """Rule 4: Confirmed ABSENT PPE generates P2 visual alert with NO audible siren."""
    worker = WorkerTrack(
        track_id=101,
        bbox=WorkerBoundingBox(x1=50, y1=50, x2=150, y2=300),
        confidence=0.89,
        ppe_status={"helmet": PPEState.ABSENT, "safety_vest": PPEState.PRESENT},
        ppe_details={
            "helmet": PPEObservation(item_type=PPEItemType.HELMET, state=PPEState.ABSENT, confidence=0.0, consecutive_missed=6),
            "safety_vest": PPEObservation(item_type=PPEItemType.SAFETY_VEST, state=PPEState.PRESENT, confidence=0.85, consecutive_hits=6),
        },
        is_compliant=False,
        history_length=15,
        first_seen=datetime.now(timezone.utc).isoformat(),
        last_seen=datetime.now(timezone.utc).isoformat(),
    )
    events = safety_engine.enforce_rule_4_and_5_ppe([worker], "camera_01", "production_floor")
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == EventType.MISSING_HELMET
    assert ev.track_id == 101
    assert ev.details["priority"] == AlarmPriority.P2.value
    assert ev.details["audible"] is False  # STRICT REQUIREMENT: No audible siren on PPE violations!


def test_rule_5_unknown_ppe_state_never_generates_violation(safety_engine):
    """Rule 5: UNKNOWN PPE state must strictly NEVER generate a violation."""
    worker = WorkerTrack(
        track_id=102,
        bbox=WorkerBoundingBox(x1=100, y1=100, x2=200, y2=400),
        confidence=0.85,
        ppe_status={"helmet": PPEState.UNKNOWN, "safety_vest": PPEState.UNKNOWN},
        ppe_details={
            "helmet": PPEObservation(item_type=PPEItemType.HELMET, state=PPEState.UNKNOWN, confidence=0.0),
            "safety_vest": PPEObservation(item_type=PPEItemType.SAFETY_VEST, state=PPEState.UNKNOWN, confidence=0.0),
        },
        is_compliant=True,  # UNKNOWN does not mark non-compliant
        history_length=2,
        first_seen=datetime.now(timezone.utc).isoformat(),
        last_seen=datetime.now(timezone.utc).isoformat(),
    )
    events = safety_engine.enforce_rule_4_and_5_ppe([worker], "camera_01", "production_floor")
    assert len(events) == 0  # STRICT: zero violation events produced!


def test_rule_6_camera_offline(safety_engine):
    """Rule 6: Camera disconnection triggers P3 advisory event."""
    ev = safety_engine.enforce_rule_6_camera_offline("camera_01", "loading_dock", is_connected=False)
    assert ev is not None
    assert ev.event_type == EventType.CAMERA_FAILURE
    assert ev.details["priority"] == AlarmPriority.P3.value
    assert ev.details["audible"] is False

    # When connected: no event
    assert safety_engine.enforce_rule_6_camera_offline("camera_01", "loading_dock", is_connected=True) is None


def test_rule_7_ai_unavailable(safety_engine):
    """Rule 7: AI engine unavailability triggers P3 advisory event."""
    ev = safety_engine.enforce_rule_7_ai_unavailable("camera_01", "loading_dock", ai_available=False)
    assert ev is not None
    assert ev.event_type == EventType.SYSTEM_FAILURE
    assert ev.details["priority"] == AlarmPriority.P3.value
    assert ev.details["audible"] is False

    # When available: no event
    assert safety_engine.enforce_rule_7_ai_unavailable("camera_01", "loading_dock", ai_available=True) is None


def test_master_scene_assessment_end_to_end(safety_engine):
    """Validates assess_scene combining PPE and hazard inputs into prioritized SafetyAssessment."""
    # Worker with missing vest
    worker = WorkerTrack(
        track_id=201,
        bbox=WorkerBoundingBox(x1=50, y1=50, x2=150, y2=300),
        confidence=0.88,
        ppe_status={"helmet": PPEState.PRESENT, "safety_vest": PPEState.ABSENT},
        ppe_details={
            "helmet": PPEObservation(item_type=PPEItemType.HELMET, state=PPEState.PRESENT, confidence=0.9),
            "safety_vest": PPEObservation(item_type=PPEItemType.SAFETY_VEST, state=PPEState.ABSENT, confidence=0.0, consecutive_missed=5),
        },
        is_compliant=False,
        history_length=15,
        first_seen=datetime.now(timezone.utc).isoformat(),
        last_seen=datetime.now(timezone.utc).isoformat(),
    )
    compliance_resp = ComplianceAnalysisResponse(
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        workers=[worker],
        summary=ComplianceSummary(total_workers=1, compliant_workers=0, non_compliant_workers=1, unknown_workers=0),
    )

    # Fire hazard present
    hazard = HazardEventDetail(
        event_id="haz_fire_master",
        hazard_type=HazardType.FIRE,
        state=HazardState.CONFIRMED,
        camera_id="camera_01",
        zone_id="storage_area",
        confidence=0.92,
        bbox=HazardBoundingBox.from_xyxy(10, 10, 80, 80),
        first_seen=datetime.now(timezone.utc).isoformat(),
        last_seen=datetime.now(timezone.utc).isoformat(),
        duration_seconds=6.0,
        detection_count=12,
        average_confidence=0.90,
        max_confidence=0.94,
        persistence_ratio=0.95,
        frames_detected=12,
        frames_missed=0,
    )
    hazard_resp = HazardAnalysisResponse(
        frame_id=1,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        camera_id="camera_01",
        zone_id="storage_area",
        scene_hazard_state=HazardState.CONFIRMED,
        relationship=HazardRelationship.FIRE_ONLY,
        hazards=[hazard],
        total_active_hazards=1,
    )

    assessment = safety_engine.assess_scene(
        camera_id="camera_01",
        zone_id="storage_area",
        compliance_response=compliance_resp,
        hazard_response=hazard_resp,
        camera_connected=True,
        ai_available=True,
    )

    assert isinstance(assessment, SafetyAssessment)
    assert assessment.camera_id == "camera_01"
    assert assessment.workers_count == 1
    assert assessment.active_violations_count == 1
    assert assessment.active_hazards_count == 1
    # Because fire is present, highest priority must be P0 and audible siren must be True
    assert assessment.highest_priority == AlarmPriority.P0
    assert assessment.requires_audible_siren is True
    assert assessment.overall_risk_score >= 80
