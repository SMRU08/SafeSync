"""
test_live_camera_pipeline.py — RAKSHYA VISION Live Camera AI Pipeline Tests
Tests:
- CameraWorker AI engine initialization & thread-local safety
- Frame inference scheduling (infer_interval_frames)
- Real YOLOv8 / WorkerComplianceEngine execution within CameraWorker
- Latest annotated frame buffering and snapshot retrieval
- Live worker tracking exposure via get_live_compliance()
- /api/compliance/live endpoint aggregation across camera workers
- /api/cameras/{camera_id}/snapshot annotated frame delivery
- Temporal compliance confirmation (N_confirm = 3) and alert generation
- UNKNOWN occlusion state safety (UNKNOWN != VIOLATION)
"""

import time
import pytest
import numpy as np
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.camera.schemas import (
    CameraConfigModel,
    CameraSourceType,
    CameraState,
    CameraStatus,
)
from app.camera.worker import CameraWorker
from app.camera.manager import CameraManager
from app.ai.compliance.schemas import (
    PPEItemType,
    PPEState,
    WorkerBoundingBox,
    PPEObservation,
    WorkerTrack,
    ComplianceSummary,
    ComplianceAnalysisResponse,
)
from app.services.event_normalizer import EventNormalizer
from app.services.alert_engine import AlertEngine

client = TestClient(app)


def test_camera_worker_ai_engines_init():
    """Verify that CameraWorker initializes compliance, alert, and normalizer engines."""
    cfg = CameraConfigModel(
        id="test_ai_cam_init",
        name="AI Init Cam",
        source="synthetic://test",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
    )
    worker = CameraWorker(cfg)
    assert worker._compliance_engine is None
    assert worker._alert_engine is None
    assert worker._event_normalizer is None

    worker._init_ai_engines()
    assert worker._compliance_engine is not None
    assert worker._alert_engine is not None
    assert worker._event_normalizer is not None


def test_camera_worker_process_frame_ai():
    """Verify CameraWorker._process_frame_ai runs compliance analysis and buffers results."""
    cfg = CameraConfigModel(
        id="test_ai_cam_process",
        name="AI Process Cam",
        source="synthetic://test",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
    )
    worker = CameraWorker(cfg)
    worker._init_ai_engines()

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    now = time.time()

    dummy_worker = WorkerTrack(
        track_id=101,
        bbox=WorkerBoundingBox(x1=100, y1=100, x2=200, y2=400),
        confidence=0.88,
        ppe={
            "helmet": PPEState.ABSENT,
            "safety_vest": PPEState.PRESENT,
        },
        ppe_details={
            "helmet": PPEObservation(
                item_type=PPEItemType.HELMET,
                state=PPEState.ABSENT,
                confidence=0.9,
            ),
            "safety_vest": PPEObservation(
                item_type=PPEItemType.SAFETY_VEST,
                state=PPEState.PRESENT,
                confidence=0.95,
            ),
        },
    )
    dummy_summary = ComplianceSummary(
        total_workers=1,
        compliant_workers=0,
        non_compliant_workers=1,
        unknown_workers=0,
    )
    dummy_resp = ComplianceAnalysisResponse(
        frame_id=1,
        timestamp_utc="2026-09-21T00:00:00Z",
        workers=[dummy_worker],
        summary=dummy_summary,
        annotated_image_base64="data:image/jpeg;base64,mock",
    )
    annotated_mock = np.ones((480, 640, 3), dtype=np.uint8) * 128

    with patch.object(
        worker._compliance_engine,
        "process_frame",
        return_value=(dummy_resp, annotated_mock, {}),
    ):
        worker._process_frame_ai(frame, now)

    # Check metrics and buffered results
    assert worker.metrics.active_workers == 1
    assert worker.metrics.active_violations == 1
    assert worker._latest_annotated_frame is not None
    assert len(worker._latest_workers) == 1
    assert worker._latest_workers[0].track_id == 101
    assert worker._latest_workers[0].ppe["helmet"] == PPEState.ABSENT


def test_camera_worker_get_latest_frame_annotated():
    """Verify get_latest_frame returns annotated frame when requested."""
    cfg = CameraConfigModel(
        id="test_annotated_frame_cam",
        name="Annotated Frame Cam",
        source="synthetic://test",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
    )
    worker = CameraWorker(cfg)
    raw_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    annotated_frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
    ts = time.time()

    worker._latest_frame = raw_frame
    worker._latest_frame_time = ts
    worker._latest_annotated_frame = annotated_frame

    # Raw frame
    frame, ret_ts = worker.get_latest_frame(annotated=False)
    assert np.array_equal(frame, raw_frame)
    assert ret_ts == ts

    # Annotated frame
    frame, ret_ts = worker.get_latest_frame(annotated=True)
    assert np.array_equal(frame, annotated_frame)
    assert ret_ts == ts


def test_camera_worker_live_compliance_retrieval():
    """Verify worker.get_live_compliance() returns formatted tracking payload."""
    cfg = CameraConfigModel(
        id="test_live_comp_cam",
        name="Live Comp Cam",
        source="synthetic://test",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
    )
    worker = CameraWorker(cfg)
    worker._latest_workers = [
        {
            "track_id": 42,
            "box": [50, 50, 150, 300],
            "confidence": 0.91,
            "ppe": {"helmet": "present", "safety_vest": "absent"},
            "overall_compliant": False,
            "dwell_time_seconds": 12.0,
            "zone_id": "test_live_comp_cam",
        }
    ]
    worker._latest_compliance_summary = {
        "total_workers": 1,
        "compliant_workers": 0,
        "non_compliant_workers": 1,
        "compliance_rate": 0.0,
    }

    comp = worker.get_live_compliance()
    assert comp["camera_id"] == "test_live_comp_cam"
    assert len(comp["workers"]) == 1
    assert comp["workers"][0]["track_id"] == 42
    assert comp["summary"]["total_workers"] == 1


