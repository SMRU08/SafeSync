"""
test_ps06_ppe_zones.py — PS06 Zone-Specific PPE Policy — Full Validation Suite

Tests:
  1. Policy loading from ppe_zones.yaml
  2. required PPE per zone
  3. optional PPE per zone (no violation)
  4. disabled PPE per zone (no violation)
  5. UNKNOWN state never generates a violation (Rule 5)
  6. Missing required gloves in production_floor → P2 violation
  7. Missing optional gloves in storage_area → no violation
  8. Different zones having different rules
  9. Fallback/default policy for unconfigured zones
  10. SafetyEngine Rule 4+5 zone-aware integration
  11. /api/compliance/ppe-zones endpoint
  12. Temporal tracker zone_id propagation
"""

import pytest
from app.ai.compliance.ppe_policy import (
    ZonePPEPolicyEngine,
    ZonePPEPolicy,
    PPE_POLICY_REQUIRED,
    PPE_POLICY_OPTIONAL,
    PPE_POLICY_DISABLED,
    ALL_PPE_ITEMS,
)
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


# ─────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_policy_engine():
    """Reset singleton between tests to avoid contamination."""
    ZonePPEPolicyEngine.reset_instance()
    yield
    ZonePPEPolicyEngine.reset_instance()


def _make_worker(track_id: int, ppe_states: dict) -> WorkerTrack:
    """Helper: build a WorkerTrack with specific PPE states per item."""
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
            confidence=0.90 if state != PPEState.UNKNOWN else None,
        )
    overall = (
        OverallComplianceState.NON_COMPLIANT
        if PPEState.ABSENT in ppe_states.values()
        else OverallComplianceState.UNKNOWN
        if PPEState.UNKNOWN in ppe_states.values()
        else OverallComplianceState.COMPLIANT
    )
    return WorkerTrack(
        track_id=track_id,
        bbox=wb,
        confidence=0.92,
        ppe=summary,
        ppe_details=details,
        overall_status=overall,
        history_length=20,
    )


# ─────────────────────────────────────────────────────────────────
# 1. Policy Loading
# ─────────────────────────────────────────────────────────────────

class TestPolicyLoading:

    def test_engine_loads_without_error(self):
        engine = ZonePPEPolicyEngine.get_instance()
        assert engine is not None

    def test_singleton_is_consistent(self):
        e1 = ZonePPEPolicyEngine.get_instance()
        e2 = ZonePPEPolicyEngine.get_instance()
        assert e1 is e2

    def test_known_zones_are_loaded(self):
        engine = ZonePPEPolicyEngine.get_instance()
        zones = engine.list_all_zones()
        zone_ids = {z["zone_id"] for z in zones}
        # At least these 5 zones defined in ppe_zones.yaml
        for expected in ["production_floor", "storage_area", "electrical_room", "loading_dock", "welding_area"]:
            assert expected in zone_ids, f"Zone '{expected}' not found in loaded policy"

    def test_all_ppe_items_covered_per_zone(self):
        engine = ZonePPEPolicyEngine.get_instance()
        for zone_data in engine.list_all_zones():
            zone_id = zone_data["zone_id"]
            policy = engine.get_policy_for_zone(zone_id)
            for item in ALL_PPE_ITEMS:
                pol = policy.get_policy(item)
                assert pol in (PPE_POLICY_REQUIRED, PPE_POLICY_OPTIONAL, PPE_POLICY_DISABLED), \
                    f"Zone {zone_id} item {item} has invalid policy: {pol}"


# ─────────────────────────────────────────────────────────────────
# 2. Required PPE Rules
# ─────────────────────────────────────────────────────────────────

class TestRequiredPPE:

    def test_production_floor_all_required(self):
        engine = ZonePPEPolicyEngine.get_instance()
        policy = engine.get_policy_for_zone("production_floor")
        assert policy.is_required("helmet")
        assert policy.is_required("safety_vest")
        assert policy.is_required("gloves")
        assert policy.is_required("safety_footwear")

    def test_electrical_room_all_required(self):
        engine = ZonePPEPolicyEngine.get_instance()
        policy = engine.get_policy_for_zone("electrical_room")
        assert policy.is_required("helmet")
        assert policy.is_required("safety_vest")
        assert policy.is_required("gloves")
        assert policy.is_required("safety_footwear")

    def test_welding_area_all_required(self):
        engine = ZonePPEPolicyEngine.get_instance()
        policy = engine.get_policy_for_zone("welding_area")
        assert policy.is_required("helmet")
        assert policy.is_required("safety_vest")
        assert policy.is_required("gloves")
        assert policy.is_required("safety_footwear")

    def test_required_items_list_non_empty(self):
        engine = ZonePPEPolicyEngine.get_instance()
        policy = engine.get_policy_for_zone("production_floor")
        assert len(policy.get_required_items()) > 0


