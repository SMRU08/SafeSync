"""
cameras.py — RAKSHYA VISION Phase 10 Step 6
FastAPI REST router exposing production Multi-Camera Manager operations:
- GET /api/cameras: List all registered cameras with real-time operational status and metrics
- GET /api/cameras/{camera_id}: Retrieve single camera telemetry and status
- POST /api/cameras/{camera_id}/start: Start camera worker
- POST /api/cameras/{camera_id}/stop: Stop camera worker
- POST /api/cameras: Register new camera dynamically
- GET /api/cameras/{camera_id}/snapshot: Retrieve the latest captured camera frame (JPEG)
"""

import io
import cv2
import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Response, Depends

from app.camera.schemas import CameraConfigModel, CameraStatus
from app.camera.manager import CameraManager
from app.security.auth import require_role
from app.models.user import User

logger = logging.getLogger("api_cameras")
router = APIRouter(prefix="/api/cameras", tags=["Cameras"])


@router.get("", response_model=List[CameraStatus], status_code=status.HTTP_200_OK)
def list_cameras():
    """
    Returns real-time operational status and metrics for all registered cameras.
    Guaranteed no fake or hardcoded telemetry: reads directly from active CameraWorkers.
    """
    manager = CameraManager.get_instance()
    return manager.get_all_statuses()


@router.get("/{camera_id}", response_model=CameraStatus, status_code=status.HTTP_200_OK)
def get_camera(camera_id: str):
    """Returns telemetry and metrics for a specific camera."""
    manager = CameraManager.get_instance()
    cam_status = manager.get_camera_status(camera_id)
    if not cam_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )
    return cam_status


@router.post("/{camera_id}/start", response_model=CameraStatus, status_code=status.HTTP_200_OK)
def start_camera(
    camera_id: str,
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR"])),
):
    """Starts capture loop for a specific camera (Requires ADMIN or OPERATOR role)."""
    manager = CameraManager.get_instance()
    if camera_id not in manager.workers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )
    manager.start_camera(camera_id)
    return manager.get_camera_status(camera_id)


@router.post("/{camera_id}/stop", response_model=CameraStatus, status_code=status.HTTP_200_OK)
def stop_camera(
    camera_id: str,
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR"])),
):
    """Gracefully stops capture loop for a specific camera (Requires ADMIN or OPERATOR role)."""
    manager = CameraManager.get_instance()
    if camera_id not in manager.workers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )
    manager.stop_camera(camera_id)
    return manager.get_camera_status(camera_id)


@router.post("", response_model=CameraStatus, status_code=status.HTTP_201_CREATED)
def create_or_update_camera(
    config: CameraConfigModel,
    current_user: User = Depends(require_role(["ADMIN"])),
):
    """Registers or updates a camera configuration (Requires ADMIN role)."""
    manager = CameraManager.get_instance()
    manager.register_camera(config, start_immediately=config.enabled)
    return manager.get_camera_status(config.id)


@router.get("/{camera_id}/snapshot")
def get_camera_snapshot(camera_id: str):
    """
    Returns the latest raw frame captured by the camera worker as a JPEG image.
    If stream is offline or no frame captured yet, returns 503.
    """
    manager = CameraManager.get_instance()
    frame, ts = manager.get_latest_frame(camera_id)
    if frame is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No active frame available for camera '{camera_id}'. Stream may be offline or connecting.",
        )

    success, encoded = cv2.imencode(".jpg", frame)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to encode frame into JPEG.",
        )

    return Response(content=encoded.tobytes(), media_type="image/jpeg")
