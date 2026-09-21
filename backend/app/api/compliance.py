"""
compliance.py — RAKSHYA VISION Phase 5
FastAPI Router for Worker Tracking, Spatial PPE Association & Compliance Analysis.
"""

import os
import cv2
import tempfile
import logging
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Query, HTTPException, status
from fastapi.responses import JSONResponse

try:
    from app.ai.detection.utils import bytes_to_bgr_image
    from app.ai.compliance.compliance_engine import WorkerComplianceEngine, load_compliance_config
    from app.ai.compliance.schemas import (
        ComplianceAnalysisResponse,
        VideoComplianceResult,
    )
    from app.ai.compliance.video_compliance import process_compliance_video
except ImportError:
    from backend.app.ai.detection.utils import bytes_to_bgr_image
    from backend.app.ai.compliance.compliance_engine import WorkerComplianceEngine, load_compliance_config
    from backend.app.ai.compliance.schemas import (
        ComplianceAnalysisResponse,
        VideoComplianceResult,
    )
    from backend.app.ai.compliance.video_compliance import process_compliance_video

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compliance", tags=["Worker Tracking & PPE Compliance"])

# Singleton engine instance
_engine_instance: Optional[WorkerComplianceEngine] = None


def get_compliance_engine() -> WorkerComplianceEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = WorkerComplianceEngine()
    return _engine_instance


@router.get("/config")
def get_compliance_configuration():
    """Returns active PPE compliance policies, tracking parameters, and association thresholds."""
    config = load_compliance_config()
    return {
        "status": "active",
        "policy": config.get("required_ppe", {}),
        "tracking": config.get("tracking", {}),
        "association": config.get("association", {}),
        "temporal": config.get("temporal", {}),
    }


@router.post("/analyze", response_model=ComplianceAnalysisResponse)
async def analyze_frame(
    file: UploadFile = File(..., description="Image or frame to analyze for worker PPE compliance"),
    confidence: float = Query(0.25, ge=0.01, le=1.0, description="Detection confidence threshold"),
    annotate: bool = Query(True, description="Whether to include annotated base64 visualization"),
):
    """
    Analyzes a single frame: detects workers, tracks IDs, associates PPE items,
    evaluates temporal compliance states, and renders compliance checklist HUD.
    """
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{file.content_type}'. Must be JPEG, PNG, or WEBP.",
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    image = bytes_to_bgr_image(file_bytes)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to decode image. File may be corrupted.",
        )

    engine = get_compliance_engine()
    response, _, latencies = engine.process_frame(
        image,
        confidence_threshold=confidence,
        annotate=annotate,
    )
    return response


@router.post("/video", response_model=VideoComplianceResult)
async def analyze_video(
    file: UploadFile = File(..., description="Video file to process for worker tracking and compliance"),
    confidence: float = Query(0.25, ge=0.01, le=1.0),
    skip_frames: int = Query(0, ge=0, le=10),
):
    """
    Processes an uploaded video through the end-to-end worker tracking and compliance pipeline.
    """
    allowed_exts = {".mp4", ".avi", ".mov", ".mkv"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported video extension '{ext}'. Must be .mp4, .avi, or .mov.",
        )

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_in:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded video file is empty (0 bytes).",
            )
        tmp_in.write(content)
        temp_input_path = tmp_in.name

    try:
        output_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "outputs", "compliance", "videos")
        )
        os.makedirs(output_dir, exist_ok=True)
        out_name = f"compliance_{os.path.basename(temp_input_path)}"
        output_video_path = os.path.join(output_dir, out_name)

        result = process_compliance_video(
            input_path=temp_input_path,
            output_path=output_video_path,
            confidence=confidence,
            skip_frames=skip_frames,
        )
        return result
    finally:
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