# ─────────────────────────────────────────────────────────────────
# 3. Optional PPE Rules
# ─────────────────────────────────────────────────────────────────

class TestOptionalPPE:

    def test_storage_area_gloves_are_optional(self):
        """PS06 core: 'gloves where applicable' — storage areas do not require gloves."""
        engine = ZonePPEPolicyEngine.get_instance()
        policy = engine.get_policy_for_zone("storage_area")
        assert policy.is_optional("gloves"), "storage_area gloves should be optional"
        assert not policy.is_required("gloves"), "storage_area gloves must NOT be required"

    def test_loading_dock_gloves_are_optional(self):
        engine = ZonePPEPolicyEngine.get_instance()
        policy = engine.get_policy_for_zone("loading_dock")
        assert policy.is_optional("gloves"), "loading_dock gloves should be optional"
        assert not policy.is_required("gloves"), "loading_dock gloves must NOT be required"

    def test_optional_items_list(self):
        engine = ZonePPEPolicyEngine.get_instance()
        policy = engine.get_policy_for_zone("storage_area")
        assert "gloves" in policy.get_optional_items()


# ─────────────────────────────────────────────────────────────────
# 4. Disabled PPE Rules
# ─────────────────────────────────────────────────────────────────

class TestDisabledPPE:

    def test_office_has_disabled_or_optional_ppe(self):
        """Office zone should have no required PPE (all optional/disabled)."""
        engine = ZonePPEPolicyEngine.get_instance()
        policy = engine.get_policy_for_zone("office")
        required_items = policy.get_required_items()
        assert len(required_items) == 0, (
            f"Office zone should have no required PPE, but has: {required_items}"
        )

    def test_disabled_ppe_is_not_required(self):
        engine = ZonePPEPolicyEngine.get_instance()
        for zone_data in engine.list_all_zones():
            policy = engine.get_policy_for_zone(zone_data["zone_id"])
            for item in policy.get_disabled_items():
                assert not policy.is_required(item), \
                    f"Disabled item {item} in zone {zone_data['zone_id']} must not be required"

    def test_disabled_ppe_is_not_optional(self):
        engine = ZonePPEPolicyEngine.get_instance()
        for zone_data in engine.list_all_zones():
            policy = engine.get_policy_for_zone(zone_data["zone_id"])
            for item in policy.get_disabled_items():
                assert not policy.is_optional(item), \
                    f"Disabled item {item} must not also be optional"


# ─────────────────────────────────────────────────────────────────
# 5. UNKNOWN state — Rule 5 protection
# ─────────────────────────────────────────────────────────────────

class TestUnknownStateProtection:

    def test_unknown_never_generates_violation_in_any_zone(self):
        """Rule 5: UNKNOWN must NEVER generate a P2 violation regardless of zone."""
        safety_engine = SafetyEngine()
        worker = _make_worker(
            track_id=999,
            ppe_states={
                "helmet": PPEState.UNKNOWN,
                "safety_vest": PPEState.UNKNOWN,
                "gloves": PPEState.UNKNOWN,
                "safety_footwear": PPEState.UNKNOWN,
            },
        )
        for zone in ["production_floor", "storage_area", "electrical_room", "office", "UNKNOWN"]:
            events = safety_engine.enforce_rule_4_and_5_ppe(
                workers=[worker],
                camera_id="test_camera",
                zone_id=zone,
            )
            assert len(events) == 0, (
                f"UNKNOWN PPE state must not generate violations in zone '{zone}', "
                f"but got {len(events)} events"
            )

    def test_present_never_generates_violation(self):
        """PPE PRESENT state must not generate any violation."""
        safety_engine = SafetyEngine()
        worker = _make_worker(
            track_id=998,
            ppe_states={
                "helmet": PPEState.PRESENT,
                "safety_vest": PPEState.PRESENT,
                "gloves": PPEState.PRESENT,
                "safety_footwear": PPEState.PRESENT,
            },
        )
        events = safety_engine.enforce_rule_4_and_5_ppe(
            workers=[worker], camera_id="cam01", zone_id="production_floor"
        )
        assert len(events) == 0


