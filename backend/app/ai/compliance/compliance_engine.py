"""
compliance_engine.py — SafeSync Phase 5
Integrated Worker Tracking, Spatial PPE Association, and Compliance Engine.
"""

import os
import yaml
import datetime
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

import base64

try:
    from app.ai.detection.detector import Detector
    from app.ai.detection.model_loader import ModelLoader
    from app.ai.detection.utils import bytes_to_bgr_image, bgr_to_jpeg_bytes
    from app.ai.compliance.tracker import ByteTrack
    from app.ai.compliance.association import SpatialPPEAssociator
    from app.ai.compliance.temporal import TemporalComplianceTracker
    from app.ai.compliance.visualizer import ComplianceVisualizer
    from app.ai.compliance.schemas import (
        PPEItemType,
        PPEState,
        OverallComplianceState,
        WorkerTrack,
        ComplianceSummary,
        ComplianceAnalysisResponse,
    )
except ImportError:
    from backend.app.ai.detection.detector import Detector
    from backend.app.ai.detection.model_loader import ModelLoader
    from backend.app.ai.detection.utils import bytes_to_bgr_image, bgr_to_jpeg_bytes
    from backend.app.ai.compliance.tracker import ByteTrack
    from backend.app.ai.compliance.association import SpatialPPEAssociator
    from backend.app.ai.compliance.temporal import TemporalComplianceTracker
    from backend.app.ai.compliance.visualizer import ComplianceVisualizer
    from backend.app.ai.compliance.schemas import (
        PPEItemType,
        PPEState,
        OverallComplianceState,
        WorkerTrack,
        ComplianceSummary,
        ComplianceAnalysisResponse,
    )


def encode_image_base64(image: np.ndarray) -> str:
    try:
        jpeg_bytes = bgr_to_jpeg_bytes(image)
        return base64.b64encode(jpeg_bytes).decode("utf-8")
    except Exception:
        return ""


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
CONFIG_PATH = os.path.join(ROOT, "configs", "compliance.yaml")


def load_compliance_config(path: str = CONFIG_PATH) -> Dict[str, Any]:
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
def deduplicate_entry_gate_detections(detections: List[Any]) -> List[Any]:
    """
    Entry Gate Only: Guarantees that ONE real object receives ONE final bounding box.
    Performs intra-class spatial suppression (IoU >= 0.40 or containment >= 0.70)
    for detections of the same class, retaining only the highest-confidence detection.
    Different classes (Person vs Helmet vs Vest vs Gloves etc.) are NEVER suppressed against each other.
    Distinct workers/objects at different locations remain completely independent.
    """
    if not detections:
        return []

    by_class: Dict[str, List[Any]] = {}
    for d in detections:
        cname = str(getattr(d, "class_name", "")).lower()
        by_class.setdefault(cname, []).append(d)

    deduped: List[Any] = []
    for cname, class_dets in by_class.items():
        if len(class_dets) <= 1:
            deduped.extend(class_dets)
            continue

        # Sort by confidence descending
        sorted_dets = sorted(class_dets, key=lambda x: float(getattr(x, "confidence", 0.0)), reverse=True)
        kept: List[Any] = []

        for cand in sorted_dets:
            cb = getattr(cand, "bbox", None)
            if hasattr(cb, "x1"):
                cx1, cy1, cx2, cy2 = float(cb.x1), float(cb.y1), float(cb.x2), float(cb.y2)
            elif isinstance(cb, (list, tuple)) and len(cb) >= 4:
                cx1, cy1, cx2, cy2 = float(cb[0]), float(cb[1]), float(cb[2]), float(cb[3])
            else:
                kept.append(cand)
                continue

            c_area = max(1.0, float((cx2 - cx1) * (cy2 - cy1)))
            suppressed = False

            for k in kept:
                kb = getattr(k, "bbox", None)
                if hasattr(kb, "x1"):
                    kx1, ky1, kx2, ky2 = float(kb.x1), float(kb.y1), float(kb.x2), float(kb.y2)
                elif isinstance(kb, (list, tuple)) and len(kb) >= 4:
                    kx1, ky1, kx2, ky2 = float(kb[0]), float(kb[1]), float(kb[2]), float(kb[3])
                else:
                    continue

                k_area = max(1.0, float((kx2 - kx1) * (ky2 - ky1)))

                ix1 = max(cx1, kx1)
                iy1 = max(cy1, ky1)
                ix2 = min(cx2, kx2)
                iy2 = min(cy2, ky2)
                iw = max(0.0, ix2 - ix1)
                ih = max(0.0, iy2 - iy1)
                inter = iw * ih

                if inter > 0:
                    union = c_area + k_area - inter
                    iou = inter / union if union > 0 else 0.0
                    containment = inter / min(c_area, k_area)

                    # Same physical object rule:
                    if iou >= 0.40 or containment >= 0.70:
                        suppressed = True
                        break

            if not suppressed:
                kept.append(cand)

        deduped.extend(kept)

    return deduped


