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
import time
import cv2
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Response, Depends, UploadFile, File
from fastapi.responses import StreamingResponse

from app.camera.schemas import CameraConfigModel, CameraStatus, CameraState
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


@router.post("/{camera_id}/reconnect", response_model=CameraStatus, status_code=status.HTTP_200_OK)
def reconnect_camera(
    camera_id: str,
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR"])),
):
    """Restarts capture connection loop immediately for a specific camera."""
    manager = CameraManager.get_instance()
    if camera_id not in manager.workers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )
    manager.stop_camera(camera_id)
    time.sleep(0.3)
    manager.start_camera(camera_id)
    return manager.get_camera_status(camera_id)


@router.post("", response_model=CameraStatus, status_code=status.HTTP_201_CREATED)
def create_or_update_camera(
    config: CameraConfigModel,
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR"])),
):
    """Registers or updates a camera configuration and persists to database."""
    manager = CameraManager.get_instance()
    manager.register_camera(config, start_immediately=config.enabled, persist_db=True)
    status_obj = manager.get_camera_status(config.id)
    if not status_obj:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve camera status after registration.",
        )
    return status_obj


@router.delete("/{camera_id}", status_code=status.HTTP_200_OK)
def delete_camera(
    camera_id: str,
    current_user: User = Depends(require_role(["ADMIN"])),
):
    """Removes a camera from active surveillance and deletes it from database."""
    manager = CameraManager.get_instance()
    if camera_id not in manager.workers and camera_id not in manager.configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )
    manager.unregister_camera(camera_id, delete_db=True)
    return {"message": f"Camera '{camera_id}' successfully removed.", "camera_id": camera_id}


@router.post("/test-source", status_code=status.HTTP_200_OK)
def test_camera_source(payload: Dict[str, Any]):
    """Tests connectivity to a camera source without registering it."""
    source = payload.get("source")
    source_type = payload.get("source_type", "usb")
    if not source:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required 'source' parameter.")
    manager = CameraManager.get_instance()
    return manager.test_camera_source(str(source), str(source_type))


def _generate_mjpeg_stream(camera_id: str, annotated: bool = True):
    """
    Generator yielding multipart MJPEG frames for real-time live browser streaming.
    Zero-lag event-driven consumer: always serves the newest captured frame.
    """
    manager = CameraManager.get_instance()
    last_frame_id = -1
    consecutive_timeouts = 0

    while True:
        frame, frame_id, ts = manager.wait_for_new_frame(
            camera_id=camera_id,
            last_frame_id=last_frame_id,
            annotated=annotated,
            timeout=0.06,
        )

        if frame is not None and frame_id > last_frame_id:
            last_frame_id = frame_id
            consecutive_timeouts = 0
            ret, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                cap_ms = int((ts or time.time()) * 1000)
                header = (
                    f"--frame\r\n"
                    f"Content-Type: image/jpeg\r\n"
                    f"X-Frame-Id: {frame_id}\r\n"
                    f"X-Capture-Timestamp: {cap_ms}\r\n\r\n"
                ).encode("ascii")
                yield header + jpeg.tobytes() + b"\r\n"
        else:
            consecutive_timeouts += 1
            worker = manager.get_worker(camera_id)
            if not worker or worker.state in (CameraState.DISCONNECTED, CameraState.DISABLED, CameraState.ERROR):
                if consecutive_timeouts > 50:  # ~3 seconds offline
                    break
            time.sleep(0.01)


@router.get("/{camera_id}/stream")
def get_camera_stream(
    camera_id: str,
    annotated: bool = True,
):
    """
    Real-time MJPEG live video stream for a specific camera.
    Supported natively by all browsers via standard <img src="/api/cameras/{id}/stream" /> tags.
    """
    manager = CameraManager.get_instance()
    if camera_id not in manager.workers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )
    return StreamingResponse(
        _generate_mjpeg_stream(camera_id, annotated=annotated),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/{camera_id}/snapshot")
def get_camera_snapshot(
    camera_id: str,
    annotated: bool = True,
):
    """
    Returns the latest frame captured by the camera worker as a JPEG image.
    By default (annotated=True), includes real-time YOLO bounding boxes, worker tracking IDs, and compliance HUD.
    """
    manager = CameraManager.get_instance()
    frame, ts = manager.get_latest_frame(camera_id, annotated=annotated)
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


@router.post("/{camera_id}/analyze")
async def analyze_camera_frame(
    camera_id: str,
    file: Optional[UploadFile] = File(None),
):
    """
    Runs on-demand AI detection & PPE compliance on the camera's live frame or uploaded frame.
    Strictly isolated and tagged to the specified camera_id.
    """
    import numpy as np
    from app.ai.compliance.compliance_engine import WorkerComplianceEngine

    manager = CameraManager.get_instance()
    if camera_id not in manager.workers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera '{camera_id}' not registered.",
        )

    engine = WorkerComplianceEngine()

    if file:
        content = await file.read()
        nparr = np.frombuffer(content, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not decode uploaded image.")
    else:
        frame, ts = manager.get_latest_frame(camera_id, annotated=False)
        if frame is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Camera '{camera_id}' has no live frames available for analysis.",
            )

    try:
        compliance_resp, annotated_frame, latencies = engine.process_frame(
            frame, confidence_threshold=0.20, annotate=True
        )

        _, encoded_img = cv2.imencode(".jpg", annotated_frame)
        import base64
        b64_img = base64.b64encode(encoded_img).decode("utf-8")

        return {
            "camera_id": camera_id,
            "timestamp": time.time(),
            "workers": [w.model_dump() if hasattr(w, "model_dump") else vars(w) for w in compliance_resp.workers],
            "summary": compliance_resp.summary.model_dump() if hasattr(compliance_resp.summary, "model_dump") else vars(compliance_resp.summary),
            "latencies": latencies,
            "annotated_image_base64": f"data:image/jpeg;base64,{b64_img}",
        }
    except Exception as exc:
        logger.error("AI frame analysis failed for camera %s: %s", camera_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(exc)}",
        )


@router.get("/{camera_id}/speaker")
def get_camera_speaker_status(camera_id: str):
    """Returns whether the camera speaker is ON or OFF."""
    manager = CameraManager.get_instance()
    cam_status = manager.get_camera_status(camera_id)
    if not cam_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )
    return {
        "camera_id": camera_id,
        "speaker_enabled": cam_status.speaker_enabled,
        "speaker_status": "ON" if cam_status.speaker_enabled else "OFF",
    }


@router.post("/{camera_id}/speaker")
def set_camera_speaker_status(
    camera_id: str,
    payload: Dict[str, Any],
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR"])),
):
    """Enables or disables localized audio alerts for this camera (Requires ADMIN or OPERATOR role)."""
    manager = CameraManager.get_instance()
    if camera_id not in manager.workers and camera_id not in manager.configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )
    enabled = bool(payload.get("enabled", True))
    manager.set_camera_speaker(camera_id, enabled)
    return {
        "camera_id": camera_id,
        "speaker_enabled": enabled,
        "speaker_status": "ON" if enabled else "OFF",
        "message": f"Camera {camera_id} speaker turned {'ON' if enabled else 'OFF'}.",
    }