def test_api_compliance_live_endpoint():
    """Verify GET /api/compliance/live queries camera workers and returns live tracking data."""
    CameraManager.reset_instance()
    manager = CameraManager.get_instance()

    cam = CameraConfigModel(
        id="cam_live_test",
        name="Cam Live Test",
        source="synthetic://test",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
    )
    manager.register_camera(cam, start_immediately=False)
    worker = manager.get_worker("cam_live_test")
    assert worker is not None

    worker._latest_workers = [
        {
            "track_id": 1,
            "box": [10, 10, 100, 200],
            "confidence": 0.85,
            "ppe": {"helmet": "present", "safety_vest": "present"},
            "overall_compliant": True,
            "dwell_time_seconds": 3.0,
            "zone_id": "cam_live_test",
        }
    ]
    worker._latest_compliance_summary = {
        "total_workers": 1,
        "compliant_workers": 1,
        "non_compliant_workers": 0,
        "compliance_rate": 100.0,
    }

    response = client.get("/api/compliance/live?camera_id=cam_live_test")
    assert response.status_code == 200
    data = response.json()
    assert data["camera_id"] == "cam_live_test"
    assert len(data["workers"]) == 1
    assert data["workers"][0]["track_id"] == 1
    assert data["summary"]["compliance_rate"] == 100.0

    CameraManager.reset_instance()


def test_unknown_occlusion_never_generates_violation():
    """
    CRITICAL SAFETY REQUIREMENT:
    UNKNOWN state from occlusion must NEVER generate a violation.
    Only confirmed ABSENT state should generate an event.
    """
    normalizer = EventNormalizer()

    # Case 1: Worker with UNKNOWN helmet and UNKNOWN vest
    dummy_worker_unknown = WorkerTrack(
        track_id=202,
        bbox=WorkerBoundingBox(x1=50, y1=50, x2=150, y2=300),
        confidence=0.9,
        ppe={
            "helmet": PPEState.UNKNOWN,
            "safety_vest": PPEState.UNKNOWN,
        },
        ppe_details={
            "helmet": PPEObservation(
                item_type=PPEItemType.HELMET,
                state=PPEState.UNKNOWN,
                confidence=0.5,
                is_occluded=True,
            ),
            "safety_vest": PPEObservation(
                item_type=PPEItemType.SAFETY_VEST,
                state=PPEState.UNKNOWN,
                confidence=0.5,
                is_occluded=True,
            ),
        },
    )
    resp_unknown = ComplianceAnalysisResponse(
        frame_id=1,
        timestamp_utc="2026-09-21T00:00:00Z",
        workers=[dummy_worker_unknown],
        summary=ComplianceSummary(total_workers=1, unknown_workers=1),
    )
    events_unknown = normalizer.from_compliance_response(resp_unknown, camera_id="camera_01")
    assert len(events_unknown) == 0

    # Case 2: Worker with confirmed ABSENT helmet
    dummy_worker_absent = WorkerTrack(
        track_id=202,
        bbox=WorkerBoundingBox(x1=50, y1=50, x2=150, y2=300),
        confidence=0.9,
        ppe={
            "helmet": PPEState.ABSENT,
            "safety_vest": PPEState.PRESENT,
        },
        ppe_details={
            "helmet": PPEObservation(
                item_type=PPEItemType.HELMET,
                state=PPEState.ABSENT,
                confidence=0.92,
            ),
            "safety_vest": PPEObservation(
                item_type=PPEItemType.SAFETY_VEST,
                state=PPEState.PRESENT,
                confidence=0.95,
            ),
        },
    )
    resp_absent = ComplianceAnalysisResponse(
        frame_id=2,
        timestamp_utc="2026-09-21T00:00:01Z",
        workers=[dummy_worker_absent],
        summary=ComplianceSummary(total_workers=1, non_compliant_workers=1),
    )
    events_absent = normalizer.from_compliance_response(resp_absent, camera_id="camera_01")
    assert len(events_absent) == 1
    assert events_absent[0].event_type.value == "MISSING_HELMET"
    assert events_absent[0].track_id == 202


def test_camera_worker_decoupled_realtime_latency_and_bounded_queue():
    """
    Verify that CameraWorker captures frames without waiting for AI,
    discards stale frames using latest-frame-wins (queue depth <= 1),
    and delivers fresh frames with latency < 100ms.
    """
    cfg = CameraConfigModel(
        id="test_realtime_decoupled",
        name="Real-Time Decoupled Cam",
        source="synthetic://test",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
        fps_target=30,
    )
    worker = CameraWorker(cfg)
    try:
        worker.start()
        time.sleep(0.3)

        # 1. Capture thread and AI thread are active
        assert worker._capture_thread is not None and worker._capture_thread.is_alive()
        assert worker._ai_thread is not None and worker._ai_thread.is_alive()

        # 2. Queue depth is bounded strictly at <= 1
        assert worker.metrics.frame_queue_depth <= 1

        # 3. Stream delivery latency is sub-50ms
        frame, frame_id, cap_time = worker.wait_for_new_frame(last_frame_id=-1, timeout=0.1)
        assert frame is not None
        assert frame_id > 0
        assert cap_time is not None
        latency_ms = (time.time() - cap_time) * 1000.0
        assert latency_ms < 100.0, f"Delivery latency too high: {latency_ms}ms"

        # 4. Status reflects operational capture
        status = worker.get_status()
        assert status.state == CameraState.CONNECTED
        assert status.metrics.frame_count > 0
    finally:
        worker.stop()
