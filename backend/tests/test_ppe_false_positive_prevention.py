"""
test_ppe_false_positive_prevention.py — RAKSHYA VISION
Verifies suppression of PPE false positives:
- Normal hair is NOT detected/confirmed as helmet.
- Normal casual shirts/dresses are NOT detected/confirmed as safety vest.
- Genuine helmets and safety vests are accurately detected and confirmed.
- Anatomical geometry constraints reject oversized/misplaced candidate boxes.
- Per-class confidence thresholds filter low-confidence noise while preserving person recall.
"""

import numpy as np
import cv2
import pytest

from app.ai.compliance.schemas import PPEItemType, PPEState, OverallComplianceState
from app.ai.compliance.association import (
    SpatialPPEAssociator,
    verify_helmet_features,
    verify_safety_vest_features,
)
from app.ai.compliance.compliance_engine import WorkerComplianceEngine
from app.ai.detection.detector import Detector


def create_mock_person_image(has_helmet: bool = False, has_vest: bool = False) -> np.ndarray:
    """
    Synthesizes a realistic 720x1280 frame of a standing worker (x1=500, y1=100, x2=780, y2=660).
    - If has_helmet is False: Head has natural dark hair (V < 50, S < 40).
    - If has_helmet is True: Head has a bright yellow industrial helmet (H=30, S=180, V=230).
    - If has_vest is False: Torso has an ordinary navy blue cotton shirt (BGR: 100, 30, 20).
    - If has_vest is True: Torso has a fluorescent lime hi-vis vest (H=35, S=190, V=240) + silver reflective strips.
    """
    frame = np.full((720, 1280, 3), (40, 40, 40), dtype=np.uint8)  # Background

    # Worker bounds: wx1=500, wy1=100, wx2=780, wy2=660 (wh=560, ww=280)
    # Head bounds: hx1=580, hy1=100, hx2=700, hy2=200 (hh=100, hw=120)
    # Torso bounds: tx1=520, ty1=210, tx2=760, ty2=450 (th=240, tw=240)
    # Legs bounds: lx1=550, ly1=450, lx2=730, ly2=660

    # Draw legs (dark trousers)
    cv2.rectangle(frame, (550, 450), (730, 660), (50, 40, 30), -1)

    if has_vest:
        # Fluorescent lime safety vest (BGR approximately: (30, 230, 210))
        cv2.rectangle(frame, (520, 210), (760, 450), (30, 230, 210), -1)
        # Silver retro-reflective horizontal tape bands (bright specular white)
        cv2.rectangle(frame, (520, 290), (760, 320), (235, 235, 235), -1)
        cv2.rectangle(frame, (520, 380), (760, 410), (235, 235, 235), -1)
    else:
        # Ordinary casual navy blue cotton shirt
        cv2.rectangle(frame, (520, 210), (760, 450), (110, 40, 20), -1)

    # Draw neck & face (skin tone)
    cv2.rectangle(frame, (600, 160), (680, 210), (140, 170, 210), -1)

    if has_helmet:
        # Bright yellow industrial safety helmet (BGR approximately: (20, 215, 245))
        cv2.ellipse(frame, (640, 150), (65, 50), 0, 0, 360, (20, 215, 245), -1)
        # Rigid helmet brim
        cv2.rectangle(frame, (570, 155), (710, 170), (15, 190, 220), -1)
    else:
        # Natural dark hair (no helmet)
        cv2.ellipse(frame, (640, 140), (55, 40), 0, 0, 360, (25, 25, 25), -1)

    return frame


def test_hair_false_positive_rejected_by_helmet_features():
    """Verify natural dark hair crop is rejected and not verified as helmet."""
    frame_no_ppe = create_mock_person_image(has_helmet=False, has_vest=False)
    worker_box = np.array([500.0, 100.0, 780.0, 660.0])  # [wx1, wy1, wx2, wy2]
    # Hair box detected by model (top of head)
    hair_box = np.array([585.0, 100.0, 695.0, 180.0])

    # Should be rejected because it is natural dark hair without helmet shell colors
    passes = verify_helmet_features(worker_box, hair_box, frame=frame_no_ppe, confidence=0.55)
    assert passes is False, "Natural dark hair must be rejected by verify_helmet_features"


def test_ordinary_shirt_false_positive_rejected_by_vest_features():
    """Verify ordinary navy shirt crop is rejected and not verified as safety vest."""
    frame_no_ppe = create_mock_person_image(has_helmet=False, has_vest=False)
    worker_box = np.array([500.0, 100.0, 780.0, 660.0])
    # Shirt box detected by model (torso)
    shirt_box = np.array([520.0, 210.0, 760.0, 450.0])

    # Should be rejected because casual navy shirt has 0% hi-vis fluorescent chroma and 0% retro-reflective tape
    passes = verify_safety_vest_features(worker_box, shirt_box, frame=frame_no_ppe, confidence=0.52)
    assert passes is False, "Casual navy shirt must be rejected by verify_safety_vest_features"


def test_genuine_helmet_and_vest_accepted():
    """Verify genuine industrial hard hat and hi-vis vest are accepted."""
    frame_ppe = create_mock_person_image(has_helmet=True, has_vest=True)
    worker_box = np.array([500.0, 100.0, 780.0, 660.0])
    helmet_box = np.array([575.0, 100.0, 705.0, 175.0])
    vest_box = np.array([520.0, 210.0, 760.0, 450.0])

    helmet_ok = verify_helmet_features(worker_box, helmet_box, frame=frame_ppe, confidence=0.60)
    assert helmet_ok is True, "Genuine yellow hard hat must pass verification"

    vest_ok = verify_safety_vest_features(worker_box, vest_box, frame=frame_ppe, confidence=0.60)
    assert vest_ok is True, "Genuine fluorescent vest with reflective strips must pass verification"


