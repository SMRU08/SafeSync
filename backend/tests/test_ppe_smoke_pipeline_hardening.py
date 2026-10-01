"""
test_ppe_smoke_pipeline_hardening.py — SafeSync PPE + Smoke Pipeline Hardening Tests

Tests Sections 2, 9-18, 19-24 of the master audit prompt.
All tests are unit-level (no running server, no camera, no DB required).
"""

import sys
import os
import numpy as np
import pytest

# Path setup (also done by conftest.py but explicit here for standalone runs)
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for p in [_BACKEND, _ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)


# ── imports ────────────────────────────────────────────────────────────────────
try:
    from app.ai.compliance.association import (
        verify_helmet_features,
        verify_safety_vest_features,
        SpatialPPEAssociator,
    )
    from app.ai.compliance.temporal import TemporalComplianceTracker
    from app.ai.compliance.schemas import PPEItemType, PPEState
except ImportError:
    from backend.app.ai.compliance.association import (
        verify_helmet_features,
        verify_safety_vest_features,
        SpatialPPEAssociator,
    )
    from backend.app.ai.compliance.temporal import TemporalComplianceTracker
    from backend.app.ai.compliance.schemas import PPEItemType, PPEState


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Wide-brim hard hat aspect ratio acceptance
# ─────────────────────────────────────────────────────────────────────────────
def test_helmet_wide_brim_aspect_ratio():
    """
    Root-cause fix: wide-brim hard hat has pw/ph ≈ 2.26 which was previously
    rejected by the hard limit of 1.90. Now extended to 2.80.
    """
    # Worker: 100×300 box (standing, head at top)
    worker_box = np.array([100.0, 50.0, 200.0, 350.0])  # 100×300
    # Wide-brim helmet: 90×40 px → aspect = 2.25
    helmet_box = np.array([105.0, 55.0, 195.0, 95.0])   # 90 wide, 40 tall → 2.25
    result = verify_helmet_features(
        worker_box, helmet_box, frame=None, confidence=0.55, img_shape=(480, 640)
    )
    assert result is True, (
        f"Wide-brim hard hat (pw/ph=2.25) must pass verify_helmet_features(). Got False."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Standard round helmet still passes
# ─────────────────────────────────────────────────────────────────────────────
def test_helmet_round_aspect_ratio():
    """Standard round safety helmet (pw/ph ≈ 1.1) must still pass."""
    worker_box = np.array([100.0, 50.0, 200.0, 350.0])
    helmet_box = np.array([125.0, 58.0, 180.0, 108.0])  # 55×50 → 1.1
    result = verify_helmet_features(
        worker_box, helmet_box, frame=None, confidence=0.55, img_shape=(480, 640)
    )
    assert result is True


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Half-body worker — footwear must be UNKNOWN (not ABSENT)
# ─────────────────────────────────────────────────────────────────────────────
def test_half_body_worker_footwear_is_unknown():
    """
    Half-body framing: worker bbox has wh/ww < 2.0 (e.g., portrait/bust shot).
    Safety footwear must evaluate to UNKNOWN, not ABSENT.
    """
    associator = SpatialPPEAssociator()
    img_shape = (480, 640)
    # Worker visible only from waist up: 120px wide, 150px tall → wh/ww = 1.25
    worker_box = np.array([100.0, 100.0, 220.0, 250.0])

    # Test via detect_occlusion
    is_occ = associator.detect_occlusion(
        worker_idx=0,
        worker_boxes=[worker_box],
        item_type=PPEItemType.SAFETY_FOOTWEAR,
        img_shape=img_shape,
    )
    assert is_occ is True, (
        "Half-body worker (wh/ww=1.25) SAFETY_FOOTWEAR zone must be detected as occluded"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Temporal tolerance — PPE not dropped after 5 missed frames
# ─────────────────────────────────────────────────────────────────────────────
def test_temporal_tolerance_6_frames():
    """
    With missing_detection_tolerance=6, PPE confirmed PRESENT must stay PRESENT
    through 5 consecutive missed frames (below tolerance).
    """
    cfg = {"temporal": {"missing_detection_tolerance": 6, "confirmation_frames": 2}}
    tracker = TemporalComplianceTracker(config=cfg)

    worker_bbox = np.array([100.0, 50.0, 200.0, 350.0])
    associations_present = {
        PPEItemType.HELMET.value: {"confidence": 0.75, "bbox": [125, 60, 180, 105]},
        PPEItemType.SAFETY_VEST.value: None,
        PPEItemType.GLOVES.value: None,
        PPEItemType.SAFETY_FOOTWEAR.value: None,
    }
    associations_empty = {k: None for k in associations_present}
    occlusion_flags = {item: False for item in PPEItemType}

    # Confirm helmet over 3 frames
    for _ in range(3):
        tracker.current_frame += 1
        tracker.update_worker(1, worker_bbox, 0.9, associations_present, occlusion_flags)

    # Now miss for 5 frames (< tolerance of 6)
    for _ in range(5):
        tracker.current_frame += 1
        wt = tracker.update_worker(1, worker_bbox, 0.9, associations_empty, occlusion_flags)

    assert wt.ppe.get("helmet") in (PPEState.PRESENT, PPEState.UNKNOWN), (
        f"Helmet must NOT flip to ABSENT after only 5 missed frames (tolerance=6). Got: {wt.ppe.get('helmet')}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Temporal tolerance — PPE becomes ABSENT only after 6+ missed frames
# ─────────────────────────────────────────────────────────────────────────────
def test_temporal_absent_after_tolerance_exceeded():
    """PPE must become ABSENT after missing_detection_tolerance (6) consecutive misses."""
    cfg = {"temporal": {"missing_detection_tolerance": 6, "confirmation_frames": 2}}
    tracker = TemporalComplianceTracker(config=cfg)

    worker_bbox = np.array([100.0, 50.0, 200.0, 350.0])
    associations_present = {
        PPEItemType.HELMET.value: {"confidence": 0.75, "bbox": [125, 60, 180, 105]},
        PPEItemType.SAFETY_VEST.value: None,
        PPEItemType.GLOVES.value: None,
        PPEItemType.SAFETY_FOOTWEAR.value: None,
    }
    associations_empty = {k: None for k in associations_present}
    occlusion_flags = {item: False for item in PPEItemType}

    # Confirm over 3 frames
    for _ in range(3):
        tracker.current_frame += 1
        tracker.update_worker(1, worker_bbox, 0.9, associations_present, occlusion_flags)

    # Miss for 7 frames (exceeds tolerance of 6)
    for _ in range(7):
        tracker.current_frame += 1
        wt = tracker.update_worker(1, worker_bbox, 0.9, associations_empty, occlusion_flags)

    assert wt.ppe.get("helmet") == PPEState.ABSENT, (
        f"Helmet must be ABSENT after 7 missed frames (tolerance=6). Got: {wt.ppe.get('helmet')}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Occlusion resets consecutive_missed (no ABSENT after clearing)
# ─────────────────────────────────────────────────────────────────────────────
def test_occlusion_resets_missed_counter():
    """
    When is_occluded=True, _consecutive_missed must be reset to 0.
    After occlusion clears, the first clear-frame must NOT see ABSENT
    (because missed count was reset during occlusion).
    """
    cfg = {"temporal": {"missing_detection_tolerance": 2, "confirmation_frames": 2}}
    tracker = TemporalComplianceTracker(config=cfg)

    worker_bbox = np.array([100.0, 50.0, 200.0, 350.0])
    assoc_present = {
        PPEItemType.HELMET.value: {"confidence": 0.75, "bbox": [125, 60, 180, 105]},
        PPEItemType.SAFETY_VEST.value: None,
        PPEItemType.GLOVES.value: None,
        PPEItemType.SAFETY_FOOTWEAR.value: None,
    }
    assoc_empty = {k: None for k in assoc_present}
    not_occluded = {item: False for item in PPEItemType}
    is_occluded = {item: False for item in PPEItemType}
    is_occluded[PPEItemType.HELMET] = True

    # Confirm helmet
    for _ in range(3):
        tracker.current_frame += 1
        tracker.update_worker(1, worker_bbox, 0.9, assoc_present, not_occluded)

    # 3 frames of occlusion (would normally exceed tolerance=2 → ABSENT)
    for _ in range(3):
        tracker.current_frame += 1
        tracker.update_worker(1, worker_bbox, 0.9, assoc_empty, is_occluded)

    # After occlusion clears — first frame without PPE must NOT be ABSENT
    tracker.current_frame += 1
    wt = tracker.update_worker(1, worker_bbox, 0.9, assoc_empty, not_occluded)

    # Should be UNKNOWN (missed_count=1 after reset, < tolerance=2) not ABSENT
    assert wt.ppe.get("helmet") != PPEState.ABSENT, (
        "Helmet must NOT be ABSENT immediately after occlusion clears — "
        "occlusion should have reset _consecutive_missed to 0"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: Smoke visualizer state gate — CANDIDATE not rendered
# ─────────────────────────────────────────────────────────────────────────────
def test_smoke_visualizer_state_gate():
    """
    Visualizer must skip CANDIDATE/DETECTING smoke boxes with conf < 0.35.
    Only CONFIRMED/ACTIVE smoke gets drawn on HUD.
    """
    try:
        from app.ai.compliance.visualizer import ComplianceVisualizer
    except ImportError:
        from backend.app.ai.compliance.visualizer import ComplianceVisualizer

    vis = ComplianceVisualizer()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # CANDIDATE smoke at 25% confidence — must NOT be drawn (verified by checking output unchanged)
    candidate_hazard = {
        "bbox": [100, 100, 200, 200],
        "class_name": "smoke",
        "confidence": 0.25,
        "state": "CANDIDATE",
    }
    out = vis.draw_frame(frame.copy(), [], hazards=[candidate_hazard])
    # Frame should be unchanged (no rectangle drawn)
    diff = np.sum(np.abs(out.astype(int) - frame.astype(int)))
    assert diff == 0, (
        f"CANDIDATE smoke at 25% must NOT be drawn on HUD. Pixel diff={diff}"
    )

    # CONFIRMED smoke at 35% confidence — MUST be drawn
    confirmed_hazard = {
        "bbox": [100, 100, 200, 200],
        "class_name": "smoke",
        "confidence": 0.50,
        "state": "CONFIRMED",
    }
    out2 = vis.draw_frame(frame.copy(), [], hazards=[confirmed_hazard])
    diff2 = np.sum(np.abs(out2.astype(int) - frame.astype(int)))
    assert diff2 > 0, "CONFIRMED smoke at 50% MUST be drawn on HUD"


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: Audio alarm state gate — only CONFIRMED triggers alarm
# ─────────────────────────────────────────────────────────────────────────────
def test_audio_alarm_state_gate():
    """
    AudioAlertEngine.evaluate_hazard() must NOT trigger alarm for CANDIDATE hazards.
    Only CONFIRMED/ACTIVE states should cause has_fire or has_smoke to be True.
    """
    try:
        from app.services.audio_alert_engine import AudioAlertEngine
        from app.ai.hazards.schemas import HazardType, HazardState
    except ImportError:
        from backend.app.services.audio_alert_engine import AudioAlertEngine
        try:
            from backend.app.ai.hazards.schemas import HazardType, HazardState
        except Exception:
            HazardType = None
            HazardState = None

    engine = AudioAlertEngine.get_instance()
    # Clear cooldown state (no reset() method — clear the timestamp dict directly)
    engine._last_alert_timestamps.clear()

    # CANDIDATE smoke — should NOT trigger alarm
    candidate = {
        "hazard_type": "smoke",
        "class_name": "smoke",
        "confidence": 0.25,
        "state": "CANDIDATE",
    }
    result = engine.evaluate_hazard(
        camera_id="test_alarm_gate_candidate",
        speaker_enabled=True,
        hazards=[candidate],
        force=True,
    )
    assert result is None, (
        f"CANDIDATE smoke must NOT trigger audio alarm. Got: {result}"
    )

    # CONFIRMED smoke — MUST trigger alarm
    confirmed = {
        "hazard_type": "smoke",
        "class_name": "smoke",
        "confidence": 0.45,
        "state": "CONFIRMED",
    }
    result2 = engine.evaluate_hazard(
        camera_id="test_alarm_gate_confirmed",
        speaker_enabled=True,
        hazards=[confirmed],
        force=True,
    )
    assert result2 is not None, "CONFIRMED smoke must trigger audio alarm"
    assert result2.priority == "CRITICAL" or result2.hazard_type == "smoke"


# ─────────────────────────────────────────────────────────────────────────────
# Test 9: Smoke torso exclusion — overlapping worker body at low conf rejected
# ─────────────────────────────────────────────────────────────────────────────
def test_smoke_torso_exclusion():
    """
    process_raw_hazards() must reject low-confidence smoke (<0.40) that heavily
    overlaps (>55%) a worker's torso bounding box.
    """
    try:
        from app.ai.hazards.hazard_engine import HazardAnalysisEngine
        from app.ai.hazards.schemas import HazardState
    except ImportError:
        from backend.app.ai.hazards.hazard_engine import HazardAnalysisEngine
        from backend.app.ai.hazards.schemas import HazardState

    engine = HazardAnalysisEngine()

    # Worker torso: 100,100 → 200,300
    worker_boxes = [np.array([100.0, 100.0, 200.0, 300.0])]

    # Smoke at 25% confidence, 80% overlapping the worker torso
    raw_hazards = [
        {
            "class_name": "smoke",
            "confidence": 0.25,
            "bbox": [110.0, 110.0, 190.0, 290.0],  # Fully inside worker box
        }
    ]

    resp = engine.process_raw_hazards(
        raw_hazards=raw_hazards,
        frame_shape=(480, 640),
        camera_id="test_cam",
        worker_boxes=worker_boxes,
    )

    # Smoke must be excluded from tracking (no active tracks)
    # CONFIRMED/ACTIVE hazards must be 0 (smoke may still be CANDIDATE if it somehow passed)
    confirmed_count = sum(
        1 for h in resp.hazards
        if str(getattr(getattr(h, "state", ""), "value", "")).upper() in ("CONFIRMED", "ACTIVE")
    )
    assert confirmed_count == 0, (
        f"Low-conf smoke overlapping worker torso must not become CONFIRMED. Got {confirmed_count} confirmed hazards."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 10: IP camera drain variable — detect_occlusion boundary checks
# ─────────────────────────────────────────────────────────────────────────────
def test_detect_occlusion_lateral_clipping():
    """
    Worker severely cut off at lateral frame boundary must be detected as occluded.
    """
    associator = SpatialPPEAssociator()
    img_shape = (480, 640)

    # Worker appears only at extreme right edge: x1=620, x2=640 → width=20px
    worker_box = np.array([620.0, 100.0, 640.0, 400.0])

    is_occ = associator.detect_occlusion(
        worker_idx=0,
        worker_boxes=[worker_box],
        item_type=PPEItemType.HELMET,
        img_shape=img_shape,
    )
    assert is_occ is True, "Worker cut off at lateral frame boundary must be occluded"
