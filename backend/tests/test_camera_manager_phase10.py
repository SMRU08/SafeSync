"""
test_camera_manager_phase10.py — SafeSync Phase 10 Step 5
Automated unit and integration test suite for Multi-Camera Manager:
- Schema validation
- Credential masking
- Isolated worker execution
- Bounded exponential backoff on connection failure
- Disabled camera handling
- Multi-camera fault isolation (one failing camera does not affect another)
- Graceful shutdown
"""

import time
import pytest
import numpy as np

from app.camera.schemas import (
    CameraConfigModel,
    CameraSourceType,
    CameraState,
    ReconnectPolicy,
)
from app.camera.worker import CameraWorker, mask_camera_source, expand_source_env
from app.camera.manager import CameraManager


def test_credential_masking():
    """Verifies that plaintext RTSP/HTTP credentials are never exposed in safe_source."""
    source = "rtsp://admin:SecretPassword123@192.168.1.50:554/stream"
    masked = mask_camera_source(source)
    assert "SecretPassword123" not in masked
    assert "admin:********@" in masked


def test_camera_config_schema_validation():
    """Verifies strict validation of camera configuration models."""
    cfg = CameraConfigModel(
        id="test_cam_01",
        name="Test Camera",
        source="synthetic://test",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
        fps_target=25,
    )
    assert cfg.id == "test_cam_01"
    assert cfg.source_type == CameraSourceType.SYNTHETIC
    assert cfg.reconnect_policy.max_retries == 5


def test_synthetic_camera_worker_captures_frames():
    """Verifies that synthetic camera worker connects, streams frames, and increments metrics."""
    cfg = CameraConfigModel(
        id="synthetic_01",
        name="Synthetic Stream",
        source="synthetic://test",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
        fps_target=30,
    )
    worker = CameraWorker(cfg)
    try:
        worker.start()
        time.sleep(0.3)

        status = worker.get_status()
        assert status.state in (CameraState.CONNECTED, CameraState.STREAMING)
        assert status.metrics.frame_count > 0

        frame, ts = worker.get_latest_frame()
        assert frame is not None
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (480, 640, 3)
        assert ts is not None
    finally:
        worker.stop()
        time.sleep(0.1)
        assert worker.get_status().state == CameraState.DISCONNECTED


def test_disabled_camera_does_not_start():
    """Verifies that disabled camera transitions to DISABLED and starts no thread."""
    cfg = CameraConfigModel(
        id="disabled_cam",
        name="Disabled Camera",
        source="synthetic://test",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=False,
    )
    worker = CameraWorker(cfg)
    worker.start()

    status = worker.get_status()
    assert status.state == CameraState.DISABLED
    assert status.metrics.frame_count == 0
    worker.stop()


def test_invalid_camera_source_reconnects_and_errors():
    """Verifies bounded backoff and transition to ERROR after reaching max_retries."""
    cfg = CameraConfigModel(
        id="failing_cam",
        name="Failing Camera",
        source="rtsp://nonexistent_ip_address_fake:554/stream",
        source_type=CameraSourceType.RTSP,
        enabled=True,
        reconnect_policy=ReconnectPolicy(
            max_retries=2,
            initial_delay_seconds=0.1,
            max_delay_seconds=0.2,
        ),
    )
    worker = CameraWorker(cfg)
    try:
        worker.start()
        # Wait enough time for 2 retries (0.1s + 0.2s + overhead)
        time.sleep(1.0)

        status = worker.get_status()
        assert status.metrics.reconnect_count >= 2
        assert status.state in (CameraState.ERROR, CameraState.OFFLINE)
        assert status.metrics.last_error is not None
    finally:
        worker.stop()


def test_multi_camera_fault_isolation():
    """
    CRITICAL PRODUCTION REQUIREMENT:
    One failing camera MUST NOT crash or impair other working cameras.
    """
    cam_good = CameraConfigModel(
        id="good_cam",
        name="Good Synthetic Cam",
        source="synthetic://good",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
        fps_target=30,
    )
    cam_bad = CameraConfigModel(
        id="bad_cam",
        name="Bad Unreachable Cam",
        source="rtsp://nonexistent_host:554/live",
        source_type=CameraSourceType.RTSP,
        enabled=True,
        reconnect_policy=ReconnectPolicy(
            max_retries=1,
            initial_delay_seconds=0.1,
            max_delay_seconds=0.2,
        ),
    )

    worker_good = CameraWorker(cam_good)
    worker_bad = CameraWorker(cam_bad)

    try:
        worker_good.start()
        worker_bad.start()

        time.sleep(1.2)

        status_good = worker_good.get_status()
        status_bad = worker_bad.get_status()

        # Bad camera should have errored, be reconnecting, or entered OFFLINE
        assert status_bad.state in (CameraState.ERROR, CameraState.RECONNECTING, CameraState.OFFLINE)
        assert status_bad.metrics.frame_count == 0

        # Good camera MUST remain CONNECTED/STREAMING and actively producing frames
        assert status_good.state in (CameraState.CONNECTED, CameraState.STREAMING)
        assert status_good.metrics.frame_count >= 1

        frame, _ = worker_good.get_latest_frame()
        assert frame is not None
    finally:
        worker_good.stop()
        worker_bad.stop()


def test_camera_manager_orchestration():
    """Verifies CameraManager lifecycle, registration, dynamic start/stop, and graceful shutdown."""
    CameraManager.reset_instance()
    manager = CameraManager.get_instance()

    # Register dynamic test cameras
    cam1 = CameraConfigModel(
        id="mgr_cam_1",
        name="Manager Cam 1",
        source="synthetic://mgr1",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
        fps_target=30,
    )
    cam2 = CameraConfigModel(
        id="mgr_cam_2",
        name="Manager Cam 2",
        source="synthetic://mgr2",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=False,
    )
    manager.register_camera(cam1, start_immediately=True)
    manager.register_camera(cam2, start_immediately=True)

    time.sleep(0.3)

    st1 = manager.get_camera_status("mgr_cam_1")
    st2 = manager.get_camera_status("mgr_cam_2")

    assert st1 is not None
    assert st1.state in (CameraState.CONNECTED, CameraState.STREAMING)
    assert st2 is not None
    assert st2.state == CameraState.DISABLED

    all_statuses = manager.get_all_statuses()
    cam_ids = [s.camera_id for s in all_statuses]
    assert "mgr_cam_1" in cam_ids
    assert "mgr_cam_2" in cam_ids

    # Stop specific camera
    manager.stop_camera("mgr_cam_1")
    time.sleep(0.1)
    assert manager.get_camera_status("mgr_cam_1").state == CameraState.DISCONNECTED

    # Graceful stop all
    manager.stop_all()
    CameraManager.reset_instance()
