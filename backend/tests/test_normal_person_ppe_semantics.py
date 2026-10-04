"""
test_normal_person_ppe_semantics.py — SafeSync Normal Person PPE Observability & Semantics

Regression test suite verifying correct PPE semantics for normal persons wearing ordinary clothes:
  - Clearly visible body region + required PPE not detected = ABSENT (after 15-frame tolerance)
  - Full-body normal person without PPE -> NON_COMPLIANT / RED bounding box
  - Insufficient visual evidence (waist-up, feet outside frame, occluded torso, distant worker) = UNKNOWN
  - UNKNOWN != ABSENT != VIOLATION (never triggers alarm or false violation)
  - Fully equipped worker -> PRESENT -> COMPLIANT / GREEN bounding box
  - Multi-worker scenes preserve strict 1-to-1 isolation
  - Fire/Smoke detection remains 100% untouched and functional
"""

from pathlib import Path
import numpy as np
import pytest
import yaml

from app.ai.compliance.schemas import (
    OverallComplianceState,
    PPEItemType,
    PPEState,
    WorkerBoundingBox,
    WorkerTrack,
)
from app.ai.compliance.association import SpatialPPEAssociator
from app.ai.compliance.temporal import TemporalComplianceTracker
from app.ai.compliance.visualizer import (
    COLOR_COMPLIANT,
    COLOR_NON_COMPLIANT,
    COLOR_UNKNOWN,
    DISPLAY_SAFE,
    DISPLAY_UNKNOWN,
    DISPLAY_VIOLATION,
    ComplianceVisualizer,
    resolve_worker_display,
)
from app.services.audio_alert_engine import AudioAlertEngine
from app.ai.hazards.hazard_engine import HazardAnalysisEngine
from app.ai.detection.detector import Detector

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPLIANCE_YAML = REPO_ROOT / "configs" / "compliance.yaml"
DETECTION_YAML = REPO_ROOT / "configs" / "detection.yaml"

ALL_ITEMS = [item.value for item in PPEItemType]


