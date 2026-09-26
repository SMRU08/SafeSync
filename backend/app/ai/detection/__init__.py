"""
__init__.py — SafeSync Detection Subsystem (Phase 4)
Exposes the public interfaces: Detector, ModelLoader, FrameProcessor, VideoProcessor, schemas.
"""

try:
    from app.ai.detection.model_loader import ModelLoader
    from app.ai.detection.detector import Detector
    from app.ai.detection.frame_processor import FrameProcessor
    from app.ai.detection.video_processor import VideoProcessor
    from app.ai.detection.schemas import (
        BoundingBox,
        DetectionObject,
        ImageDetectionResponse,
        VideoProcessingOptions,
        VideoProcessingResult,
        DetectionHealthResponse,
    )
except ImportError:
    from backend.app.ai.detection.model_loader import ModelLoader
    from backend.app.ai.detection.detector import Detector
    from backend.app.ai.detection.frame_processor import FrameProcessor
    from backend.app.ai.detection.video_processor import VideoProcessor
    from backend.app.ai.detection.schemas import (
        BoundingBox,
        DetectionObject,
        ImageDetectionResponse,
        VideoProcessingOptions,
        VideoProcessingResult,
        DetectionHealthResponse,
    )

__all__ = [
    "ModelLoader",
    "Detector",
    "FrameProcessor",
    "VideoProcessor",
    "BoundingBox",
    "DetectionObject",
    "ImageDetectionResponse",
    "VideoProcessingOptions",
    "VideoProcessingResult",
    "DetectionHealthResponse",
]