def test_anatomical_oversized_helmet_box_rejected():
    """Verify oversized helmet box (e.g. spanning hair + face + neck + shoulders) is rejected."""
    worker_box = np.array([500.0, 100.0, 780.0, 660.0])  # wh = 560
    # Box with height 200 (ph/wh = 200/560 = 0.357 > 0.26)
    oversized_box = np.array([550.0, 100.0, 730.0, 300.0])

    passes = verify_helmet_features(worker_box, oversized_box, frame=None, confidence=0.70)
    assert passes is False, "Oversized helmet box spanning down to chest must be rejected by anatomical checks"


def test_anatomical_misplaced_helmet_box_rejected():
    """Verify helmet box centered too low on the body (e.g. chest level) is rejected."""
    worker_box = np.array([500.0, 100.0, 780.0, 660.0])  # wy1 = 100, wh = 560
    # Box placed at chest level (py1 = 280, py2 = 360, center = 320 -> rel_yc = 220/560 = 0.39)
    chest_box = np.array([580.0, 280.0, 700.0, 360.0])

    passes = verify_helmet_features(worker_box, chest_box, frame=None, confidence=0.70)
    assert passes is False, "Misplaced helmet candidate at chest level must be rejected"


def test_per_class_confidence_filtering():
    """Verify Detector enforces per-class thresholds: helmet (0.38), vest (0.38), person (0.25)."""
    det = Detector()
    # Check that class_conf_thresholds loaded from configs/detection.yaml
    assert "helmet" in det.class_conf_thresholds
    assert det.class_conf_thresholds["helmet"] >= 0.35
    assert det.class_conf_thresholds["safety_vest"] >= 0.35
    assert det.class_conf_thresholds["person"] <= 0.30


def test_spatial_associator_rejects_false_positives_in_frame():
    """Verify SpatialPPEAssociator returns None for helmet and vest when visual/anatomical checks fail."""
    associator = SpatialPPEAssociator()
    frame_no_ppe = create_mock_person_image(has_helmet=False, has_vest=False)

    tracked_workers = [(1, np.array([500.0, 100.0, 780.0, 660.0]), 0.88)]
    # Simulate YOLO detections that falsely labeled hair as helmet and navy shirt as vest
    ppe_dets = [
        {"class_name": "helmet", "bbox": [585.0, 100.0, 695.0, 180.0], "confidence": 0.45},
        {"class_name": "safety_vest", "bbox": [520.0, 210.0, 760.0, 450.0], "confidence": 0.46},
    ]

    associations, unassociated = associator.associate(
        tracked_workers, ppe_dets, img_shape=(720, 1280), frame=frame_no_ppe
    )

    # Neither the false helmet nor the false vest should be associated to worker 1
    assert associations[1][PPEItemType.HELMET.value] is None, "False helmet must not be associated to worker"
    assert associations[1][PPEItemType.SAFETY_VEST.value] is None, "False vest must not be associated to worker"


def test_temporal_tracker_confirms_absent_for_unprotected_worker(monkeypatch):
    """
    Verify that when a worker without PPE is observed over multiple frames,
    the compliance engine confirms Helmet: ABSENT and Vest: ABSENT with Overall: NON_COMPLIANT.
    """
    from app.ai.detection.schemas import ImageDetectionResponse, DetectionObject, BoundingBox

    engine = WorkerComplianceEngine()
    frame_no_ppe = create_mock_person_image(has_helmet=False, has_vest=False)

    # Mock detector returning 1 person and 2 false-positive candidate boxes (hair as helmet, navy shirt as vest)
    mock_detections = [
        DetectionObject(
            class_id=0,
            class_name="person",
            confidence=0.92,
            bbox=BoundingBox(x1=500.0, y1=100.0, x2=780.0, y2=660.0),
        ),
        # False positive helmet on hair (must be rejected by associator)
        DetectionObject(
            class_id=1,
            class_name="helmet",
            confidence=0.45,
            bbox=BoundingBox(x1=585.0, y1=100.0, x2=695.0, y2=180.0),
        ),
        # False positive vest on navy shirt (must be rejected by associator)
        DetectionObject(
            class_id=2,
            class_name="safety_vest",
            confidence=0.48,
            bbox=BoundingBox(x1=520.0, y1=210.0, x2=760.0, y2=450.0),
        ),
    ]

    mock_resp = ImageDetectionResponse(
        success=True,
        detections=mock_detections,
        total_detections=len(mock_detections),
        inference_time_ms=12.0,
        image_width=1280,
        image_height=720,
        model_version="test",
        device="cpu",
    )

    monkeypatch.setattr(engine.detector, "detect_image", lambda *args, **kwargs: (mock_resp, None))

    # Process 6 consecutive frames (missing_detection_tolerance is 5)
    last_resp = None
    for _ in range(6):
        resp, _, _ = engine.process_frame(frame_no_ppe, annotate=False)
        last_resp = resp

    assert last_resp is not None
    assert len(last_resp.workers) >= 1, "Tracked worker must be identified"
    worker = last_resp.workers[0]

    # Helmet and vest must NOT be PRESENT; after 5+ missed frames, confirmed ABSENT
    assert worker.ppe["helmet"] == PPEState.ABSENT, f"Expected ABSENT, got {worker.ppe['helmet']}"
    assert worker.ppe["safety_vest"] == PPEState.ABSENT, f"Expected ABSENT, got {worker.ppe['safety_vest']}"
    assert worker.overall_status == OverallComplianceState.NON_COMPLIANT, "Worker without PPE must be NON_COMPLIANT"
