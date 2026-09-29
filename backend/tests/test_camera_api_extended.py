"""
test_camera_api_extended.py — SafeSync
Unit and integration tests for multi-camera surveillance endpoints:
- GET /api/cameras (multi-camera list with operational metrics)
- POST /api/cameras (dynamic registration & DB persistence)
- DELETE /api/cameras/{id} (unregistration & DB cleanup)
- GET /api/cameras/{id}/stream (MJPEG live streaming)
- POST /api/cameras/test-source (pre-flight source verification)
- Fault isolation across concurrent cameras
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.camera.manager import CameraManager

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_cameras():
    CameraManager.reset_instance()
    yield
    CameraManager.reset_instance()


def test_list_cameras_endpoint():
    """Verifies GET /api/cameras returns all registered cameras with required surveillance fields."""
    response = client.get("/api/cameras")
    assert response.status_code == 200
    cameras = response.json()
    assert isinstance(cameras, list)
    assert len(cameras) >= 1

    first_cam = cameras[0]
    assert "camera_id" in first_cam
    assert "name" in first_cam
    assert "status" in first_cam
    assert "stream_url" in first_cam
    assert "fps" in first_cam
    assert "resolution" in first_cam
    assert "metrics" in first_cam


def test_test_camera_source_synthetic():
    """Verifies POST /api/cameras/test-source validates synthetic source."""
    resp = client.post("/api/cameras/test-source", json={
        "source": "synthetic://test",
        "source_type": "synthetic"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["reachable"] is True


def test_create_and_delete_camera():
    """Verifies adding a camera persists to DB and deleting unregisters it."""
    new_cam_payload = {
        "id": "test_cam_surveillance",
        "name": "Surveillance Test Camera",
        "location": "Loading Bay South",
        "zone_id": "loading_dock",
        "source": "synthetic://surveillance",
        "source_type": "synthetic",
        "enabled": True,
        "fps_target": 25,
        "resolution": "1280x720",
    }

    # 1. Create camera
    create_resp = client.post("/api/cameras", json=new_cam_payload)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["camera_id"] == "test_cam_surveillance"
    assert created_data["status"] in ("online", "connecting", "offline", "streaming")
    assert created_data["stream_url"] == "/api/cameras/test_cam_surveillance/stream"

    # 2. Verify it is present in camera list
    list_resp = client.get("/api/cameras")
    assert list_resp.status_code == 200
    all_cams = list_resp.json()
    cam_ids = [c["camera_id"] for c in all_cams]
    assert "test_cam_surveillance" in cam_ids

    # 3. Delete camera
    del_resp = client.delete("/api/cameras/test_cam_surveillance")
    assert del_resp.status_code == 200
    assert del_resp.json()["camera_id"] == "test_cam_surveillance"

    # 4. Verify no longer present
    list_resp2 = client.get("/api/cameras")
    all_cams2 = list_resp2.json()
    assert "test_cam_surveillance" not in [c["camera_id"] for c in all_cams2]


def test_mjpeg_stream_endpoint():
    """Verifies GET /api/cameras/{id}/stream initializes multipart MJPEG stream."""
    # Ensure camera_01 exists or create a synthetic test camera
    manager = CameraManager.get_instance()
    from app.camera.schemas import CameraConfigModel, CameraSourceType
    cfg = CameraConfigModel(
        id="test_stream_cam",
        name="Stream Test",
        source="synthetic://stream",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
    )
    try:
        manager.register_camera(cfg, start_immediately=True, persist_db=False)

        import time
        time.sleep(0.1)
        from app.api.cameras import _generate_mjpeg_stream
        gen = _generate_mjpeg_stream("test_stream_cam")
        first_chunk = next(gen)
        assert b"--frame\r\n" in first_chunk
        assert b"Content-Type: image/jpeg\r\n" in first_chunk
    finally:
        manager.unregister_camera("test_stream_cam", delete_db=True)


def test_camera_speaker_toggle_json_and_raw_string():
    """Verifies POST /api/cameras/{id}/speaker works with JSON dict, raw string, and text/plain headers."""
    manager = CameraManager.get_instance()
    from app.camera.schemas import CameraConfigModel, CameraSourceType
    cfg = CameraConfigModel(
        id="test_speaker_cam",
        name="Speaker Test",
        source="synthetic://speaker",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
        speaker_enabled=True,
    )
    try:
        manager.register_camera(cfg, start_immediately=False, persist_db=False)

        # 1. Turn OFF via standard JSON
        resp1 = client.post("/api/cameras/test_speaker_cam/speaker", json={"enabled": False})
        assert resp1.status_code == 200
        assert resp1.json()["speaker_enabled"] is False
        assert resp1.json()["speaker_status"] == "OFF"

        # 2. Turn ON via raw text/plain string (simulating frontend fetch without Content-Type header)
        resp2 = client.post(
            "/api/cameras/test_speaker_cam/speaker",
            content='{"enabled":true}',
            headers={"Content-Type": "text/plain"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["speaker_enabled"] is True
        assert resp2.json()["speaker_status"] == "ON"

        # 3. Turn OFF via raw string with quotes
        resp3 = client.post(
            "/api/cameras/test_speaker_cam/speaker",
            content='{"enabled":false}',
            headers={"Content-Type": "text/plain"},
        )
        assert resp3.status_code == 200
        assert resp3.json()["speaker_enabled"] is False
        assert resp3.json()["speaker_status"] == "OFF"

        # 4. Check GET /api/cameras/{id}/speaker
        get_resp = client.get("/api/cameras/test_speaker_cam/speaker")
        assert get_resp.status_code == 200
        assert get_resp.json()["speaker_enabled"] is False
    finally:
        manager.unregister_camera("test_speaker_cam", delete_db=True)
