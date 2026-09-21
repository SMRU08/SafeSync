"""
hazards.py — RAKSHYA VISION Phase 6
FastAPI Router for Fire and Smoke Hazard Analysis.
Exposes endpoints for frame analysis, event history, and hazard configuration.
Strictly decoupled from notifications, alerts, and risk scoring.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Query, Path, HTTPException, Depends, status
from sqlalchemy.orm import Session

try:
    from app.database.session import get_db
    from app.models.hazard import HazardEvent, HazardObservation
    from app.ai.detection.utils import bytes_to_bgr_image
    from app.ai.hazards.hazard_engine import HazardAnalysisEngine, load_hazard_config
    from app.ai.hazards.schemas import (
        HazardAnalysisResponse,
        HazardEventDetail,
        HazardState,
        HazardType,
        HazardBoundingBox,
    )
except ImportError:
    from backend.app.database.session import get_db
    from backend.app.models.hazard import HazardEvent, HazardObservation
    from backend.app.ai.detection.utils import bytes_to_bgr_image
    from backend.app.ai.hazards.hazard_engine import HazardAnalysisEngine, load_hazard_config
    from backend.app.ai.hazards.schemas import (
        HazardAnalysisResponse,
        HazardEventDetail,
        HazardState,
        HazardType,
        HazardBoundingBox,
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hazards", tags=["Fire & Smoke Hazard Analysis"])

_engine_instance: Optional[HazardAnalysisEngine] = None


def get_hazard_engine() -> HazardAnalysisEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = HazardAnalysisEngine()
    return _engine_instance


@router.get("/config")
def get_hazard_configuration():
    """Returns the active fire & smoke parameters, temporal thresholds, and zone definitions."""
    engine = get_hazard_engine()
    cfg = engine.config
    return {
        "status": "active",
        "hazard_thresholds": cfg.get("hazard", {}),
        "tracking": cfg.get("tracking", {}),
        "zones_enabled": cfg.get("zones", {}).get("enabled", True),
        "cameras": list(engine.zone_manager.cameras.keys()),
        "configured_zones": list(engine.zone_manager.zones.keys()),
    }


@router.post("/analyze", response_model=HazardAnalysisResponse)
async def analyze_frame(
    file: UploadFile = File(..., description="Image or video frame to analyze for fire/smoke hazards"),
    camera_id: str = Query("camera_01", description="Camera identifier"),
    confidence: Optional[float] = Query(None, ge=0.01, le=1.0, description="Optional confidence override"),
    annotate: bool = Query(True, description="Whether to generate base64 annotated image"),
    db: Session = Depends(get_db),
):
    """
    Analyzes an uploaded image or frame for fire and smoke hazards,
    tracks events spatially, evaluates temporal states, and records observations.
    """
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported media type '{file.content_type}'. Must be JPEG, PNG, or WEBP.",
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

    engine = get_hazard_engine()
    response, _, _ = engine.process_frame(
        frame=image,
        camera_id=camera_id,
        confidence_override=confidence,
        annotate=annotate,
    )

    # Persist active hazard events to database
    try:
        for h in response.hazards:
            db_event = db.query(HazardEvent).filter(HazardEvent.event_id == h.event_id).first()
            if not db_event:
                db_event = HazardEvent(
                    event_id=h.event_id,
                    hazard_type=h.hazard_type.value,
                    state=h.state.value,
                    camera_id=h.camera_id,
                    zone_id=h.zone_id,
                    duration_seconds=h.duration_seconds,
                    detection_count=h.detection_count,
                    average_confidence=h.average_confidence,
                    max_confidence=h.max_confidence,
                )
                db.add(db_event)
                db.flush()
            else:
                db_event.state = h.state.value
                db_event.duration_seconds = h.duration_seconds
                db_event.detection_count = h.detection_count
                db_event.average_confidence = h.average_confidence
                db_event.max_confidence = h.max_confidence

            obs = HazardObservation(
                hazard_event_id=db_event.id,
                event_id=h.event_id,
                frame_number=response.frame_id,
                hazard_type=h.hazard_type.value,
                confidence=h.confidence,
                x1=h.bbox.x1,
                y1=h.bbox.y1,
                x2=h.bbox.x2,
                y2=h.bbox.y2,
            )
            db.add(obs)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to persist hazard observations to DB: %s", exc)

    return response


@router.get("", response_model=List[dict])
def list_hazard_events(
    state: Optional[str] = Query(None, description="Filter by state: SUSPECTED, CONFIRMED, CLEARED"),
    hazard_type: Optional[str] = Query(None, description="Filter by type: fire or smoke"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Returns recent hazard events from the database.
    If database has no records, returns currently active engine events.
    """
    query = db.query(HazardEvent)
    if state:
        query = query.filter(HazardEvent.state == state.upper())
    if hazard_type:
        query = query.filter(HazardEvent.hazard_type == hazard_type.lower())

    records = query.order_by(HazardEvent.id.desc()).limit(limit).all()
    if records:
        return [
            {
                "event_id": r.event_id,
                "hazard_type": r.hazard_type,
                "state": r.state,
                "camera_id": r.camera_id,
                "zone_id": r.zone_id,
                "first_seen": r.first_seen.isoformat(),
                "last_seen": r.last_seen.isoformat(),
                "duration_seconds": r.duration_seconds,
                "detection_count": r.detection_count,
                "average_confidence": r.average_confidence,
                "max_confidence": r.max_confidence,
            }
            for r in records
        ]

    # Fallback to in-memory active tracks
    engine = get_hazard_engine()
    results = []
    for t in engine.tracker.active_tracks:
        st = engine.state_machine.event_states.get(t.event_id, HazardState.NO_HAZARD)
        if state and st.value != state.upper():
            continue
        if hazard_type and t.hazard_type.value != hazard_type.lower():
            continue
        results.append({
            "event_id": t.event_id,
            "hazard_type": t.hazard_type.value,
            "state": st.value,
            "camera_id": t.camera_id,
            "zone_id": t.zone_id,
            "first_seen": t.first_seen.isoformat(),
            "last_seen": t.last_seen.isoformat(),
            "duration_seconds": t.duration_seconds,
            "detection_count": t.detection_count,
            "average_confidence": round(t.average_confidence, 4),
            "max_confidence": round(t.max_confidence, 4),
        })
    return results