# ─────────────────────────────────────────────────────────────────
# 6. Missing required gloves in production_floor → P2 violation
# ─────────────────────────────────────────────────────────────────

class TestMissingRequiredGloves:

    def test_absent_gloves_in_production_floor_generates_p2(self):
        """PS06 core: missing required PPE in a zone where it is required → P2 violation."""
        safety_engine = SafetyEngine()
        worker = _make_worker(
            track_id=101,
            ppe_states={
                "helmet": PPEState.PRESENT,
                "safety_vest": PPEState.PRESENT,
                "gloves": PPEState.ABSENT,
                "safety_footwear": PPEState.PRESENT,
            },
        )
        events = safety_engine.enforce_rule_4_and_5_ppe(
            workers=[worker], camera_id="camera_01", zone_id="production_floor"
        )
        assert len(events) == 1, f"Expected 1 violation, got {len(events)}"
        assert events[0].event_type == EventType.MISSING_GLOVES
        assert events[0].details["priority"] == AlarmPriority.P2.value
        assert events[0].details.get("zone_policy") == "required"

    def test_absent_gloves_in_electrical_room_generates_p2(self):
        safety_engine = SafetyEngine()
        worker = _make_worker(
            track_id=102,
            ppe_states={"helmet": PPEState.PRESENT, "safety_vest": PPEState.PRESENT,
                        "gloves": PPEState.ABSENT, "safety_footwear": PPEState.PRESENT},
        )
        events = safety_engine.enforce_rule_4_and_5_ppe(
            workers=[worker], camera_id="camera_01", zone_id="electrical_room"
        )
        assert len(events) == 1
        assert events[0].event_type == EventType.MISSING_GLOVES

    def test_absent_helmet_always_generates_violation(self):
        """Helmet is required in ALL industrial zones (production_floor, storage_area, etc.)."""
        safety_engine = SafetyEngine()
        worker = _make_worker(
            track_id=103,
            ppe_states={"helmet": PPEState.ABSENT, "safety_vest": PPEState.PRESENT,
                        "gloves": PPEState.PRESENT, "safety_footwear": PPEState.PRESENT},
        )
        for zone in ["production_floor", "storage_area", "electrical_room", "loading_dock", "welding_area"]:
            events = safety_engine.enforce_rule_4_and_5_ppe(
                workers=[worker], camera_id="cam01", zone_id=zone
            )
            assert any(e.event_type == EventType.MISSING_HELMET for e in events), \
                f"Missing helmet should generate violation in zone '{zone}'"


# ─────────────────────────────────────────────────────────────────
# 7. Optional gloves in storage_area → no violation
# ─────────────────────────────────────────────────────────────────

class TestOptionalGlovesNoViolation:

    def test_absent_optional_gloves_in_storage_area_no_violation(self):
        """PS06: 'gloves where applicable' — storage_area gloves ABSENT must NOT be a violation."""
        safety_engine = SafetyEngine()
        worker = _make_worker(
            track_id=201,
            ppe_states={"helmet": PPEState.PRESENT, "safety_vest": PPEState.PRESENT,
                        "gloves": PPEState.ABSENT, "safety_footwear": PPEState.PRESENT},
        )
        events = safety_engine.enforce_rule_4_and_5_ppe(
            workers=[worker], camera_id="camera_02", zone_id="storage_area"
        )
        assert len(events) == 0, (
            f"Optional gloves in storage_area must NOT generate violations, "
            f"but got {len(events)}"
        )

    def test_absent_optional_gloves_in_loading_dock_no_violation(self):
        safety_engine = SafetyEngine()
        worker = _make_worker(
            track_id=202,
            ppe_states={"helmet": PPEState.PRESENT, "safety_vest": PPEState.PRESENT,
                        "gloves": PPEState.ABSENT, "safety_footwear": PPEState.PRESENT},
        )
        events = safety_engine.enforce_rule_4_and_5_ppe(
            workers=[worker], camera_id="camera_02", zone_id="loading_dock"
        )
        assert len(events) == 0, "Optional gloves in loading_dock must not generate violations"


