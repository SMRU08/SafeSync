"""
schemas.py — SafeSync Phase 6 v2
Pydantic schemas for Fire & Smoke Hazard Analysis.

Extended HazardState with a 7-state pipeline:
  NO_HAZARD → CANDIDATE → DETECTING → CONFIRMED → ACTIVE → CLEARING → CLEARED

Only CONFIRMED / ACTIVE states generate emergency incidents.
CANDIDATE and DETECTING are internal validation stages — no alerts.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HazardType(str, Enum):
    FIRE = "fire"
    SMOKE = "smoke"


class HazardState(str, Enum):
    """
    Seven-stage temporal hazard state machine with backward compatibility for SUSPECTED.
    """
    NO_HAZARD = "NO_HAZARD"
    CANDIDATE = "CANDIDATE"
    SUSPECTED = "SUSPECTED"  # Backward compatibility alias for CANDIDATE/DETECTING
    DETECTING = "DETECTING"
    CONFIRMED = "CONFIRMED"
    ACTIVE = "ACTIVE"
    CLEARING = "CLEARING"
    CLEARED = "CLEARED"


# ── State ordering for severity comparison ──────────────────────────────────
HAZARD_STATE_SEVERITY: Dict[str, int] = {
    HazardState.CONFIRMED: 7,
    HazardState.ACTIVE: 6,
    HazardState.CLEARING: 5,
    HazardState.DETECTING: 4,
    HazardState.SUSPECTED: 4,
    HazardState.CANDIDATE: 3,
    HazardState.CLEARED: 2,
    HazardState.NO_HAZARD: 1,
}


def is_alert_state(state: HazardState) -> bool:
    """True only for states that should trigger emergency alerts."""
    return state in (HazardState.CONFIRMED, HazardState.ACTIVE)


class HazardRelationship(str, Enum):
    NO_HAZARD = "NO_HAZARD"
    FIRE_ONLY = "FIRE_ONLY"
    SMOKE_ONLY = "SMOKE_ONLY"
    FIRE_AND_SMOKE = "FIRE_AND_SMOKE"


class HazardBoundingBox(BaseModel):
    x1: float = Field(..., description="Left pixel coordinate")
    y1: float = Field(..., description="Top pixel coordinate")
    x2: float = Field(..., description="Right pixel coordinate")
    y2: float = Field(..., description="Bottom pixel coordinate")
    center_x: float = Field(..., description="Center X coordinate")
    center_y: float = Field(..., description="Center Y coordinate")
    area: float = Field(..., description="Bounding box area in square pixels")

    @classmethod
    def from_xyxy(cls, x1: float, y1: float, x2: float, y2: float) -> "HazardBoundingBox":
        w = max(0.0, x2 - x1)
        h = max(0.0, y2 - y1)
        return cls(
            x1=float(x1),
            y1=float(y1),
            x2=float(x2),
            y2=float(y2),
            center_x=float(x1 + w / 2.0),
            center_y=float(y1 + h / 2.0),
            area=float(w * h),
        )


class HazardObservationSchema(BaseModel):
    """Single-frame detection observation."""
    hazard_type: HazardType
    confidence: float
    bbox: HazardBoundingBox
    frame_number: Optional[int] = None
    timestamp: str
    camera_id: str = "camera_01"
    zone_id: str = "UNKNOWN"


class HazardEventDetail(BaseModel):
    """Aggregated tracking and temporal state for an anonymous hazard event."""
    event_id: str = Field(..., description="Anonymous hazard identifier, e.g. HAZARD-0001")
    hazard_type: HazardType
    state: HazardState
    camera_id: str = "camera_01"
    zone_id: str = "UNKNOWN"
    confidence: float = Field(..., description="Current/latest detection confidence")
    average_confidence: float
    max_confidence: float
    validated_confidence: float = Field(
        default=0.0,
        description="Confirmation-weighted confidence: average_confidence * persistence_ratio"
    )
    bbox: HazardBoundingBox
    first_seen: str
    last_seen: str
    duration_seconds: float = 0.0
    detection_count: int = 1
    persistence_ratio: float = Field(..., description="Ratio of detected frames to total observed frames")
    frames_detected: int
    frames_missed: int
    spatial_consistency_score: float = Field(
        default=1.0,
        description="0-1 score of spatial coherence across frames (1=perfectly stable, 0=random)"
    )
    # Raw fields for diagnostics
    raw_model_confidence: float = Field(
        default=0.0,
        description="Raw latest YOLO model confidence (unfiltered)"
    )
    temporal_score: float = Field(
        default=0.0,
        description="persistence_ratio used in temporal validation"
    )
    final_hazard_state: str = Field(
        default="",
        description="String value of the resolved state for API consumers"
    )


class HazardAnalysisResponse(BaseModel):
    """Response schema for single frame or real-time stream analysis."""
    frame_id: int
    timestamp_utc: str
    camera_id: str
    zone_id: str
    scene_hazard_state: HazardState = Field(
        ..., description="Overall scene state across all active tracks"
    )
    relationship: HazardRelationship = Field(
        ..., description="Observation category: NO_HAZARD, FIRE_ONLY, SMOKE_ONLY, FIRE_AND_SMOKE"
    )
    hazards: List[HazardEventDetail] = Field(default_factory=list)
    total_active_hazards: int = 0
    annotated_image_base64: Optional[str] = None


class VideoHazardResult(BaseModel):
    """Metrics and artifacts from processing an entire video for hazards."""
    video_path: str
    output_video_path: str
    total_frames: int
    processed_frames: int
    total_fire_events: int
    total_smoke_events: int
    confirmed_events: int
    suspected_events: int
    cleared_events: int
    processing_fps: float
    mean_latency_ms: float
    benchmark_path: Optional[str] = None
