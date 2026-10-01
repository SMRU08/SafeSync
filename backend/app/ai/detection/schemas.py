"""
schemas.py — SafeSync Phase 4
Structured schemas for detection results, API responses, and processing options.
Strictly decoupled from compliance logic and worker IDs (deferred to Phase 5).
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Normalized or pixel coordinates for a single detection box."""
    x1: float = Field(..., description="Top-left X coordinate in pixels")
    y1: float = Field(..., description="Top-left Y coordinate in pixels")
    x2: float = Field(..., description="Bottom-right X coordinate in pixels")
    y2: float = Field(..., description="Bottom-right Y coordinate in pixels")

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def area(self) -> float:
        return self.width * self.height


class DetectionObject(BaseModel):
    """Structured detection object representing a single model prediction."""
    class_id: int = Field(..., ge=0, description="0..6 canonical class ID")
    class_name: str = Field(..., description="Canonical class name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    bbox: BoundingBox = Field(..., description="Bounding box pixel coordinates")


class ImageDetectionResponse(BaseModel):
    """API response model for single image detection."""
    success: bool = True
    detections: List[DetectionObject] = Field(default_factory=list)
    total_detections: int = 0
    inference_time_ms: float = 0.0
    image_width: int = 0
    image_height: int = 0
    model_version: str = "ppe_fire_smoke_v1"
    device: str = "cpu"
    class_counts: Dict[str, int] = Field(default_factory=dict)
    raw_detections: List[Dict[str, Any]] = Field(default_factory=list, description="Raw model detections before filtering")


class VideoProcessingOptions(BaseModel):
    """Configuration options for processing a video file or stream."""
    confidence_threshold: float = Field(0.25, ge=0.01, le=1.0)
    iou_threshold: float = Field(0.45, ge=0.01, le=1.0)
    image_size: int = Field(384, ge=128, le=1280)
    device: str = "auto"
    skip_frames: int = Field(0, ge=0, description="0=process every frame, 1=every 2nd, etc.")
    classes_filter: Optional[List[str]] = Field(default=None, description="Optional class filter")
    save_video: bool = True
    output_path: Optional[str] = None


class VideoProcessingResult(BaseModel):
    """Summary of complete video inference run."""
    success: bool = True
    input_video: str = ""
    output_video_path: Optional[str] = None
    video_width: int = 0
    video_height: int = 0
    total_source_frames: int = 0
    processed_frames: int = 0
    skipped_frames: int = 0
    corrupted_frames: int = 0
    total_detections: int = 0
    class_detection_counts: Dict[str, int] = Field(default_factory=dict)
    input_fps: float = 0.0
    processing_fps: float = 0.0
    inference_fps: float = 0.0
    mean_inference_latency_ms: float = 0.0
    total_processing_time_s: float = 0.0
    device: str = "cpu"
    error_message: Optional[str] = None


class DetectionHealthResponse(BaseModel):
    """Health status of the detection subsystem."""
    model_loaded: bool = False
    model_version: str = ""
    model_path: str = ""
    device: str = ""
    class_count: int = 0
    classes: Dict[int, str] = Field(default_factory=dict)
    status: str = "healthy"
    error: Optional[str] = None