class WorkerComplianceEngine:
    """
    End-to-end pipeline orchestrator:
    Frame -> YOLO Detection -> Person Filtering -> ByteTrack Tracking ->
    Spatial PPE Association -> Temporal Compliance Validation -> Visual HUD Rendering.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_compliance_config()

        # Initialize detector
        self.detector = Detector()

        # Initialize ByteTrack
        track_cfg = self.config.get("tracking", {})
        self.tracker = ByteTrack(
            track_high_thresh=track_cfg.get("track_high_thresh", 0.25),
            track_low_thresh=track_cfg.get("track_low_thresh", 0.10),
            new_track_thresh=track_cfg.get("new_track_thresh", 0.35),
            track_buffer=track_cfg.get("track_buffer", 30),
            match_thresh=track_cfg.get("match_thresh", 0.70),
            confirmation_frames=track_cfg.get("confirmation_frames", 2),
            lost_tolerance_frames=track_cfg.get("lost_tolerance_frames", 15),
        )

        # Initialize spatial associator
        self.associator = SpatialPPEAssociator(self.config)

        # Initialize temporal compliance state machine
        self.temporal_tracker = TemporalComplianceTracker(self.config)

        # Initialize visualizer
        self.visualizer = ComplianceVisualizer(show_hud=True)

        self.frame_counter = 0

    def reset(self):
        """Resets tracking state and temporal history."""
        self.tracker.reset()
        self.temporal_tracker.reset()
        self.frame_counter = 0

    def process_frame(
        self,
        frame: np.ndarray,
        confidence_threshold: float = 0.20,
        annotate: bool = True,
        zone_id: str = "UNKNOWN",
        imgsz: Optional[int] = None,
    ) -> Tuple[ComplianceAnalysisResponse, np.ndarray, Dict[str, float]]:
        """
        Processes a single video or camera frame.

        Returns:
            - ComplianceAnalysisResponse
            - annotated_frame (or original if annotate=False)
            - latency_breakdown dict (detection_ms, tracking_ms, association_ms, temporal_ms, total_ms)
        """
        import time
        t_start = time.perf_counter()
        self.frame_counter += 1
        self.temporal_tracker.current_frame = self.frame_counter

        # 1. Detection stage
        t0 = time.perf_counter()
        det_response, _ = self.detector.detect_image(
            frame,
            conf=confidence_threshold,
            imgsz=imgsz,
            annotate=False,
        )
        t_detect = (time.perf_counter() - t0) * 1000.0

        is_entry_gate = (zone_id or "").lower() in ("entry_gate", "entry", "gate")

        # Entry Gate Diagnostic Logging: Raw model candidates
        raw_candidates_count = len(getattr(det_response, "raw_detections", [])) or len(det_response.detections)
        if is_entry_gate:
            import logging
            logging.getLogger("compliance_engine").info("[ENTRY GATE] RAW DETECTIONS: %d", raw_candidates_count)

        # Isolated Entry Gate same-object intra-class deduplication
        if is_entry_gate:
            detections_to_process = deduplicate_entry_gate_detections(det_response.detections)
            import logging
            logging.getLogger("compliance_engine").info("[ENTRY GATE] AFTER NMS: %d", len(detections_to_process))
        else:
            detections_to_process = det_response.detections

        # Separate detections into: persons, PPE items, environmental hazards
        person_dets = []
        ppe_dets = []
        hazards = []

        min_area = self.config.get("tracking", {}).get("min_box_area", 400)
        for obj in detections_to_process:
            cname = obj.class_name.lower()
            b = [obj.bbox.x1, obj.bbox.y1, obj.bbox.x2, obj.bbox.y2]
            if cname == "person":
                box_w = max(0.0, b[2] - b[0])
                box_h = max(0.0, b[3] - b[1])
                if (box_w * box_h) >= min_area:
                    person_dets.append([b[0], b[1], b[2], b[3], obj.confidence])
            elif cname in ["helmet", "safety_vest", "gloves", "safety_footwear"]:
                ppe_dets.append({
                    "class_name": cname,
                    "bbox": b,
                    "confidence": obj.confidence,
                })
            elif cname in ["fire", "smoke"]:
                # Environmental hazards: passed through without marking PPE violations
                hazards.append({
                    "class_name": cname,
                    "bbox": b,
                    "confidence": obj.confidence,
                })

        person_array = np.array(person_dets) if person_dets else np.empty((0, 5))

        # 2. Tracking stage (ByteTrack)
        t1 = time.perf_counter()
        tracked_workers = self.tracker.update(person_array)
        t_track = (time.perf_counter() - t1) * 1000.0

        # 3. Spatial PPE Association stage
        t2 = time.perf_counter()
        img_shape = frame.shape[:2]
        associations, unassociated_ppe = self.associator.associate(
            tracked_workers, ppe_dets, img_shape=img_shape, frame=frame
        )
        t_assoc = (time.perf_counter() - t2) * 1000.0

        # 4. Temporal Validation & Compliance State Machine
        t3 = time.perf_counter()
        worker_tracks: List[WorkerTrack] = []
        worker_boxes = [wb for _, wb, _ in tracked_workers]

        for idx, (tid, wb, conf) in enumerate(tracked_workers):
            # Compute occlusion flags for each PPE item type
            occl_flags = {}
            for item_type in PPEItemType:
                occl_flags[item_type] = self.associator.detect_occlusion(
                    idx, worker_boxes, item_type, img_shape
                )

            worker_obj = self.temporal_tracker.update_worker(
                track_id=tid,
                worker_bbox=wb,
                confidence=conf,
                associations=associations.get(tid, {}),
                is_occluded_flags=occl_flags,
                zone_id=zone_id,
            )
            worker_tracks.append(worker_obj)

        self.temporal_tracker.prune_stale_tracks()
        t_temp = (time.perf_counter() - t3) * 1000.0

        if is_entry_gate:
            import logging
            logging.getLogger("compliance_engine").info("[ENTRY GATE] AFTER TRACKING: %d", len(worker_tracks))

        # 5. Summarize compliance statistics
        summary = ComplianceSummary(
            total_workers=len(worker_tracks),
            compliant_workers=sum(
                1 for w in worker_tracks if w.overall_status == OverallComplianceState.COMPLIANT
            ),
            non_compliant_workers=sum(
                1 for w in worker_tracks if w.overall_status == OverallComplianceState.NON_COMPLIANT
            ),
            unknown_workers=sum(
                1 for w in worker_tracks if w.overall_status == OverallComplianceState.UNKNOWN
            ),
        )

        # 6. Visualization
        annotated_frame = frame
        b64_img = None
        if annotate:
            annotated_frame = self.visualizer.draw_frame(
                frame, worker_tracks, unassociated_ppe, hazards, is_entry_gate=is_entry_gate
            )
            b64_img = encode_image_base64(annotated_frame)

        total_ms = (time.perf_counter() - t_start) * 1000.0
        latencies = {
            "detection_ms": round(t_detect, 2),
            "tracking_ms": round(t_track, 2),
            "association_ms": round(t_assoc, 2),
            "temporal_ms": round(t_temp, 2),
            "total_ms": round(total_ms, 2),
        }

        response = ComplianceAnalysisResponse(
            frame_id=self.frame_counter,
            timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            workers=worker_tracks,
            summary=summary,
            unassociated_ppe_count=len(unassociated_ppe),
            environmental_hazards=hazards,
            raw_detections=getattr(det_response, "raw_detections", []),
            annotated_image_base64=b64_img,
        )

        return response, annotated_frame, latencies
