"""
schemas.py — RAKSHYA VISION Phase 6
Pydantic schemas for Fire & Smoke Hazard Analysis.
Strictly decoupled from PPE compliance and risk scoring.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HazardType(str, Enum):
    FIRE = "fire"
    SMOKE = "smoke"


class HazardState(str, Enum):
    NO_HAZARD = "NO_HAZARD"
    SUSPECTED = "SUSPECTED"
    CONFIRMED = "CONFIRMED"
    CLEARED = "CLEARED"


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
    confidence: float = Field(..., description="Current/latest confidence score")
    bbox: HazardBoundingBox
    first_seen: str
    last_seen: str
    duration_seconds: float = 0.0
    detection_count: int = 1
    average_confidence: float
    max_confidence: float
    persistence_ratio: float = Field(..., description="Ratio of detected frames to total observed frames")
    frames_detected: int
    frames_missed: int


class HazardAnalysisResponse(BaseModel):
    """Response schema for single frame or real-time stream analysis."""
    frame_id: int
    timestamp_utc: str
    camera_id: str
    zone_id: str
    scene_hazard_state: HazardState = Field(
        ..., description="Overall scene state: NO_HAZARD, SUSPECTED, CONFIRMED, CLEARED"
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
