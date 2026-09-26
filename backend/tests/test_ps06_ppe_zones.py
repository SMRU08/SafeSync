"""
test_ps06_ppe_zones.py — Unit & Integration tests for PS06 Zone-Specific PPE Policy
Validates:
1. ZonePPEPolicyEngine correctly parses ppe_zones.yaml.
2. Zone "production_floor": full PPE required (helmet, safety_vest, gloves, safety_footwear).
3. Zone "storage_area": gloves are OPTIONAL ("gloves where applicable" requirement).
4. Zone "office": PPE is optional/disabled.
5. Fallback policy applies when an unlisted zone is encountered.
6. SafetyEngine Rule 4 & 5 integration:
   - Absent gloves in "storage_area" -> NO violation event generated.
   - Absent gloves in "production_floor" -> P2 violation event generated.
   - Absent helmet in "storage_area" -> P2 violation event generated.
   - Unknown state never generates a violation regardless of zone.
7. /api/compliance/ppe-zones endpoint returns valid policy structure.
"""

import pytest
from app.ai.compliance.ppe_policy import ZonePPEPolicyEngine, ALL_PPE_ITEMS
from app.ai.compliance.schemas import (
    WorkerTrack,
    WorkerBoundingBox,
    PPEObservation,
    PPEState,
    PPEItemType,
    OverallComplianceState,
)
from app.services.safety_engine import SafetyEngine
from app.ai.risk.schemas import EventType, AlarmPriority
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(autouse=True)
def reset_policy_engine():
    ZonePPEPolicyEngine.reset_instance()
    yield
    ZonePPEPolicyEngine.reset_instance()


def test_zone_policy_loader():
    """Verify that ZonePPEPolicyEngine loads production_floor and storage_area configs."""
    engine = ZonePPEPolicyEngine.get_instance()
    
    # Production floor
    prod_policy = engine.get_policy_for_zone("production_floor")
    assert prod_policy.is_required("helmet") is True
    assert prod_policy.is_required("safety_vest") is True
    assert prod_policy.is_required("gloves") is True
    assert prod_policy.is_required("safety_footwear") is True
    assert prod_policy.is_optional("gloves") is False

    # Storage area (Gloves where applicable -> gloves are optional!)
    storage_policy = engine.get_policy_for_zone("storage_area")
    assert storage_policy.is_required("helmet") is True
    assert storage_policy.is_required("safety_vest") is True
    assert storage_policy.is_required("gloves") is False
    assert storage_policy.is_optional("gloves") is True
    assert storage_policy.is_required("safety_footwear") is True


def test_zone_policy_fallback():
    """Verify that an unconfigured zone falls back to the default policy."""
    engine = ZonePPEPolicyEngine.get_instance()
    fallback_policy = engine.get_policy_for_zone("unknown_mystery_zone")
    assert fallback_policy.is_required("helmet") is True
    assert fallback_policy.is_required("safety_vest") is True
    assert fallback_policy.is_required("gloves") is True
    assert fallback_policy.is_required("safety_footwear") is True


def _create_mock_worker(track_id: int, ppe_states: dict) -> WorkerTrack:
    wb = WorkerBoundingBox(x1=100, y1=100, x2=200, y2=400)
    details = {}
    summary = {}
    for item_type in PPEItemType:
        state = ppe_states.get(item_type.value, PPEState.UNKNOWN)
        summary[item_type.value] = state
        details[item_type.value] = PPEObservation(
            item_type=item_type,
            state=state,
            consecutive_seen=5 if state == PPEState.PRESENT else 0,
            consecutive_missed=5 if state == PPEState.ABSENT else 0,
        )
    return WorkerTrack(
        track_id=track_id,
        bbox=wb,
        confidence=0.92,
        ppe=summary,
        ppe_details=details,
        overall_status=OverallComplianceState.NON_COMPLIANT,
    )