# ─────────────────────────────────────────────────────────────────
# 8. Different zones have different rules
# ─────────────────────────────────────────────────────────────────

class TestZonesDifferentRules:

    def test_gloves_required_in_production_optional_in_storage(self):
        engine = ZonePPEPolicyEngine.get_instance()
        prod = engine.get_policy_for_zone("production_floor")
        stor = engine.get_policy_for_zone("storage_area")
        assert prod.is_required("gloves")
        assert not stor.is_required("gloves")

    def test_office_vs_welding_area_differ_significantly(self):
        engine = ZonePPEPolicyEngine.get_instance()
        office = engine.get_policy_for_zone("office")
        welding = engine.get_policy_for_zone("welding_area")
        office_req = set(office.get_required_items())
        welding_req = set(welding.get_required_items())
        assert len(welding_req) > len(office_req), \
            "Welding area should require more PPE than office zone"

    def test_storage_area_requires_helmet_and_vest(self):
        engine = ZonePPEPolicyEngine.get_instance()
        policy = engine.get_policy_for_zone("storage_area")
        assert policy.is_required("helmet")
        assert policy.is_required("safety_vest")

    def test_different_violations_different_zones(self):
        """Worker missing gloves: violation in production_floor, not in storage_area."""
        safety_engine = SafetyEngine()
        worker_prod = _make_worker(301, {"helmet": PPEState.PRESENT, "safety_vest": PPEState.PRESENT,
                                         "gloves": PPEState.ABSENT, "safety_footwear": PPEState.PRESENT})
        worker_stor = _make_worker(302, {"helmet": PPEState.PRESENT, "safety_vest": PPEState.PRESENT,
                                         "gloves": PPEState.ABSENT, "safety_footwear": PPEState.PRESENT})
        prod_events = safety_engine.enforce_rule_4_and_5_ppe(
            workers=[worker_prod], camera_id="cam01", zone_id="production_floor"
        )
        stor_events = safety_engine.enforce_rule_4_and_5_ppe(
            workers=[worker_stor], camera_id="cam02", zone_id="storage_area"
        )
        assert len(prod_events) == 1, "Production floor should generate 1 glove violation"
        assert len(stor_events) == 0, "Storage area should generate 0 violations for missing gloves"


# ─────────────────────────────────────────────────────────────────
# 9. Fallback / Default Policy
# ─────────────────────────────────────────────────────────────────

class TestFallbackPolicy:

    def test_unknown_zone_falls_back_to_default(self):
        engine = ZonePPEPolicyEngine.get_instance()
        policy = engine.get_policy_for_zone("totally_unknown_zone_xyz")
        # Default policy should require at minimum helmet and safety_vest
        assert policy is not None
        # All 4 items should have a defined policy
        for item in ALL_PPE_ITEMS:
            pol = policy.get_policy(item)
            assert pol in (PPE_POLICY_REQUIRED, PPE_POLICY_OPTIONAL, PPE_POLICY_DISABLED)

    def test_empty_zone_id_falls_back(self):
        engine = ZonePPEPolicyEngine.get_instance()
        policy = engine.get_policy_for_zone("")
        assert policy is not None

    def test_none_zone_id_falls_back(self):
        engine = ZonePPEPolicyEngine.get_instance()
        policy = engine.get_policy_for_zone(None)
        assert policy is not None

    def test_fallback_defaults_to_all_required(self):
        """Default policy should be strict (all required) for safety."""
        engine = ZonePPEPolicyEngine.get_instance()
        fallback = engine.get_policy_for_zone("nonexistent_zone")
        # At minimum helmet should be required
        assert fallback.is_required("helmet"), "Default policy must require helmets"
        assert fallback.is_required("safety_vest"), "Default policy must require vests"

    def test_safety_engine_uses_all_required_for_unknown_zone(self):
        """If zone is unknown, all PPE treated as required (fail-safe)."""
        safety_engine = SafetyEngine()
        worker = _make_worker(
            track_id=401,
            ppe_states={"helmet": PPEState.ABSENT, "safety_vest": PPEState.PRESENT,
                        "gloves": PPEState.PRESENT, "safety_footwear": PPEState.PRESENT},
        )
        events = safety_engine.enforce_rule_4_and_5_ppe(
            workers=[worker], camera_id="cam_unknown", zone_id="UNKNOWN_ZONE_XYZ"
        )
        assert any(e.event_type == EventType.MISSING_HELMET for e in events), \
            "Unknown zone should fall back to default (strict) policy and generate helmet violation"


