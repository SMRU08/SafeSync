"""
test_worker_box_colors.py — SafeSync worker bounding-box safety color (visualization only).

Verifies that the COMPLETE person bounding box color is derived from the FINAL,
temporally-validated worker compliance state:

    confirmed ABSENT  -> RED    (#EF4444)
    any UNKNOWN       -> AMBER  (#F59E0B)
    all PRESENT       -> GREEN  (#22C55E)

and that UNKNOWN never becomes RED, temporary detector loss (< 15 frames) never
creates RED, and alerts fire only for confirmed absence.

The temporal tracker is driven with the real production configs/compliance.yaml so
the 15-frame missing-detection tolerance is exercised exactly as deployed.
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

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPLIANCE_YAML = REPO_ROOT / "configs" / "compliance.yaml"

ALL_ITEMS = ["helmet", "safety_vest", "gloves", "safety_footwear"]
NO_OCCLUSION = {item: False for item in PPEItemType}


def _bgr(hex_color: str):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (b, g, r)


@pytest.fixture(scope="module")
def prod_config():
    with open(COMPLIANCE_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def tracker(prod_config):
    return TemporalComplianceTracker(prod_config)


@pytest.fixture
def tracker_4pt(prod_config):
    """Tracker where all 4 PPE items (helmet, vest, gloves, footwear) are required."""
    cfg = {
        "temporal": dict(prod_config.get("temporal", {})),
        "required_ppe": {item: True for item in ALL_ITEMS},
    }
    return TemporalComplianceTracker(cfg)


@pytest.fixture(autouse=True)
def _fresh_audio_engine():
    AudioAlertEngine.reset_instance()
    yield
    AudioAlertEngine.reset_instance()


def _assoc(present_items):
    return {
        item: ({"bbox": [10, 10, 20, 20], "confidence": 0.9} if item in present_items else None)
        for item in ALL_ITEMS
    }


def _step(tracker, track_id, present_items, occluded=None, bbox=(100, 100, 200, 400)):
    tracker.current_frame += 1
    flags = dict(NO_OCCLUSION)
    for item in occluded or []:
        flags[PPEItemType(item)] = True
    return tracker.update_worker(
        track_id=track_id,
        worker_bbox=np.array(bbox, dtype=float),
        confidence=0.9,
        associations=_assoc(present_items),
        is_occluded_flags=flags,
    )


def _make_worker(track_id, ppe, status, bbox=(100, 100, 200, 400)):
    return WorkerTrack(
        track_id=track_id,
        bbox=WorkerBoundingBox(x1=bbox[0], y1=bbox[1], x2=bbox[2], y2=bbox[3]),
        confidence=0.9,
        ppe={k: PPEState(v) for k, v in ppe.items()},
        overall_status=status,
    )


def _box_edge_color(img, worker):
    """Samples a pixel on the left edge of the person box, mid-height (away from the HUD card)."""
    b = worker.bbox
    return tuple(int(c) for c in img[(b.y1 + b.y2) // 2, b.x1])


def _alert(worker, engine=None):
    engine = engine or AudioAlertEngine.get_instance()
    return engine.evaluate_worker(
        camera_id="cam_test",
        speaker_enabled=True,
        worker_id=worker.track_id,
        ppe_status=worker.ppe_status,
        lang="en",
    )


# ──────────────────────────── Regression guards ────────────────────────────

def test_spec_colors_and_production_tolerance(prod_config):
    assert COLOR_COMPLIANT == _bgr("#22C55E")
    assert COLOR_UNKNOWN == _bgr("#F59E0B")
    assert COLOR_NON_COMPLIANT == _bgr("#EF4444")
    # 15-frame tolerance must remain unchanged
    assert prod_config["temporal"]["missing_detection_tolerance"] == 15
    assert prod_config["required_ppe"]["helmet"] is True
    assert prod_config["required_ppe"]["safety_vest"] is True


# ──────────────────────────── TEST 1 ────────────────────────────

def test_1_all_ppe_present_is_green_no_violation_no_alert(tracker_4pt):
    w = None
    for _ in range(5):
        w = _step(tracker_4pt, 1, ALL_ITEMS)
    assert all(w.ppe[k] == PPEState.PRESENT for k in ALL_ITEMS)
    assert w.overall_status == OverallComplianceState.COMPLIANT

    d = resolve_worker_display(w)
    assert d["display_state"] == DISPLAY_SAFE
    assert d["color"] == COLOR_COMPLIANT
    assert d["label"] == "SAFE"
    assert d["missing_items"] == []

    img = ComplianceVisualizer(show_hud=True).draw_frame(np.zeros((600, 800, 3), np.uint8), [w])
    assert _box_edge_color(img, w) == COLOR_COMPLIANT

    assert _alert(w).action == "COMPLIANT"


# ──────────────────────────── TEST 2 ────────────────────────────

def test_2_footwear_unknown_is_amber_no_violation_no_alert():
    w = _make_worker(
        2,
        {"helmet": "PRESENT", "safety_vest": "PRESENT", "gloves": "PRESENT", "safety_footwear": "UNKNOWN"},
        OverallComplianceState.UNKNOWN,
    )
    d = resolve_worker_display(w)
    assert d["display_state"] == DISPLAY_UNKNOWN
    assert d["color"] == COLOR_UNKNOWN
    assert d["color"] != COLOR_NON_COMPLIANT
    assert d["missing_items"] == []
    assert d["unknown_items"] == ["Footwear"]
    assert d["detail"] == "Footwear visibility limited"

    img = ComplianceVisualizer().draw_frame(np.zeros((600, 800, 3), np.uint8), [w])
    assert _box_edge_color(img, w) == COLOR_UNKNOWN

    assert _alert(w).action == "COMPLIANT"  # no missing items -> no alert


# ──────────────────────────── TEST 3 ────────────────────────────

def test_3_helmet_temporarily_undetected_under_15_frames_never_red(tracker):
    for _ in range(5):
        _step(tracker, 3, ALL_ITEMS)

    others = ["safety_vest", "gloves", "safety_footwear"]
    for i in range(14):  # < 15 tolerance frames
        w = _step(tracker, 3, others)
        assert w.ppe["helmet"] != PPEState.ABSENT, f"frame {i + 1}"
        assert w.overall_status != OverallComplianceState.NON_COMPLIANT
        d = resolve_worker_display(w)
        assert d["color"] != COLOR_NON_COMPLIANT
        assert _alert(w).action == "COMPLIANT"


# ──────────────────────────── TEST 4 ────────────────────────────

def test_4_helmet_confirmed_absent_after_tolerance_is_red_alert_once(tracker):
    for _ in range(5):
        _step(tracker, 4, ALL_ITEMS)

    others = ["safety_vest", "gloves", "safety_footwear"]
    w = None
    for _ in range(15):  # reach the 15-frame tolerance
        w = _step(tracker, 4, others)

    assert w.ppe["helmet"] == PPEState.ABSENT
    assert w.overall_status == OverallComplianceState.NON_COMPLIANT

    d = resolve_worker_display(w)
    assert d["display_state"] == DISPLAY_VIOLATION
    assert d["color"] == COLOR_NON_COMPLIANT
    assert d["label"] == "CONFIRMED VIOLATION"
    assert d["missing_items"] == ["Helmet"]
    assert d["detail"] == "Missing: Helmet"

    img = ComplianceVisualizer().draw_frame(np.zeros((600, 800, 3), np.uint8), [w])
    assert _box_edge_color(img, w) == COLOR_NON_COMPLIANT

    # Existing alert mechanism: fires once, then deduplicated by the existing cooldown
    engine = AudioAlertEngine.get_instance()
    first = _alert(w, engine)
    assert first.action == "AUDIO_TRIGGERED"
    assert first.missing_ppe == ["helmet"]
    w2 = _step(tracker, 4, others)
    assert _alert(w2, engine).action == "COOLDOWN"


# ──────────────────────────── TEST 5 ────────────────────────────

def test_5_multiple_workers_independent_colors_no_contamination(tracker_4pt):
    bbox_a, bbox_b, bbox_c = (20, 100, 120, 450), (300, 100, 400, 450), (580, 100, 680, 450)
    a = b = c = None
    for _ in range(5):
        a = _step(tracker_4pt, 101, ALL_ITEMS, bbox=bbox_a)
        b = _step(tracker_4pt, 102, ["helmet", "safety_vest", "gloves"], occluded=["safety_footwear"], bbox=bbox_b)
        c = _step(tracker_4pt, 103, ALL_ITEMS, bbox=bbox_c)
    for _ in range(15):
        a = _step(tracker_4pt, 101, ALL_ITEMS, bbox=bbox_a)
        b = _step(tracker_4pt, 102, ["helmet", "safety_vest", "gloves"], occluded=["safety_footwear"], bbox=bbox_b)
        c = _step(tracker_4pt, 103, ["safety_vest", "gloves", "safety_footwear"], bbox=bbox_c)

    assert resolve_worker_display(a)["display_state"] == DISPLAY_SAFE
    assert resolve_worker_display(b)["display_state"] == DISPLAY_UNKNOWN
    assert resolve_worker_display(c)["display_state"] == DISPLAY_VIOLATION
    assert resolve_worker_display(c)["missing_items"] == ["Helmet"]

    img = ComplianceVisualizer().draw_frame(np.zeros((600, 800, 3), np.uint8), [a, b, c])
    assert _box_edge_color(img, a) == COLOR_COMPLIANT
    assert _box_edge_color(img, b) == COLOR_UNKNOWN
    assert _box_edge_color(img, c) == COLOR_NON_COMPLIANT

    # Worker C's violation must not leak into A or B
    assert a.overall_status == OverallComplianceState.COMPLIANT
    assert b.ppe["helmet"] == PPEState.PRESENT
    assert b.overall_status == OverallComplianceState.UNKNOWN


# ──────────────────────────── TEST 6 ────────────────────────────

def test_6_waist_up_worker_footwear_out_of_frame_is_unknown_never_red(tracker_4pt):
    upper = ["helmet", "safety_vest", "gloves"]
    w = None
    for _ in range(40):  # well beyond the 15-frame tolerance
        w = _step(tracker_4pt, 6, upper, occluded=["safety_footwear"])
        assert w.ppe["safety_footwear"] == PPEState.UNKNOWN
        assert w.overall_status != OverallComplianceState.NON_COMPLIANT

    assert w.overall_status == OverallComplianceState.UNKNOWN
    d = resolve_worker_display(w)
    assert d["display_state"] == DISPLAY_UNKNOWN
    assert d["color"] == COLOR_UNKNOWN
    assert d["missing_items"] == []
    assert _alert(w).action == "COMPLIANT"


# ──────────────────────────── TEST 7 ────────────────────────────

def test_7_small_distant_gloves_not_visible_is_unknown_no_false_violation(tracker_4pt):
    visible = ["helmet", "safety_vest", "safety_footwear"]
    w = None
    for _ in range(40):
        w = _step(tracker_4pt, 7, visible, occluded=["gloves"])
        assert w.ppe["gloves"] == PPEState.UNKNOWN
        assert w.overall_status != OverallComplianceState.NON_COMPLIANT

    assert w.overall_status == OverallComplianceState.UNKNOWN
    d = resolve_worker_display(w)
    assert d["display_state"] == DISPLAY_UNKNOWN
    assert d["unknown_items"] == ["Gloves"]
    assert d["missing_items"] == []
    assert _alert(w).action == "COMPLIANT"


# ──────────────────────────── Priority table ────────────────────────────

@pytest.mark.parametrize(
    "ppe, status, expected",
    [
        ({k: "PRESENT" for k in ALL_ITEMS}, OverallComplianceState.COMPLIANT, DISPLAY_SAFE),
        ({**{k: "PRESENT" for k in ALL_ITEMS}, "safety_footwear": "UNKNOWN"}, OverallComplianceState.UNKNOWN, DISPLAY_UNKNOWN),
        ({**{k: "PRESENT" for k in ALL_ITEMS}, "safety_footwear": "ABSENT"}, OverallComplianceState.NON_COMPLIANT, DISPLAY_VIOLATION),
        ({"helmet": "ABSENT", "safety_vest": "UNKNOWN", "gloves": "PRESENT", "safety_footwear": "UNKNOWN"}, OverallComplianceState.NON_COMPLIANT, DISPLAY_VIOLATION),
        ({k: "UNKNOWN" for k in ALL_ITEMS}, OverallComplianceState.UNKNOWN, DISPLAY_UNKNOWN),
    ],
)
def test_state_priority(ppe, status, expected):
    d = resolve_worker_display(_make_worker(9, ppe, status))
    assert d["display_state"] == expected
    if expected != DISPLAY_VIOLATION:
        assert d["color"] != COLOR_NON_COMPLIANT
        assert d["missing_items"] == []
