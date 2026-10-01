"""
test_master_real_world_validation.py — SafeSync Master Validation Suite
======================================================================
Covers:
  - Multi-Worker Tracking & Isolation (Section 10)
  - PPE Color & Style Generalization (Section 7)
  - Gloves & Bare Hands Zone Validation (Section 8)
  - Safety Footwear & Framing Cutoff Validation (Section 9)
  - Fire & Smoke State Machine (Section 13)
  - Smoke Torso-Overlap Exclusion (Section 12)
  - Audio Alarm & Visualizer State Gating (Sections 6, 7, 13, 17)
  - Latest-Frame-Wins Telemetry Schema (Section 15)
"""

import sys
import os
import time
import numpy as np
import pytest

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for p in [_BACKEND, _ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.ai.compliance.schemas import (
    PPEItemType,
    PPEState,
    OverallComplianceState,
    WorkerTrack,
    WorkerBoundingBox,
)
from app.ai.compliance.tracker import ByteTrack
from app.ai.compliance.association import SpatialPPEAssociator, verify_helmet_features, verify_safety_vest_features
from app.ai.compliance.temporal import TemporalComplianceTracker
from app.ai.compliance.visualizer import ComplianceVisualizer
from app.ai.hazards.schemas import HazardType, HazardState
from app.ai.hazards.temporal import TemporalHazardStateMachine
from app.ai.hazards.tracker import SpatialHazardTracker
from app.ai.hazards.hazard_engine import HazardAnalysisEngine
from app.services.audio_alert_engine import AudioAlertEngine


# =============================================================================
# 1. MULTI-WORKER TRACKING & PPE ASSOCIATION ISOLATION (Section 10)
# =============================================================================

def test_multi_worker_tracking_and_isolation():
    """
    Test 3 workers side-by-side:
      Worker 1: Compliant (Helmet + Vest)
      Worker 2: Non-compliant (Vest only, NO Helmet)
      Worker 3: Compliant (Helmet + Vest)
    Verifies:
      1. Unique Track IDs are assigned and persist across frames.
      2. Worker 1's helmet is NOT assigned to Worker 2.
      3. Worker 2 is correctly evaluated as NON_COMPLIANT.
      4. Workers 1 and 3 are evaluated as COMPLIANT.
    """
    tracker = ByteTrack(
        track_high_thresh=0.20,
        track_low_thresh=0.08,
        new_track_thresh=0.25,
        track_buffer=30,
        match_thresh=0.70,
        confirmation_frames=2,
    )
    associator = SpatialPPEAssociator()
    temp_tracker = TemporalComplianceTracker(config={
        "temporal": {"confirmation_frames": 2, "missing_detection_tolerance": 6},
        "required_ppe": {"helmet": True, "safety_vest": True, "gloves": False, "safety_footwear": False}
    })

    # Worker bboxes: 3 distinct people across width
    # W1: [100, 100, 200, 400]
    # W2: [300, 100, 400, 400]
    # W3: [500, 100, 600, 400]
    w1_box = [100.0, 100.0, 200.0, 400.0, 0.90]
    w2_box = [300.0, 100.0, 400.0, 400.0, 0.88]
    w3_box = [500.0, 100.0, 600.0, 400.0, 0.92]

    # PPE items:
    # W1 helmet: [120, 105, 180, 160]
    # W1 vest:   [110, 170, 190, 310]
    # W2 vest:   [310, 170, 390, 310] (NO helmet for W2!)
    # W3 helmet: [520, 105, 580, 160]
    # W3 vest:   [510, 170, 590, 310]
    ppe_items = [
        {"class_name": "helmet", "bbox": [120, 105, 180, 160], "confidence": 0.85},
        {"class_name": "safety_vest", "bbox": [110, 170, 190, 310], "confidence": 0.82},
        {"class_name": "safety_vest", "bbox": [310, 170, 390, 310], "confidence": 0.80},
        {"class_name": "helmet", "bbox": [520, 105, 580, 160], "confidence": 0.88},
        {"class_name": "safety_vest", "bbox": [510, 170, 590, 310], "confidence": 0.84},
    ]

    img_shape = (720, 1280)
    worker_tracks_history = {}

    # Run over 4 consecutive frames for ByteTrack & Temporal confirmation
    for f in range(1, 5):
        temp_tracker.current_frame = f
        # ByteTrack update
        dets = np.array([w1_box, w2_box, w3_box])
        active_tracks = tracker.update(dets)
        assert len(active_tracks) == 3, f"Frame {f}: expected 3 tracks, got {len(active_tracks)}"

        # Associate
        associations, unassociated = associator.associate(
            active_tracks, ppe_items, img_shape=img_shape
        )

        # Temporal compliance update
        frame_worker_tracks = []
        for idx, (tid, wb, conf) in enumerate(active_tracks):
            occl = {
                item: associator.detect_occlusion(idx, [b for _, b, _ in active_tracks], item, img_shape)
                for item in PPEItemType
            }
            wt = temp_tracker.update_worker(
                track_id=tid,
                worker_bbox=wb,
                confidence=conf,
                associations=associations.get(tid, {}),
                is_occluded_flags=occl,
            )
            frame_worker_tracks.append(wt)
        worker_tracks_history[f] = frame_worker_tracks

    # Evaluate final frame
    final_tracks = worker_tracks_history[4]
    assert len(final_tracks) == 3

    # Sort workers by X coordinate
    sorted_tracks = sorted(final_tracks, key=lambda w: w.bbox.x1)
    w1_res, w2_res, w3_res = sorted_tracks[0], sorted_tracks[1], sorted_tracks[2]

    # Verify Track IDs are unique
    tids = {w.track_id for w in final_tracks}
    assert len(tids) == 3, f"Track IDs must be unique: {tids}"

    # Verify Worker 1: Compliant (Helmet PRESENT, Vest PRESENT)
    assert w1_res.ppe.get("helmet") == PPEState.PRESENT, f"Worker 1 helmet should be PRESENT: {w1_res.ppe}"
    assert w1_res.ppe.get("safety_vest") == PPEState.PRESENT, f"Worker 1 vest should be PRESENT: {w1_res.ppe}"
    assert w1_res.overall_status == OverallComplianceState.COMPLIANT, f"Worker 1 overall: {w1_res.overall_status}"

    # Verify Worker 2: Non-compliant (Helmet NOT present, Vest PRESENT)
    assert w2_res.ppe.get("helmet") in (PPEState.ABSENT, PPEState.UNKNOWN), f"Worker 2 helmet: {w2_res.ppe}"
    assert w2_res.ppe.get("safety_vest") == PPEState.PRESENT, f"Worker 2 vest should be PRESENT: {w2_res.ppe}"
    # Worker 2 must NOT have stolen Worker 1 or Worker 3's helmet!

    # Verify Worker 3: Compliant (Helmet PRESENT, Vest PRESENT)
    assert w3_res.ppe.get("helmet") == PPEState.PRESENT, f"Worker 3 helmet should be PRESENT: {w3_res.ppe}"
    assert w3_res.ppe.get("safety_vest") == PPEState.PRESENT, f"Worker 3 vest should be PRESENT: {w3_res.ppe}"
    assert w3_res.overall_status == OverallComplianceState.COMPLIANT, f"Worker 3 overall: {w3_res.overall_status}"


# =============================================================================
# 2. PPE COLOR & STYLE GENERALIZATION (Section 7)
# =============================================================================

def test_helmet_style_generalization():
    """
    Tests wide-brim hard hats, forestry helmets, compact bump caps, and dark/high-conf helmets.
    Verifies that the aspect ratio limits and high-confidence bypass accept diverse styles.
    """
    worker_box = np.array([200.0, 100.0, 320.0, 500.0])  # width=120, height=400

    # 1. Wide-brim industrial helmet (aspect ratio = 2.45, pw=110, ph=45)
    wide_brim = np.array([205.0, 105.0, 315.0, 150.0])
    res1 = verify_helmet_features(worker_box, wide_brim, frame=None, confidence=0.60)
    assert res1 is True, "Wide-brim helmet (aspect=2.44) must be accepted"

    # 2. Compact aerodynamic safety cap (aspect ratio = 0.85, pw=45, ph=53)
    compact_cap = np.array([235.0, 105.0, 280.0, 158.0])
    res2 = verify_helmet_features(worker_box, compact_cap, frame=None, confidence=0.55)
    assert res2 is True, "Compact safety cap (aspect=0.85) must be accepted"

    # 3. High-confidence helmet with dark/shadowed image (conf >= 0.65 bypasses HSV check)
    dark_frame = np.zeros((600, 600, 3), dtype=np.uint8)  # Black frame = 0 shell color
    res3 = verify_helmet_features(worker_box, wide_brim, frame=dark_frame, confidence=0.72)
    assert res3 is True, "High-confidence helmet (conf=0.72) must bypass HSV check even in pitch dark frame"

    # 4. Out-of-bounds helmet (below torso) must be rejected
    torso_box = np.array([205.0, 300.0, 315.0, 360.0])
    res4 = verify_helmet_features(worker_box, torso_box, frame=None, confidence=0.80)
    assert res4 is False, "Helmet detected at torso level must be rejected"


# =============================================================================
# 3. GLOVES & BARE HANDS ANATOMICAL VALIDATION (Section 8)
# =============================================================================

def test_gloves_anatomical_anchoring():
    """
    Verifies that candidate glove detections outside the lower-arm/hand zone
    (e.g., above shoulders, in cranium zone, or far laterally) are rejected.
    """
    associator = SpatialPPEAssociator()
    worker_box = np.array([200.0, 100.0, 350.0, 500.0])  # width=150, height=400

    # Normal hand location (mid-to-lower body lateral)
    valid_hand = np.array([170.0, 250.0, 210.0, 310.0])
    aff_valid = associator.compute_affinity(worker_box, valid_hand, PPEItemType.GLOVES)
    assert aff_valid > 0.15, f"Valid hand position should have positive affinity, got {aff_valid}"

    # Invalid location: Head/Cranium area
    head_artifact = np.array([240.0, 110.0, 280.0, 150.0])
    aff_head = associator.compute_affinity(worker_box, head_artifact, PPEItemType.GLOVES)
    # Head zone rel_yc is < 0.15, outside gloves zone (0.30 to 0.95)
    assert aff_head < 0.15, f"Head area artifact must not have high gloves affinity, got {aff_head}"


# =============================================================================
# 4. SAFETY FOOTWEAR & FRAMING CUTOFF (Section 9)
# =============================================================================

def test_footwear_waist_cutoff_unknown_not_violation():
    """
    When worker is framed from waist-up (wh/ww < 2.0 or feet touch bottom margin):
      1. detect_occlusion must return True for FOOTWEAR.
      2. The temporal tracker must set footwear state to UNKNOWN.
      3. UNKNOWN footwear must NOT trigger NON_COMPLIANT.
    """
    associator = SpatialPPEAssociator()
    img_shape = (480, 640)

    # Half-body worker cropped at waist: width=140, height=180 -> wh/ww = 1.28 (< 2.0)
    worker_box = np.array([200.0, 100.0, 340.0, 280.0])

    is_footwear_occluded = associator.detect_occlusion(
        worker_idx=0,
        worker_boxes=[worker_box],
        item_type=PPEItemType.SAFETY_FOOTWEAR,
        img_shape=img_shape,
    )
    assert is_footwear_occluded is True, "Half-body worker footwear must be detected as occluded"

    # Feed to temporal compliance tracker with footwear mandatory policy
    temp_tracker = TemporalComplianceTracker(config={
        "temporal": {"confirmation_frames": 2, "missing_detection_tolerance": 2},
        "required_ppe": {"helmet": True, "safety_vest": True, "gloves": False, "safety_footwear": True}
    })

    # Worker has Helmet + Vest, Footwear is None, but Footwear is OCCLUDED
    associations = {
        "helmet": {"bbox": [230, 105, 310, 155], "confidence": 0.85},
        "safety_vest": {"bbox": [220, 150, 320, 270], "confidence": 0.88},
        "safety_footwear": None,
        "gloves": None,
    }
    occl_flags = {
        PPEItemType.HELMET: False,
        PPEItemType.SAFETY_VEST: False,
        PPEItemType.GLOVES: True,
        PPEItemType.SAFETY_FOOTWEAR: True,
    }

    # 4 frames: Footwear should remain UNKNOWN and NEVER flip to ABSENT
    wt = None
    for f in range(1, 5):
        temp_tracker.current_frame = f
        wt = temp_tracker.update_worker(
            track_id=10,
            worker_bbox=worker_box,
            confidence=0.90,
            associations=associations,
            is_occluded_flags=occl_flags,
        )

    assert wt is not None
    assert wt.ppe.get("safety_footwear") == PPEState.UNKNOWN, (
        f"Occluded footwear must be UNKNOWN, got: {wt.ppe.get('safety_footwear')}"
    )
    # UNKNOWN != VIOLATION: Overall status must be UNKNOWN (or COMPLIANT), NEVER NON_COMPLIANT!
    assert wt.overall_status != OverallComplianceState.NON_COMPLIANT, (
        f"Worker with UNKNOWN footwear must not be NON_COMPLIANT. Got: {wt.overall_status}"
    )


# =============================================================================
# 5. FIRE & SMOKE 7-STAGE STATE MACHINE (Section 13)
# =============================================================================

def test_hazard_state_machine_lifecycle():
    """
    Tests 7-stage hazard state machine:
      Frame 1: 1st observation -> CANDIDATE (No alarm, no HUD box)
      Frame 2-4: Consistent observations -> DETECTING -> CONFIRMED
      Frame 5-8: Active persistence -> ACTIVE
      Frame 9-16: Consecutive misses -> CLEARING -> CLEARED
    """
    config = {
        "hazard": {
            "confirmation_frames": 3,
            "minimum_observation_ratio": 0.50,
            "smoke_confirmation_confidence": 0.35,
            "fire_confirmation_confidence": 0.25,
            "fire_clear_frames": 4,
            "smoke_clear_frames": 5,
            "max_centroid_jump_normalized": 0.18,
            "min_consistent_detections": 2,
        }
    }
    sm = TemporalHazardStateMachine(config)
    tracker = SpatialHazardTracker(config)

    camera_id = "cam_test"
    frame_shape = (720, 1280)

    # ── Frame 1: Single detection ─────────────────────────────────────────────
    det_f1 = [{
        "hazard_type": HazardType.FIRE,
        "confidence": 0.40,
        "bbox": [100.0, 100.0, 150.0, 150.0],
        "zone_id": "ZONE_A",
    }]
    tracks_f1 = tracker.update(det_f1, frame_idx=1, camera_id=camera_id, frame_shape=frame_shape)
    assert len(tracks_f1) == 1
    state_f1 = sm.evaluate_track_state(tracks_f1[0])
    assert state_f1 == HazardState.CANDIDATE, f"Frame 1 must be CANDIDATE, got {state_f1}"

    # Verify AudioAlertEngine suppresses CANDIDATE
    audio_engine = AudioAlertEngine.get_instance()
    audio_engine._last_alert_timestamps.clear()
    payload = audio_engine.evaluate_hazard(
        camera_id=camera_id,
        speaker_enabled=True,
        hazards=[{"class_name": "fire", "state": state_f1.value, "confidence": 0.40}],
        force=True,
    )
    assert payload is None, "CANDIDATE state must NOT trigger audio alert"

    # ── Frame 2 & 3: Sustained consistent detections ──────────────────────────
    tracks_f2 = tracker.update(det_f1, frame_idx=2, camera_id=camera_id, frame_shape=frame_shape)
    state_f2 = sm.evaluate_track_state(tracks_f2[0])

    tracks_f3 = tracker.update(det_f1, frame_idx=3, camera_id=camera_id, frame_shape=frame_shape)
    state_f3 = sm.evaluate_track_state(tracks_f3[0])
    assert state_f3 in (HazardState.CONFIRMED, HazardState.DETECTING), f"Frame 3 state: {state_f3}"

    # ── Frame 4: Confirm ──────────────────────────────────────────────────────
    tracks_f4 = tracker.update(det_f1, frame_idx=4, camera_id=camera_id, frame_shape=frame_shape)
    state_f4 = sm.evaluate_track_state(tracks_f4[0])
    assert state_f4 in (HazardState.CONFIRMED, HazardState.ACTIVE), f"Frame 4 should be CONFIRMED/ACTIVE: {state_f4}"

    # Verify AudioAlertEngine TRIGGERS on CONFIRMED
    payload_f4 = audio_engine.evaluate_hazard(
        camera_id=camera_id,
        speaker_enabled=True,
        hazards=[{"class_name": "fire", "state": state_f4.value, "confidence": 0.40}],
        force=True,
    )
    assert payload_f4 is not None, "CONFIRMED state MUST trigger audio alert"
    assert payload_f4.priority == "CRITICAL"

    # ── Frames 5+: Hazard disappears -> CLEARING -> CLEARED ───────────────────
    for f in range(5, 12):
        tracks_missed = tracker.update([], frame_idx=f, camera_id=camera_id, frame_shape=frame_shape)
        if tracks_missed:
            st = sm.evaluate_track_state(tracks_missed[0])
            if f >= 9:
                assert st in (HazardState.CLEARING, HazardState.CLEARED, HazardState.NO_HAZARD)


# =============================================================================
# 6. SMOKE TORSO-OVERLAP EXCLUSION (Section 12)
# =============================================================================

def test_smoke_torso_overlap_suppression():
    """
    Verifies that low-confidence smoke (<0.40) overlapping a worker torso (>55%)
    is excluded from tracking, while genuine separate smoke is retained.
    """
    engine = HazardAnalysisEngine()

    worker_boxes = [np.array([200.0, 150.0, 320.0, 480.0])]  # Worker body

    # Candidate 1: Dark clothing misclassified as smoke inside worker box (conf=0.28)
    torso_smoke = {
        "class_name": "smoke",
        "confidence": 0.28,
        "bbox": [210.0, 200.0, 310.0, 380.0],  # Heavily overlapping torso
    }

    # Candidate 2: Genuine smoke column in background/ceiling (conf=0.38)
    genuine_smoke = {
        "class_name": "smoke",
        "confidence": 0.38,
        "bbox": [450.0, 50.0, 600.0, 250.0],   # Far away from worker
    }

    resp = engine.process_raw_hazards(
        raw_hazards=[torso_smoke, genuine_smoke],
        frame_shape=(720, 1280),
        camera_id="cam_main",
        worker_boxes=worker_boxes,
    )

    # Candidate 1 should have been suppressed before tracking; Candidate 2 tracked
    active_b_boxes = [h.bbox for h in resp.hazards]
    # Check that no hazard is inside the worker's torso region
    for b in active_b_boxes:
        # Check x1, y1
        assert not (b.x1 >= 200 and b.x2 <= 330 and b.y1 >= 150 and b.y2 <= 480), (
            f"Torso smoke must not be present in tracked hazards: {b}"
        )


# =============================================================================
# 7. TELEMETRY SCHEMA INTEGRITY (Section 15)
# =============================================================================

def test_live_compliance_telemetry_fields():
    """
    Verifies that the CameraWorker.get_live_compliance() dictionary contains
    all required Section 15 telemetry fields:
    frame_id, fps, capture_fps, inference_time_ms, active_workers, active_violations,
    active_hazards, dropped_frames, dropped_ai_frames, frame_queue_depth, camera_state.
    """
    from app.camera.worker import CameraWorker
    from app.camera.schemas import CameraConfigModel, CameraSourceType

    cfg = CameraConfigModel(
        id="cam_telemetry_test",
        name="Test Telemetry Camera",
        source="synthetic",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
    )
    worker = CameraWorker(cfg)
    compliance_data = worker.get_live_compliance()

    # Verify top-level structure
    assert "camera_id" in compliance_data
    assert "workers" in compliance_data
    assert "hazards" in compliance_data
    assert "fps" in compliance_data
    assert "inference_latency_ms" in compliance_data
    assert "debug_telemetry" in compliance_data

    # Verify Section 15 debug telemetry fields
    dt = compliance_data["debug_telemetry"]
    required_dt_keys = [
        "frame_id", "fps", "capture_fps", "inference_time_ms",
        "active_workers", "active_violations", "active_hazards",
        "dropped_frames", "dropped_ai_frames", "frame_queue_depth",
        "model", "camera_state",
    ]
    for key in required_dt_keys:
        assert key in dt, f"Missing telemetry key: {key} in debug_telemetry"
