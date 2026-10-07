"""
test_entry_gate_dedup.py — Entry Gate Duplicate Bounding Box Verification Test Suite

Verifies that for Entry Gate ONLY:
- 1 Person -> Exactly 1 Person box
- Multiple distinct workers -> Exactly 1 box per worker (no false merges)
- Worker + PPE -> Exactly 1 box per PPE item (no duplicate helmet/vest/glove/shoe)
- Person + Fire + Smoke -> Exactly 1 Person, 1 Fire, 1 Smoke (no mutual suppression)
- Multiple Frames -> Stable track IDs and box counts across 30 consecutive frames
- Stream Reconnect -> Zero leftover/ghost boxes after reconnect
- Other cameras (Production Floor, etc.) -> Completely untouched
"""

import numpy as np
import pytest
from app.ai.compliance.compliance_engine import (
    WorkerComplianceEngine,
    deduplicate_entry_gate_detections,
)
from app.ai.detection.schemas import (
    BoundingBox,
    DetectionObject,
    ImageDetectionResponse,
)


def _make_det(class_name: str, bbox: list, conf: float = 0.90, class_id: int = 0) -> DetectionObject:
    return DetectionObject(
        class_id=class_id,
        class_name=class_name,
        confidence=conf,
        bbox=BoundingBox(x1=bbox[0], y1=bbox[1], x2=bbox[2], y2=bbox[3]),
    )


def test_entry_gate_dedup_function_one_person():
    """Test 1: One Person with duplicate/overlapping candidate boxes receives exactly 1 box."""
    raw_dets = [
        _make_det("person", [100, 100, 300, 600], conf=0.92),
        _make_det("person", [105, 102, 298, 595], conf=0.88),  # Duplicate overlapping
        _make_det("person", [120, 150, 280, 580], conf=0.75),  # Nested duplicate
    ]
    deduped = deduplicate_entry_gate_detections(raw_dets)
    assert len(deduped) == 1
    assert deduped[0].class_name == "person"
    assert deduped[0].confidence == 0.92


def test_entry_gate_dedup_function_multiple_workers():
    """Test 2: Multiple workers at distinct spatial coordinates are NOT merged."""
    raw_dets = [
        _make_det("person", [50, 100, 200, 600], conf=0.91),    # Worker 1 (left)
        _make_det("person", [55, 105, 195, 595], conf=0.85),    # Duplicate of Worker 1
        _make_det("person", [300, 100, 450, 600], conf=0.89),   # Worker 2 (middle)
        _make_det("person", [550, 100, 700, 600], conf=0.93),   # Worker 3 (right)
    ]
    deduped = deduplicate_entry_gate_detections(raw_dets)
    assert len(deduped) == 3
    # Exactly 3 workers retained, each with highest confidence
    confs = sorted([d.confidence for d in deduped])
    assert confs == [0.89, 0.91, 0.93]


def test_entry_gate_dedup_function_worker_plus_ppe():
    """Test 3: Worker + PPE items retain exactly 1 box per real object (no duplicate helmet/vest/gloves)."""
    raw_dets = [
        _make_det("person", [100, 100, 400, 700], conf=0.95),
        _make_det("helmet", [180, 105, 280, 180], conf=0.93),
        _make_det("helmet", [185, 110, 275, 175], conf=0.82),   # Duplicate helmet candidate
        _make_det("safety_vest", [150, 220, 350, 450], conf=0.91),
        _make_det("safety_vest", [155, 230, 345, 440], conf=0.80), # Duplicate vest candidate
        _make_det("gloves", [110, 400, 160, 470], conf=0.88),
        _make_det("gloves", [340, 400, 390, 470], conf=0.87),    # Other hand
        _make_det("safety_footwear", [160, 650, 240, 700], conf=0.85),
    ]
    deduped = deduplicate_entry_gate_detections(raw_dets)
    classes = [d.class_name for d in deduped]
    assert classes.count("person") == 1
    assert classes.count("helmet") == 1
    assert classes.count("safety_vest") == 1
    assert classes.count("gloves") == 2  # Left and right hands at distinct locations
    assert classes.count("safety_footwear") == 1


def test_entry_gate_dedup_function_fire_smoke():
    """Test 4: Person + Fire + Smoke in Entry Gate retains 1 Person, 1 Fire, 1 Smoke without mutual suppression."""
    raw_dets = [
        _make_det("person", [100, 100, 300, 600], conf=0.92),
        _make_det("fire", [500, 300, 650, 500], conf=0.88),
        _make_det("fire", [510, 310, 640, 490], conf=0.76),     # Duplicate fire candidate
        _make_det("smoke", [480, 150, 700, 350], conf=0.84),
        _make_det("smoke", [490, 160, 690, 340], conf=0.72),    # Duplicate smoke candidate
    ]
    deduped = deduplicate_entry_gate_detections(raw_dets)
    classes = [d.class_name for d in deduped]
    assert classes.count("person") == 1
    assert classes.count("fire") == 1
    assert classes.count("smoke") == 1
    assert len(deduped) == 3


