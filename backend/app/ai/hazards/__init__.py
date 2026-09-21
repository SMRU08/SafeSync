"""
Fire and Smoke Hazard Analysis Package — RAKSHYA VISION Phase 6
"""

try:
    from app.ai.hazards.schemas import (
        HazardType,
        HazardState,
        HazardRelationship,
        HazardBoundingBox,
        HazardObservationSchema,
        HazardEventDetail,
        HazardAnalysisResponse,
        VideoHazardResult,
    )
    from app.ai.hazards.tracker import SpatialHazardTracker, HazardTrack
    from app.ai.hazards.temporal import TemporalHazardStateMachine
    from app.ai.hazards.zones import ZoneManager
    from app.ai.hazards.visualizer import HazardVisualizer
    from app.ai.hazards.hazard_engine import HazardAnalysisEngine, load_hazard_config
    from app.ai.hazards.video_hazard import process_hazard_video
except ImportError:
    from backend.app.ai.hazards.schemas import (
        HazardType,
        HazardState,
        HazardRelationship,
        HazardBoundingBox,
        HazardObservationSchema,
        HazardEventDetail,
        HazardAnalysisResponse,
        VideoHazardResult,
    )
    from backend.app.ai.hazards.tracker import SpatialHazardTracker, HazardTrack
    from backend.app.ai.hazards.temporal import TemporalHazardStateMachine
    from backend.app.ai.hazards.zones import ZoneManager
    from backend.app.ai.hazards.visualizer import HazardVisualizer
    from backend.app.ai.hazards.hazard_engine import HazardAnalysisEngine, load_hazard_config
    from backend.app.ai.hazards.video_hazard import process_hazard_video

__all__ = [
    "HazardType",
    "HazardState",
    "HazardRelationship",
    "HazardBoundingBox",
    "HazardObservationSchema",
    "HazardEventDetail",
    "HazardAnalysisResponse",
    "VideoHazardResult",
    "SpatialHazardTracker",
    "HazardTrack",
    "TemporalHazardStateMachine",
    "ZoneManager",
    "HazardVisualizer",
    "HazardAnalysisEngine",
    "load_hazard_config",
    "process_hazard_video",
]
