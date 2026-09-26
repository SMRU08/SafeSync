"""
detection.py — SafeSync Phase 4 API Router
Endpoints:
  GET  /api/detection/health
  POST /api/detection/image
  POST /api/detection/video
"""

import os
import tempfile
import logging
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse

from app.ai.detection.model_loader import ModelLoader
from app.ai.detection.detector import Detector
from app.ai.detection.video_processor import VideoProcessor
from app.ai.detection.schemas import (
    ImageDetectionResponse,
    VideoProcessingOptions,
    VideoProcessingResult,
    DetectionHealthResponse,
)

logger = logging.getLogger("safesync.api.detection")

router = APIRouter(prefix="/api/detection", tags=["Detection"])

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
MAX_IMAGE_SIZE_BYTES = 20 * 1024 * 1024   # 20 MB
MAX_VIDEO_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB


@router.get("/health", response_model=DetectionHealthResponse, status_code=status.HTTP_200_OK)
def detection_health():
    """Returns the initialization and operational status of the AI detection engine."""
    loader = ModelLoader.get_instance()
    try:
        is_loaded = loader.is_loaded()
        if not is_loaded:
            # Attempt loading
            loader.load_model()
            is_loaded = loader.is_loaded()

        return DetectionHealthResponse(
            model_loaded=is_loaded,
            model_version=loader.config.get("model", {}).get("name", "ppe_fire_smoke_v1"),
            model_path=loader.model_path or "",
            device=loader.device,
            class_count=len(loader.classes),
            classes={int(k): str(v) for k, v in loader.classes.items()},
            status="healthy" if is_loaded else "unhealthy",
        )
    except Exception as e:
        logger.error(f"Detection engine health check failed: {e}", exc_info=True)
        return DetectionHealthResponse(
            model_loaded=False,
            model_version="unavailable",
            model_path="",
            device="none",
            class_count=0,
            classes={},
            status="unhealthy",
            error="Detection model unavailable",
        )


@router.post("/image", response_model=ImageDetectionResponse, status_code=status.HTTP_200_OK)
async def detect_image(
    file: UploadFile = File(..., description="Image file (JPG, PNG, WebP)"),
    confidence: float = Form(0.25, ge=0.01, le=1.0, description="Confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class filter (e.g. 'person,helmet')"),
):
    """
    Executes object detection on an uploaded image file.
    Returns structured detection bounding boxes, confidence scores, and latency.
    """
    # 1. Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image format '{ext}'. Allowed extensions: {list(ALLOWED_IMAGE_EXTENSIONS)}",
        )

    # 2. Read contents and validate size
    try:
        contents = await file.read()
    except Exception as e:
        logger.error(f"Failed to read image upload: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not read uploaded image data.")

    if len(contents) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty (0 bytes).")

    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image size ({len(contents) / (1024*1024):.1f} MB) exceeds maximum allowed limit of 20 MB.",
        )

    # 3. Parse optional class filter
    class_filter_list = [c.strip().lower() for c in classes.split(",") if c.strip()] if classes else None

    # 4. Execute detection
    try:
        detector = Detector()
        response, _ = detector.detect_image(
            image_input=contents,
            conf=confidence,
            classes_filter=class_filter_list,
            annotate=False,
        )
        return response
    except ValueError as e:
        logger.warning(f"Image validation/decoding error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Corrupted or unreadable image file. Unable to decode image format.",
        )
    except Exception as e:
        logger.error(f"Inference error during image detection: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while executing detection inference. Please check server logs.",
        )


@router.post("/video", response_model=VideoProcessingResult, status_code=status.HTTP_200_OK)
async def detect_video(
    file: UploadFile = File(..., description="Video file (MP4, AVI, MOV)"),
    confidence: float = Form(0.25, ge=0.01, le=1.0, description="Confidence threshold"),
    skip_frames: int = Form(0, ge=0, le=10, description="Frame skipping stride"),
    classes: Optional[str] = Form(None, description="Comma-separated class filter"),
):
    """
    Processes an uploaded video file through the object detection pipeline.
    Returns processing metrics, detection counts, and output video reference.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video format '{ext}'. Allowed: {list(ALLOWED_VIDEO_EXTENSIONS)}",
        )

    try:
        contents = await file.read()
    except Exception as e:
        logger.error(f"Failed to read video upload: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not read uploaded video data.")

    if len(contents) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty (0 bytes).")

    if len(contents) > MAX_VIDEO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Video size ({len(contents) / (1024*1024):.1f} MB) exceeds maximum allowed limit of 100 MB.",
        )

    class_filter_list = [c.strip().lower() for c in classes.split(",") if c.strip()] if classes else None

    # Save to a temporary file
    temp_dir = tempfile.mkdtemp(prefix="safesync_upload_")
    temp_input_path = os.path.join(temp_dir, f"input{ext}")

    try:
        with open(temp_input_path, "wb") as f:
            f.write(contents)

        options = VideoProcessingOptions(
            confidence_threshold=confidence,
            skip_frames=skip_frames,
            classes_filter=class_filter_list,
            save_video=True,
        )

        processor = VideoProcessor()
        result = processor.process_video(video_path=temp_input_path, options=options)

        if not result.success:
            logger.error(f"Video processing failed: {result.error_message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Video processing failure: {result.error_message}",
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video inference exception: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during video inference. Please check server logs.",
        )
    finally:
        # Cleanup temporary input upload
        if os.path.isfile(temp_input_path):
            try:
                os.remove(temp_input_path)
            except Exception:
                pass
        try:
            os.rmdir(temp_dir)
        except Exception:
            pass
