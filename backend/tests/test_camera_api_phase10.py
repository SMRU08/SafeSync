"""
test_camera_api_phase10.py — SafeSync Phase 10 Step 6
Automated test suite for Multi-Camera REST API endpoints:
- GET /api/cameras (list real-time camera operational statuses)
- GET /api/cameras/{camera_id} (single camera telemetry)
- POST /api/cameras/{camera_id}/start (start camera worker)
- POST /api/cameras/{camera_id}/stop (stop camera worker)
- POST /api/cameras (register/update camera)
- GET /api/cameras/{camera_id}/snapshot (live JPEG frame retrieval)
- Validation & error cases (404 on missing camera, 503 on missing frame)
"""

import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.camera.manager import CameraManager
from app.camera.schemas import CameraConfigModel, CameraSourceType

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_camera_manager():
    """Ensures a clean camera manager state before each test."""
    CameraManager.reset_instance()
    manager = CameraManager.get_instance()
    # Register a known synthetic camera
    cam_synth = CameraConfigModel(
        id="api_test_synth",
        name="API Test Synthetic Camera",
        zone_id="production_floor",
        source="synthetic://api_test",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
        fps_target=30,
    )
    cam_disabled = CameraConfigModel(
        id="api_test_disabled",
        name="API Test Disabled Camera",
        zone_id="storage_area",
        source="synthetic://disabled",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=False,
    )
    manager.register_camera(cam_synth, start_immediately=True)
    manager.register_camera(cam_disabled, start_immediately=False)
    time.sleep(0.2)

    yield manager

    manager.stop_all()
    CameraManager.reset_instance()


def test_list_cameras_endpoint():
    """Verifies GET /api/cameras returns list of actual camera statuses."""
    response = client.get("/api/cameras")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    ids = [c["camera_id"] for c in data]
    assert "api_test_synth" in ids
    assert "api_test_disabled" in ids

    synth_cam = next(c for c in data if c["camera_id"] == "api_test_synth")
    assert synth_cam["state"] in ("CONNECTED", "STREAMING")
    assert synth_cam["metrics"]["frame_count"] > 0
    assert "safe_source" in synth_cam


def test_get_single_camera_endpoint():
    """Verifies GET /api/cameras/{camera_id} returns accurate camera telemetry."""
    response = client.get("/api/cameras/api_test_synth")
    assert response.status_code == 200
    data = response.json()
    assert data["camera_id"] == "api_test_synth"
    assert data["state"] in ("CONNECTED", "STREAMING")
    assert data["zone_id"] == "production_floor"


def test_get_nonexistent_camera_returns_404():
    """Verifies GET /api/cameras/{camera_id} returns 404 for unknown camera."""
    response = client.get("/api/cameras/nonexistent_camera_id_999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_stop_and_start_camera_endpoints():
    """Verifies POST /api/cameras/{camera_id}/stop and start transitions."""
    # 1. Stop camera
    res_stop = client.post("/api/cameras/api_test_synth/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["state"] == "DISCONNECTED"

    # 2. Verify state reflects in GET
    res_get = client.get("/api/cameras/api_test_synth")
    assert res_get.json()["state"] == "DISCONNECTED"

    # 3. Start camera
    res_start = client.post("/api/cameras/api_test_synth/start")
    assert res_start.status_code == 200
    time.sleep(0.2)
    res_get2 = client.get("/api/cameras/api_test_synth")
    assert res_get2.json()["state"] in ("CONNECTED", "STREAMING", "CONNECTING")


def test_register_camera_endpoint():
    """Verifies POST /api/cameras dynamically registers a new camera."""
    payload = {
        "id": "dynamic_cam_01",
        "name": "Dynamic Production Cam",
        "zone_id": "electrical_room",
        "source": "synthetic://dynamic",
        "source_type": "synthetic",
        "enabled": True,
        "fps_target": 25,
        "resolution": "1280x720",
        "reconnect_policy": {
            "max_retries": 3,
            "initial_delay_seconds": 1.0,
            "max_delay_seconds": 10.0,
        },
    }
    response = client.post("/api/cameras", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["camera_id"] == "dynamic_cam_01"
    assert data["state"] in ("CONNECTED", "CONNECTING", "STREAMING")

    # Cleanup
    client.post("/api/cameras/dynamic_cam_01/stop")


def test_get_camera_snapshot_endpoint():
    """Verifies GET /api/cameras/{camera_id}/snapshot returns JPEG byte stream."""
    time.sleep(0.3)
    response = client.get("/api/cameras/api_test_synth/snapshot")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 1000  # valid image binary


def test_get_camera_snapshot_offline_returns_503():
    """Verifies GET /api/cameras/{camera_id}/snapshot returns 503 when camera is offline."""
    response = client.get("/api/cameras/api_test_disabled/snapshot")
    assert response.status_code == 503
    assert "not available" in response.json()["detail"].lower() or "offline" in response.json()["detail"].lower()