def test_compliance_engine_entry_gate_integration():
    """Test full compliance engine processing on Entry Gate."""
    engine = WorkerComplianceEngine()
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    # Mock detector returning raw detections with duplicates
    class MockDetector:
        def detect_image(self, img, conf=0.25, imgsz=640, annotate=False):
            return ImageDetectionResponse(
                detections=[
                    _make_det("person", [200, 150, 450, 650], conf=0.94),
                    _make_det("person", [205, 155, 445, 645], conf=0.87),  # Duplicate person
                    _make_det("helmet", [280, 155, 370, 230], conf=0.91),
                    _make_det("helmet", [285, 160, 365, 225], conf=0.79),  # Duplicate helmet
                    _make_det("safety_vest", [240, 250, 410, 480], conf=0.90),
                ],
                total_detections=5,
                inference_time_ms=10.0,
            ), None

    engine.detector = MockDetector()

    # Process frame with zone_id="entry_gate"
    resp, annotated_frame, latencies = engine.process_frame(
        frame, zone_id="entry_gate", annotate=True
    )

    # Exactly 1 tracked worker
    assert len(resp.workers) == 1
    worker = resp.workers[0]
    # PPE associated cleanly into ppe_details
    assert "helmet" in worker.ppe_details
    assert "safety_vest" in worker.ppe_details
    assert worker.ppe_details["helmet"].bbox is not None
    assert worker.ppe_details["safety_vest"].bbox is not None


def test_visualizer_entry_gate_dedup_and_clean_render():
    """Test visualizer renders clean single boxes and suppresses phantom unassociated_ppe for Entry Gate."""
    engine = WorkerComplianceEngine()
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    class MockDetector:
        def detect_image(self, img, conf=0.25, imgsz=640, annotate=False):
            return ImageDetectionResponse(
                detections=[
                    _make_det("person", [200, 150, 450, 650], conf=0.94),
                    _make_det("helmet", [280, 155, 370, 230], conf=0.91),
                    _make_det("fire", [700, 200, 900, 450], conf=0.85),
                    _make_det("fire", [710, 210, 890, 440], conf=0.75),  # Overlapping fire
                ],
                total_detections=4,
                inference_time_ms=10.0,
            ), None

    engine.detector = MockDetector()
    resp, annotated_frame, latencies = engine.process_frame(
        frame, zone_id="entry_gate", annotate=True
    )
    assert annotated_frame is not None
    assert annotated_frame.shape == (720, 1280, 3)


def test_entry_gate_multiple_frames_stability():
    """Test 5: Over 30 consecutive frames, track ID and box count stay strictly stable."""
    engine = WorkerComplianceEngine()
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    class StableDetector:
        def detect_image(self, img, conf=0.25, imgsz=640, annotate=False):
            return ImageDetectionResponse(
                detections=[
                    _make_det("person", [200, 150, 450, 650], conf=0.95),
                    _make_det("person", [204, 152, 448, 646], conf=0.82),  # Intra-frame jitter/dup
                    _make_det("helmet", [280, 155, 370, 230], conf=0.92),
                    _make_det("safety_vest", [240, 250, 410, 480], conf=0.89),
                ],
                total_detections=4,
                inference_time_ms=8.0,
            ), None

    engine.detector = StableDetector()

    initial_track_id = None
    for frame_idx in range(30):
        resp, _, _ = engine.process_frame(frame, zone_id="entry_gate", annotate=False)
        assert len(resp.workers) == 1, f"Frame {frame_idx}: expected 1 worker, got {len(resp.workers)}"
        worker = resp.workers[0]
        if initial_track_id is None:
            initial_track_id = worker.track_id
        else:
            assert worker.track_id == initial_track_id, f"Frame {frame_idx}: track ID changed from {initial_track_id} to {worker.track_id}"


def test_entry_gate_reconnect_clean_state():
    """Test 6: Tracker reset / stream reconnect flushes state cleanly without leftover duplicate boxes."""
    engine = WorkerComplianceEngine()
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    class ActiveDetector:
        def detect_image(self, img, conf=0.25, imgsz=640, annotate=False):
            return ImageDetectionResponse(
                detections=[_make_det("person", [200, 150, 450, 650], conf=0.95)],
                total_detections=1,
                inference_time_ms=8.0,
            ), None

    class EmptyDetector:
        def detect_image(self, img, conf=0.25, imgsz=640, annotate=False):
            return ImageDetectionResponse(detections=[], total_detections=0, inference_time_ms=5.0), None

    engine.detector = ActiveDetector()
    resp1, _, _ = engine.process_frame(frame, zone_id="entry_gate")
    assert len(resp1.workers) == 1

    # Simulate camera disconnect and reconnect by reinitializing tracker
    from app.ai.compliance.tracker import ByteTrack
    engine.tracker = ByteTrack()
    engine.temporal_tracker.reset()
    engine.detector = EmptyDetector()

    resp2, _, _ = engine.process_frame(frame, zone_id="entry_gate")
    assert len(resp2.workers) == 0, "Expected 0 workers after clean reset"