@router.get("/{event_id}")
def get_hazard_event_detail(
    event_id: str = Path(..., description="Hazard event ID (e.g. HAZARD-0001)"),
    db: Session = Depends(get_db),
):
    """
    Returns full details and historical observations for a specific hazard event.
    """
    db_event = db.query(HazardEvent).filter(HazardEvent.event_id == event_id).first()
    if db_event:
        observations = [
            {
                "frame_number": o.frame_number,
                "timestamp": o.timestamp.isoformat(),
                "hazard_type": o.hazard_type,
                "confidence": o.confidence,
                "bbox": {"x1": o.x1, "y1": o.y1, "x2": o.x2, "y2": o.y2},
            }
            for o in db_event.observations
        ]
        return {
            "event_id": db_event.event_id,
            "hazard_type": db_event.hazard_type,
            "state": db_event.state,
            "camera_id": db_event.camera_id,
            "zone_id": db_event.zone_id,
            "first_seen": db_event.first_seen.isoformat(),
            "last_seen": db_event.last_seen.isoformat(),
            "duration_seconds": db_event.duration_seconds,
            "detection_count": db_event.detection_count,
            "average_confidence": db_event.average_confidence,
            "max_confidence": db_event.max_confidence,
            "observations": observations,
        }

    # Search in-memory tracks
    engine = get_hazard_engine()
    for t in engine.tracker.active_tracks + engine.tracker.archived_tracks:
        if t.event_id == event_id:
            st = engine.state_machine.event_states.get(t.event_id, HazardState.NO_HAZARD)
            return {
                "event_id": t.event_id,
                "hazard_type": t.hazard_type.value,
                "state": st.value,
                "camera_id": t.camera_id,
                "zone_id": t.zone_id,
                "first_seen": t.first_seen.isoformat(),
                "last_seen": t.last_seen.isoformat(),
                "duration_seconds": t.duration_seconds,
                "detection_count": t.detection_count,
                "average_confidence": round(t.average_confidence, 4),
                "max_confidence": round(t.max_confidence, 4),
                "observations": [],
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Hazard event '{event_id}' not found.",
    )