@pytest.fixture(scope="module")
def prod_compliance_config():
    with open(COMPLIANCE_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prod_detection_config():
    with open(DETECTION_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def associator():
    return SpatialPPEAssociator()


@pytest.fixture
def tracker_4pt(prod_compliance_config):
    """Tracker with full 4-point PPE mandatory configuration."""
    cfg = {
        "temporal": dict(prod_compliance_config.get("temporal", {})),
        "required_ppe": {item: True for item in ALL_ITEMS},
    }
    return TemporalComplianceTracker(cfg)


@pytest.fixture(autouse=True)
def _reset_audio_engine():
    AudioAlertEngine.reset_instance()
    yield
    AudioAlertEngine.reset_instance()


def _make_associations(present_dict):
    """present_dict: item_name -> bbox or None"""
    return {
        item: (
            {"bbox": present_dict[item], "confidence": 0.88, "class_name": item}
            if item in present_dict and present_dict[item] is not None
            else None
        )
        for item in ALL_ITEMS
    }


def _run_temporal_sequence(tracker, associator, track_id, worker_box, present_dict, num_frames, img_shape=(720, 1280), other_boxes=None):
    all_boxes = [worker_box] + (other_boxes or [])
    worker_idx = 0
    w = None
    for _ in range(num_frames):
        tracker.current_frame += 1
        occl_flags = {
            item: associator.detect_occlusion(worker_idx, all_boxes, item, img_shape)
            for item in PPEItemType
        }
        assoc = _make_associations(present_dict)
        w = tracker.update_worker(
            track_id=track_id,
            worker_bbox=worker_box,
            confidence=0.92,
            associations=assoc,
            is_occluded_flags=occl_flags,
        )
    return w


# =============================================================================
# 1. Full-body normal person without helmet -> Helmet ABSENT
# =============================================================================
def test_1_full_body_normal_person_without_helmet_is_absent(tracker_4pt, associator):
    """A clearly visible standing person without a helmet must have helmet marked ABSENT after 15 frames."""
    img_shape = (720, 1280)
    worker_box = np.array([300.0, 100.0, 480.0, 650.0])  # Full body, standing adult
    assert not associator.detect_occlusion(0, [worker_box], PPEItemType.HELMET, img_shape)

    present = {
        "safety_vest": [320, 180, 460, 400],
        "gloves": [280, 320, 320, 380],
        "safety_footwear": [330, 580, 450, 650],
    }

    # Within 14 frames, candidate absent remains under temporal validation
    w_early = _run_temporal_sequence(tracker_4pt, associator, 1, worker_box, present, 14, img_shape)
    assert w_early.ppe["helmet"] != PPEState.ABSENT

    # At frame 15, confirmed ABSENT
    w_final = _run_temporal_sequence(tracker_4pt, associator, 1, worker_box, present, 1, img_shape)
    assert w_final.ppe["helmet"] == PPEState.ABSENT
    assert w_final.overall_status == OverallComplianceState.NON_COMPLIANT
    display = resolve_worker_display(w_final)
    assert display["color"] == COLOR_NON_COMPLIANT
    assert "Helmet" in display["missing_items"]


# =============================================================================
# 2. Full-body normal person without vest -> Vest ABSENT
# =============================================================================
def test_2_full_body_normal_person_without_vest_is_absent(tracker_4pt, associator):
    """A clearly visible standing person without a vest must have vest marked ABSENT after 15 frames."""
    img_shape = (720, 1280)
    worker_box = np.array([300.0, 100.0, 480.0, 650.0])
    assert not associator.detect_occlusion(0, [worker_box], PPEItemType.SAFETY_VEST, img_shape)

    present = {
        "helmet": [340, 90, 440, 160],
        "gloves": [280, 320, 320, 380],
        "safety_footwear": [330, 580, 450, 650],
    }

    w_final = _run_temporal_sequence(tracker_4pt, associator, 2, worker_box, present, 15, img_shape)
    assert w_final.ppe["safety_vest"] == PPEState.ABSENT
    assert w_final.overall_status == OverallComplianceState.NON_COMPLIANT
    display = resolve_worker_display(w_final)
    assert display["color"] == COLOR_NON_COMPLIANT
    assert "Vest" in display["missing_items"]


# =============================================================================
# 3. Full-body normal person without gloves -> Gloves ABSENT
# =============================================================================
def test_3_full_body_normal_person_without_gloves_is_absent(tracker_4pt, associator):
    """A clearly visible standing person without gloves must have gloves marked ABSENT after 15 frames."""
    img_shape = (720, 1280)
    worker_box = np.array([300.0, 100.0, 480.0, 650.0])
    assert not associator.detect_occlusion(0, [worker_box], PPEItemType.GLOVES, img_shape)

    present = {
        "helmet": [340, 90, 440, 160],
        "safety_vest": [320, 180, 460, 400],
        "safety_footwear": [330, 580, 450, 650],
    }

    w_final = _run_temporal_sequence(tracker_4pt, associator, 3, worker_box, present, 15, img_shape)
    assert w_final.ppe["gloves"] == PPEState.ABSENT
    assert w_final.overall_status == OverallComplianceState.NON_COMPLIANT
    display = resolve_worker_display(w_final)
    assert display["color"] == COLOR_NON_COMPLIANT
    assert "Gloves" in display["missing_items"]


# =============================================================================
# 4. Full-body normal person without safety footwear -> Footwear ABSENT
# =============================================================================
def test_4_full_body_normal_person_without_footwear_is_absent(tracker_4pt, associator):
    """A clearly visible standing person without safety footwear must have footwear marked ABSENT after 15 frames."""
    img_shape = (720, 1280)
    worker_box = np.array([300.0, 100.0, 480.0, 650.0])
    assert not associator.detect_occlusion(0, [worker_box], PPEItemType.SAFETY_FOOTWEAR, img_shape)

    present = {
        "helmet": [340, 90, 440, 160],
        "safety_vest": [320, 180, 460, 400],
        "gloves": [280, 320, 320, 380],
    }

    w_final = _run_temporal_sequence(tracker_4pt, associator, 4, worker_box, present, 15, img_shape)
    assert w_final.ppe["safety_footwear"] == PPEState.ABSENT
    assert w_final.overall_status == OverallComplianceState.NON_COMPLIANT
    display = resolve_worker_display(w_final)
    assert display["color"] == COLOR_NON_COMPLIANT
    assert "Footwear" in display["missing_items"]


# =============================================================================
# 5. Full-body normal person without ANY required PPE -> All ABSENT -> NON_COMPLIANT
# =============================================================================
def test_5_full_body_normal_person_all_ppe_absent_red_violation(tracker_4pt, associator):
    """
    Normal person enters wearing ordinary clothes (normal shirt, pants, shoes, no PPE).
    All observable body regions are visible.
    All 4 PPE items become ABSENT after 15 frames.
    Overall compliance becomes NON_COMPLIANT with RED bounding box.
    """
    img_shape = (720, 1280)
    worker_box = np.array([300.0, 100.0, 480.0, 650.0])
    # Verify all regions are sufficiently visible
    for item in PPEItemType:
        assert not associator.detect_occlusion(0, [worker_box], item, img_shape)
        assert associator.is_anatomical_region_visible(0, [worker_box], item, img_shape)

    # Empty detections for all PPE
    present_empty = {}

    # Frame 1 to 14: Candidates under validation, not yet confirmed absent
    w_mid = _run_temporal_sequence(tracker_4pt, associator, 5, worker_box, present_empty, 14, img_shape)
    assert w_mid.overall_status != OverallComplianceState.NON_COMPLIANT

    # Frame 15: Confirmed ABSENT for all items
    w_final = _run_temporal_sequence(tracker_4pt, associator, 5, worker_box, present_empty, 1, img_shape)
    for item in ALL_ITEMS:
        assert w_final.ppe[item] == PPEState.ABSENT, f"{item} should be confirmed ABSENT"

    assert w_final.overall_status == OverallComplianceState.NON_COMPLIANT

    display = resolve_worker_display(w_final)
    assert display["display_state"] == DISPLAY_VIOLATION
    assert display["color"] == COLOR_NON_COMPLIANT
    assert set(display["missing_items"]) == {"Helmet", "Vest", "Gloves", "Footwear"}

    # Bounding box visualizer must render RED
    vis = ComplianceVisualizer(show_hud=True)
    canvas = np.zeros((720, 1280, 3), dtype=np.uint8)
    drawn = vis.draw_frame(canvas, [w_final])
    left_edge_pixel = tuple(int(c) for c in drawn[(w_final.bbox.y1 + w_final.bbox.y2) // 2, w_final.bbox.x1])
    assert left_edge_pixel == COLOR_NON_COMPLIANT


# =============================================================================
# 6. Waist-up person -> Footwear UNKNOWN
# =============================================================================
def test_6_waist_up_person_footwear_unknown(tracker_4pt, associator):
    """Waist-up camera framing: lower body not visible. Footwear must evaluate to UNKNOWN, never ABSENT."""
    img_shape = (720, 1280)
    # Waist-up framing: wh/ww = 180 / 150 = 1.20 (< 1.65)
    worker_box = np.array([200.0, 100.0, 350.0, 280.0])
    assert associator.detect_occlusion(0, [worker_box], PPEItemType.SAFETY_FOOTWEAR, img_shape)

    present = {
        "helmet": [230, 95, 320, 145],
        "safety_vest": [220, 150, 330, 260],
    }

    # Run for 30 frames (well beyond 15-frame tolerance)
    w = _run_temporal_sequence(tracker_4pt, associator, 6, worker_box, present, 30, img_shape)
    assert w.ppe["safety_footwear"] == PPEState.UNKNOWN
    # Must NOT become ABSENT
    assert w.ppe["safety_footwear"] != PPEState.ABSENT
    display = resolve_worker_display(w)
    assert display["color"] != COLOR_NON_COMPLIANT


# =============================================================================
# 7. Feet outside frame -> Footwear UNKNOWN
# =============================================================================
def test_7_feet_outside_frame_footwear_unknown(tracker_4pt, associator):
    """Person visible from head to knees/shins (feet outside bottom of frame): Footwear must be UNKNOWN."""
    img_shape = (720, 1280)
    # wy2 = 720 hits bottom frame edge
    worker_box = np.array([200.0, 50.0, 360.0, 720.0])
    assert associator.detect_occlusion(0, [worker_box], PPEItemType.SAFETY_FOOTWEAR, img_shape)

    present = {
        "helmet": [230, 45, 330, 100],
        "safety_vest": [220, 120, 340, 350],
        "gloves": [190, 350, 230, 420],
    }

    w = _run_temporal_sequence(tracker_4pt, associator, 7, worker_box, present, 25, img_shape)
    assert w.ppe["safety_footwear"] == PPEState.UNKNOWN
    assert "safety_footwear" not in [k for k, v in w.ppe.items() if v == PPEState.ABSENT]


# =============================================================================
# 8. Occluded torso -> Vest UNKNOWN
# =============================================================================
def test_8_occluded_torso_vest_unknown(tracker_4pt, associator):
    """Worker standing behind another worker/machinery occluding torso: Vest must evaluate to UNKNOWN, not ABSENT."""
    img_shape = (720, 1280)
    worker_target = np.array([300.0, 100.0, 480.0, 650.0])
    # Overlapping worker directly in front of torso
    worker_in_front = np.array([290.0, 180.0, 490.0, 480.0])
    all_workers = [worker_target, worker_in_front]

    assert associator.detect_occlusion(0, all_workers, PPEItemType.SAFETY_VEST, img_shape)

    present = {
        "helmet": [340, 90, 440, 160],
        "safety_footwear": [330, 580, 450, 650],
    }

    w = _run_temporal_sequence(
        tracker_4pt, associator, 8, worker_target, present, 20, img_shape, other_boxes=[worker_in_front]
    )
    assert w.ppe["safety_vest"] == PPEState.UNKNOWN
    assert w.ppe["safety_vest"] != PPEState.ABSENT


# =============================================================================
# 9. Distant/small worker -> Appropriate PPE UNKNOWN
# =============================================================================
def test_9_distant_small_worker_ppe_unknown(tracker_4pt, associator):
    """Distant small worker below resolution threshold: small PPE (gloves, footwear) must be UNKNOWN."""
    img_shape = (720, 1280)
    # Small box: wh = 68 (< 120 for gloves, < 90 for footwear), ww = 24
    worker_box = np.array([500.0, 200.0, 524.0, 268.0])

    assert associator.detect_occlusion(0, [worker_box], PPEItemType.GLOVES, img_shape)
    assert associator.detect_occlusion(0, [worker_box], PPEItemType.SAFETY_FOOTWEAR, img_shape)

    w = _run_temporal_sequence(tracker_4pt, associator, 9, worker_box, {}, 20, img_shape)
    assert w.ppe["gloves"] == PPEState.UNKNOWN
    assert w.ppe["safety_footwear"] == PPEState.UNKNOWN


# =============================================================================
# 10. Fully equipped worker -> PRESENT for visible PPE -> COMPLIANT / GREEN
# =============================================================================
def test_10_fully_equipped_worker_compliant_green(tracker_4pt, associator):
    """Full-PPE worker with all required PPE detected: all PRESENT, overall COMPLIANT, GREEN box."""
    img_shape = (720, 1280)
    worker_box = np.array([300.0, 100.0, 480.0, 650.0])
    present_all = {
        "helmet": [340, 90, 440, 160],
        "safety_vest": [320, 180, 460, 400],
        "gloves": [280, 320, 320, 380],
        "safety_footwear": [330, 580, 450, 650],
    }

    w = _run_temporal_sequence(tracker_4pt, associator, 10, worker_box, present_all, 5, img_shape)
    for item in ALL_ITEMS:
        assert w.ppe[item] == PPEState.PRESENT

    assert w.overall_status == OverallComplianceState.COMPLIANT
    display = resolve_worker_display(w)
    assert display["display_state"] == DISPLAY_SAFE
    assert display["color"] == COLOR_COMPLIANT
    assert display["label"] == "SAFE"

    # Alert engine must confirm COMPLIANT (no alarm)
    engine = AudioAlertEngine.get_instance()
    alert_res = engine.evaluate_worker("cam1", True, 10, w.ppe_status)
    assert alert_res.action == "COMPLIANT"


# =============================================================================
# 11. Multi-worker scene -> No cross-worker PPE assignment
# =============================================================================
def test_11_multi_worker_no_cross_assignment(associator):
    """Multi-worker scene with 1 helmet and 1 vest: strict 1-to-1 matching, no stealing or duplicate PPE."""
    img_shape = (720, 1280)
    w1_box = np.array([100.0, 100.0, 200.0, 450.0])
    w2_box = np.array([350.0, 100.0, 450.0, 450.0])
    tracked = [(101, w1_box, 0.90), (102, w2_box, 0.90)]

    # Helmet near w1, vest near w2
    ppe_dets = [
        {"class_name": "helmet", "bbox": [120, 90, 180, 150], "confidence": 0.88},
        {"class_name": "safety_vest", "bbox": [360, 180, 440, 320], "confidence": 0.85},
    ]

    associations, unassociated = associator.associate(tracked, ppe_dets, img_shape=img_shape)

    # Worker 101 gets helmet, NOT vest
    assert associations[101]["helmet"] is not None
    assert associations[101]["safety_vest"] is None

    # Worker 102 gets vest, NOT helmet
    assert associations[102]["helmet"] is None
    assert associations[102]["safety_vest"] is not None

    assert len(unassociated) == 0


# =============================================================================
# 12. Fire/Smoke regression -> Unchanged
# =============================================================================
def test_12_fire_smoke_regression_unchanged(prod_detection_config):
    """Verifies that Fire/Smoke detection thresholds (0.20/0.20) and pipeline logic remain completely untouched."""
    fire_thresh = prod_detection_config["inference"]["class_confidence_thresholds"]["fire"]
    smoke_thresh = prod_detection_config["inference"]["class_confidence_thresholds"]["smoke"]
    assert fire_thresh == 0.20, f"Fire threshold must be 0.20, got {fire_thresh}"
    assert smoke_thresh == 0.20, f"Smoke threshold must be 0.20, got {smoke_thresh}"

    # Detector verification
    detector = Detector(model_type="ppe")
    assert detector is not None

    # Hazard engine verification
    hazard_engine = HazardAnalysisEngine()
    empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    resp, _, _ = hazard_engine.process_frame(empty_frame)
    assert len(resp.hazards) == 0
