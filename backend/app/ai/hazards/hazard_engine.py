"""
hazard_engine.py — RAKSHYA VISION Phase 6
Integrated Fire and Smoke Hazard Analysis Engine.
Extracts fire and smoke detections, tracks spatial hazard events, evaluates temporal states,
associates camera/zone metadata, and renders visual annotations.
Strictly decoupled from PPE compliance and risk scoring.
"""

import os
import yaml
import base64
import time
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional, Any
import numpy as np

try:
    from app.ai.detection.detector import Detector
    from app.ai.detection.model_loader import ModelLoader
    from app.ai.detection.utils import bytes_to_bgr_image, bgr_to_jpeg_bytes
    from app.ai.hazards.schemas import (
        HazardType,
        HazardState,
        HazardRelationship,
        HazardBoundingBox,
        HazardEventDetail,
        HazardAnalysisResponse,
    )
    from app.ai.hazards.tracker import SpatialHazardTracker, HazardTrack
    from app.ai.hazards.temporal import TemporalHazardStateMachine
    from app.ai.hazards.zones import ZoneManager
    from app.ai.hazards.visualizer import HazardVisualizer
except ImportError:
    from backend.app.ai.detection.detector import Detector
    from backend.app.ai.detection.model_loader import ModelLoader
    from backend.app.ai.detection.utils import bytes_to_bgr_image, bgr_to_jpeg_bytes
    from backend.app.ai.hazards.schemas import (
        HazardType,
        HazardState,
        HazardRelationship,
        HazardBoundingBox,
        HazardEventDetail,
        HazardAnalysisResponse,
    )
    from backend.app.ai.hazards.tracker import SpatialHazardTracker, HazardTrack
    from backend.app.ai.hazards.temporal import TemporalHazardStateMachine
    from backend.app.ai.hazards.zones import ZoneManager
    from backend.app.ai.hazards.visualizer import HazardVisualizer


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DEFAULT_HAZARD_CONFIG = os.path.join(ROOT, "configs", "hazard.yaml")


def load_hazard_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    path = config_path or DEFAULT_HAZARD_CONFIG
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


