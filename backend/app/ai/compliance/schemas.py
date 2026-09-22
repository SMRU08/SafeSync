"""
schemas.py — RAKSHYA VISION Phase 5
Pydantic v2 schemas for Worker Tracking, Spatial PPE Association, and Compliance Evaluation.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, computed_field


class PPEItemType(str, Enum):
    HELMET = "helmet"
    SAFETY_VEST = "safety_vest"
    GLOVES = "gloves"
    SAFETY_FOOTWEAR = "safety_footwear"


class PPEState(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    UNKNOWN = "UNKNOWN"


class OverallComplianceState(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    UNKNOWN = "UNKNOWN"


class WorkerBoundingBox(BaseModel):
    x1: int = Field(..., description="Left coordinate")
    y1: int = Field(..., description="Top coordinate")
    x2: int = Field(..., description="Right coordinate")
    y2: int = Field(..., description="Bottom coordinate")

    @property
    def width(self) -> int:
        return max(0, self.x2 - self.x1)

    @property
    def height(self) -> int:
        return max(0, self.y2 - self.y1)

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0


class PPEObservation(BaseModel):
    item_type: PPEItemType
    state: PPEState = PPEState.UNKNOWN
    confidence: Optional[float] = None
    bbox: Optional[WorkerBoundingBox] = None
    consecutive_seen: int = 0
    consecutive_missed: int = 0
    evidence_ratio: float = 0.0
    is_occluded: bool = False
    details: Optional[str] = None


class WorkerTrack(BaseModel):
    track_id: int = Field(..., description="Anonymous temporary worker track ID")
    bbox: WorkerBoundingBox
    confidence: float
    ppe: Dict[str, PPEState] = Field(default_factory=dict)
    ppe_details: Dict[str, PPEObservation] = Field(default_factory=dict)
    overall_status: OverallComplianceState = OverallComplianceState.UNKNOWN
    history_length: int = 1
    is_partially_occluded: bool = False

    @computed_field
    @property
    def ppe_status(self) -> Dict[str, str]:
        """Frontend-compatible dictionary mapping of gear states."""
        res = {}
        for item in ["helmet", "safety_vest", "gloves", "safety_footwear"]:
            val = self.ppe.get(item, PPEState.UNKNOWN)
            res[item] = val.value if hasattr(val, "value") else str(val)
        return res

    @computed_field
    @property
    def overall_compliant(self) -> bool:
        """Frontend-compatible boolean compliance flag."""
        return self.overall_status == OverallComplianceState.COMPLIANT

    @computed_field
    @property
    def active_frames(self) -> int:
        """Frontend-compatible frame persistence count."""
        return self.history_length


class ComplianceSummary(BaseModel):
    total_workers: int = 0
    compliant_workers: int = 0
    non_compliant_workers: int = 0
    unknown_workers: int = 0


class ComplianceAnalysisResponse(BaseModel):
    frame_id: Optional[int] = None
    timestamp_utc: str
    workers: List[WorkerTrack] = Field(default_factory=list)
    summary: ComplianceSummary = Field(default_factory=ComplianceSummary)
    unassociated_ppe_count: int = 0
    environmental_hazards: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Active fire and smoke detections passed through without marking PPE violations"
    )
    annotated_image_base64: Optional[str] = None


class VideoComplianceResult(BaseModel):
    video_path: str
    output_video_path: Optional[str] = None
    total_frames: int
    processed_frames: int
    unique_tracks_count: int
    average_track_duration_frames: float
    final_compliance_summary: ComplianceSummary
    processing_fps: float
    mean_latency_ms: float
    tracking_metrics_path: Optional[str] = None