def test_safety_engine_gloves_optional_in_storage_area():
    """
    PS06 Core Test:
    Worker in 'storage_area' is missing gloves, but wearing helmet, vest, and shoes.
    Because gloves are optional in storage_area, NO violation must be generated.
    """
    safety_engine = SafetyEngine()
    
    worker = _create_mock_worker(
        track_id=101,
        ppe_states={
            "helmet": PPEState.PRESENT,
            "safety_vest": PPEState.PRESENT,
            "gloves": PPEState.ABSENT,  # Missing gloves!
            "safety_footwear": PPEState.PRESENT,
        },
    )

    events = safety_engine.enforce_rule_4_and_5_ppe(
        workers=[worker],
        camera_id="camera_02",
        zone_id="storage_area",
    )

    # In storage_area, gloves are optional -> zero violations generated!
    assert len(events) == 0


def test_safety_engine_gloves_required_in_production_floor():
    """
    PS06 Core Test:
    Worker in 'production_floor' is missing gloves.
    Because gloves are mandatory in production_floor, a P2 MISSING_GLOVES violation MUST be generated.
    """
    safety_engine = SafetyEngine()
    
    worker = _create_mock_worker(
        track_id=102,
        ppe_states={
            "helmet": PPEState.PRESENT,
            "safety_vest": PPEState.PRESENT,
            "gloves": PPEState.ABSENT,  # Missing gloves!
            "safety_footwear": PPEState.PRESENT,
        },
    )

    events = safety_engine.enforce_rule_4_and_5_ppe(
        workers=[worker],
        camera_id="camera_01",
        zone_id="production_floor",
    )

    assert len(events) == 1
    assert events[0].event_type == EventType.MISSING_GLOVES
    assert events[0].details["priority"] == AlarmPriority.P2.value
    assert events[0].details["zone_policy"] == "required"


def test_safety_engine_missing_helmet_in_storage_area():
    """
    Worker in 'storage_area' is missing helmet.
    Helmet is required in all industrial zones, so a P2 MISSING_HELMET violation must be generated.
    """
    safety_engine = SafetyEngine()
    
    worker = _create_mock_worker(
        track_id=103,
        ppe_states={
            "helmet": PPEState.ABSENT,  # Missing helmet!
            "safety_vest": PPEState.PRESENT,
            "gloves": PPEState.PRESENT,
            "safety_footwear": PPEState.PRESENT,
        },
    )

    events = safety_engine.enforce_rule_4_and_5_ppe(
        workers=[worker],
        camera_id="camera_02",
        zone_id="storage_area",
    )

    assert len(events) == 1
    assert events[0].event_type == EventType.MISSING_HELMET
    assert events[0].details["priority"] == AlarmPriority.P2.value


def test_safety_engine_rule_5_unknown_state_never_violates():
    """
    Rule 5 check: UNKNOWN PPE state must never produce a violation,
    even in production_floor where all PPE is required.
    """
    safety_engine = SafetyEngine()
    
    worker = _create_mock_worker(
        track_id=104,
        ppe_states={
            "helmet": PPEState.UNKNOWN,
            "safety_vest": PPEState.UNKNOWN,
            "gloves": PPEState.UNKNOWN,
            "safety_footwear": PPEState.UNKNOWN,
        },
    )

    events = safety_engine.enforce_rule_4_and_5_ppe(
        workers=[worker],
        camera_id="camera_01",
        zone_id="production_floor",
    )

    assert len(events) == 0


def test_api_compliance_ppe_zones_endpoint():
    """Verify GET /api/compliance/ppe-zones returns registered zones and their policies."""
    client = TestClient(app)
    response = client.get("/api/compliance/ppe-zones")
    assert response.status_code == 200
    data = response.json()
    assert "zones" in data
    assert data["total_zones"] >= 5
    
    # Check production_floor entry
    prod = next((z for z in data["zones"] if z["zone_id"] == "production_floor"), None)
    assert prod is not None
    assert "gloves" in prod["required"]

    # Check storage_area entry
    storage = next((z for z in data["zones"] if z["zone_id"] == "storage_area"), None)
    assert storage is not None
    assert "gloves" in storage["optional"]