# ─────────────────────────────────────────────────────────────────
# 10. Invalid configuration handling
# ─────────────────────────────────────────────────────────────────

class TestInvalidConfiguration:

    def test_engine_handles_missing_config_gracefully(self):
        """Engine must not crash even if ppe_zones.yaml is missing."""
        ZonePPEPolicyEngine.reset_instance()
        engine = ZonePPEPolicyEngine(config_path="/nonexistent/path/ppe_zones.yaml")
        # Should fall back to hard defaults
        policy = engine.get_policy_for_zone("any_zone")
        assert policy is not None
        assert policy.is_required("helmet")

    def test_policy_api_does_not_crash(self):
        engine = ZonePPEPolicyEngine.get_instance()
        # Should never crash on strange inputs
        for zone_input in [None, "", "  ", "123", "ZONE@#$", "a" * 200]:
            try:
                policy = engine.get_policy_for_zone(zone_input)
                assert policy is not None
            except Exception as e:
                pytest.fail(f"ZonePPEPolicyEngine.get_policy_for_zone({zone_input!r}) raised: {e}")


# ─────────────────────────────────────────────────────────────────
# 11. API Endpoint
# ─────────────────────────────────────────────────────────────────

class TestPPEZonesAPIEndpoint:

    def test_ppe_zones_endpoint_returns_200(self):
        client = TestClient(app)
        resp = client.get("/api/compliance/ppe-zones")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_ppe_zones_endpoint_contains_zones(self):
        client = TestClient(app)
        data = client.get("/api/compliance/ppe-zones").json()
        assert "zones" in data
        assert data["total_zones"] >= 5

    def test_production_floor_in_api_response(self):
        client = TestClient(app)
        data = client.get("/api/compliance/ppe-zones").json()
        prod = next((z for z in data["zones"] if z["zone_id"] == "production_floor"), None)
        assert prod is not None, "production_floor must appear in /api/compliance/ppe-zones"
        assert "gloves" in prod.get("required", [])

    def test_storage_area_gloves_optional_in_api_response(self):
        client = TestClient(app)
        data = client.get("/api/compliance/ppe-zones").json()
        stor = next((z for z in data["zones"] if z["zone_id"] == "storage_area"), None)
        assert stor is not None, "storage_area must appear in /api/compliance/ppe-zones"
        assert "gloves" in stor.get("optional", [])

    def test_ps06_note_in_api_response(self):
        client = TestClient(app)
        data = client.get("/api/compliance/ppe-zones").json()
        assert "ps06_note" in data


# ─────────────────────────────────────────────────────────────────
# 12. Temporal tracker zone_id propagation
# ─────────────────────────────────────────────────────────────────

class TestTemporalTrackerZoneId:

    def test_temporal_tracker_accepts_zone_id(self):
        """TemporalComplianceTracker.update_worker must accept zone_id without error."""
        from app.ai.compliance.temporal import TemporalComplianceTracker
        import numpy as np
        from app.ai.compliance.schemas import PPEItemType

        config = {}
        tracker = TemporalComplianceTracker(config)
        bbox = np.array([100, 100, 200, 400], dtype=float)
        assoc = {item.value: None for item in PPEItemType}
        occ_flags = {item: False for item in PPEItemType}

        # Should not raise
        result = tracker.update_worker(
            track_id=1,
            worker_bbox=bbox,
            confidence=0.9,
            associations=assoc,
            is_occluded_flags=occ_flags,
            zone_id="production_floor",
        )
        assert result is not None

    def test_temporal_tracker_zone_id_optional(self):
        """Calling update_worker without zone_id must still work (backward compat)."""
        from app.ai.compliance.temporal import TemporalComplianceTracker
        import numpy as np
        from app.ai.compliance.schemas import PPEItemType

        config = {}
        tracker = TemporalComplianceTracker(config)
        bbox = np.array([100, 100, 200, 400], dtype=float)
        assoc = {item.value: None for item in PPEItemType}
        occ_flags = {item: False for item in PPEItemType}

        # Should not raise even without zone_id
        result = tracker.update_worker(
            track_id=2,
            worker_bbox=bbox,
            confidence=0.9,
            associations=assoc,
            is_occluded_flags=occ_flags,
            # No zone_id passed — uses default
        )
        assert result is not None