class HazardAnalysisEngine:
    """
    Master engine for Fire & Smoke hazard detection, tracking, and temporal evaluation.
    """

    def __init__(
        self,
        hazard_config_path: Optional[str] = None,
        camera_config_path: Optional[str] = None,
        model_loader: Optional[ModelLoader] = None,
    ):
        self.config = load_hazard_config(hazard_config_path)

        # Initialize detector with decoupled hazard model
        self.detector = Detector(model_loader, model_type="hazards")

        # Detection thresholds
        h_cfg = self.config.get("hazard", {})
        self.default_conf = float(h_cfg.get("confidence_threshold", 0.25))
        self.fire_conf = float(h_cfg.get("fire_confidence", self.default_conf))
        self.smoke_conf = float(h_cfg.get("smoke_confidence", self.default_conf))

        # Initialize subcomponents
        self.zone_manager = ZoneManager(camera_config_path)
        self.tracker = SpatialHazardTracker(self.config)
        self.state_machine = TemporalHazardStateMachine(self.config)
        self.visualizer = HazardVisualizer(show_hud=True)

        self.frame_counter = 0

    def reset(self):
        """Resets tracking and temporal state for a new video or camera session."""
        self.tracker.reset()
        self.state_machine.reset()
        self.frame_counter = 0

    def process_frame(
        self,
        frame: np.ndarray,
        camera_id: str = "camera_01",
        confidence_override: Optional[float] = None,
        annotate: bool = True,
    ) -> Tuple[HazardAnalysisResponse, np.ndarray, Dict[str, float]]:
        """
        Processes a single video or camera frame for fire and smoke hazards.

        Returns:
            - HazardAnalysisResponse
            - annotated_frame (or original if annotate=False)
            - latency breakdown dict (detect_ms, track_ms, temporal_ms, total_ms)
        """
        t_start = time.perf_counter()
        self.frame_counter += 1
        h, w = frame.shape[:2]

        # 1. Detection Stage
        t0 = time.perf_counter()
        min_conf = confidence_override or min(self.fire_conf, self.smoke_conf)
        det_response, _ = self.detector.detect_image(
            frame,
            conf=min_conf,
            annotate=False,
        )
        t_detect = (time.perf_counter() - t0) * 1000.0

        # Filter strictly for fire (class 5) and smoke (class 6)
        hazard_dets = []
        for obj in det_response.detections:
            cname = obj.class_name.lower()
            if cname not in ["fire", "smoke"]:
                continue

            htype = HazardType.FIRE if cname == "fire" else HazardType.SMOKE
            req_conf = confidence_override or (self.fire_conf if htype == HazardType.FIRE else self.smoke_conf)
            if obj.confidence < req_conf:
                continue

            cx = (obj.bbox.x1 + obj.bbox.x2) / 2.0
            cy = (obj.bbox.y1 + obj.bbox.y2) / 2.0
            zone_id = self.zone_manager.resolve_zone(
                camera_id=camera_id,
                center_x=cx,
                center_y=cy,
                frame_width=w,
                frame_height=h,
            )

            hazard_dets.append({
                "hazard_type": htype,
                "confidence": float(obj.confidence),
                "bbox": [obj.bbox.x1, obj.bbox.y1, obj.bbox.x2, obj.bbox.y2],
                "zone_id": zone_id,
            })

        # 2. Spatial Tracking Stage
        t1 = time.perf_counter()
        active_tracks = self.tracker.update(
            hazard_detections=hazard_dets,
            frame_idx=self.frame_counter,
            camera_id=camera_id,
            frame_shape=(h, w),
        )
        t_track = (time.perf_counter() - t1) * 1000.0

        # 3. Temporal Validation & State Machine Stage
        t2 = time.perf_counter()
        hazard_details: List[HazardEventDetail] = []

        for trk in active_tracks:
            state = self.state_machine.evaluate_track_state(trk)
            bbox_schema = HazardBoundingBox.from_xyxy(
                trk.last_bbox[0], trk.last_bbox[1], trk.last_bbox[2], trk.last_bbox[3]
            )
            detail = HazardEventDetail(
                event_id=trk.event_id,
                hazard_type=trk.hazard_type,
                state=state,
                camera_id=trk.camera_id,
                zone_id=trk.zone_id,
                confidence=trk.last_confidence,
                bbox=bbox_schema,
                first_seen=trk.first_seen.isoformat(),
                last_seen=trk.last_seen.isoformat(),
                duration_seconds=trk.duration_seconds,
                detection_count=trk.detection_count,
                average_confidence=round(trk.average_confidence, 4),
                max_confidence=round(trk.max_confidence, 4),
                persistence_ratio=round(trk.persistence_ratio, 4),
                frames_detected=trk.detection_count,
                frames_missed=trk.missed_frames,
            )
            hazard_details.append(detail)

        scene_state = self.state_machine.evaluate_overall_scene_state(active_tracks)
        relationship = self.state_machine.evaluate_scene_relationship(active_tracks)
        t_temp = (time.perf_counter() - t2) * 1000.0

        total_ms = (time.perf_counter() - t_start) * 1000.0
        latencies = {
            "detect_ms": round(t_detect, 2),
            "track_ms": round(t_track, 2),
            "temporal_ms": round(t_temp, 2),
            "total_ms": round(total_ms, 2),
        }

        # 4. Visualization Stage
        cam_name = self.zone_manager.get_camera_name(camera_id)
        zone_name = self.zone_manager.get_zone_name(
            hazard_details[0].zone_id if hazard_details else "UNKNOWN"
        )
        if annotate:
            fps_val = 1000.0 / total_ms if total_ms > 0 else 0.0
            annotated_frame = self.visualizer.draw_hazards(
                frame=frame,
                hazard_events=hazard_details,
                scene_state=scene_state,
                camera_name=cam_name,
                zone_name=zone_name,
                relationship=relationship.value,
                fps=fps_val,
                latency_ms=total_ms,
            )
            jpeg_bytes = bgr_to_jpeg_bytes(annotated_frame)
            b64_img = base64.b64encode(jpeg_bytes).decode("utf-8")
        else:
            annotated_frame = frame
            b64_img = None

        response = HazardAnalysisResponse(
            frame_id=self.frame_counter,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            camera_id=camera_id,
            zone_id=hazard_details[0].zone_id if hazard_details else "UNKNOWN",
            scene_hazard_state=scene_state,
            relationship=relationship,
            hazards=hazard_details,
            total_active_hazards=len(hazard_details),
            annotated_image_base64=b64_img,
        )

        return response, annotated_frame, latencies
