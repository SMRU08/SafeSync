"""
tracker.py — SafeSync Phase 6
Spatial Hazard Tracker for Fire and Smoke Events.
Maintains persistent anonymous hazard event IDs (HAZARD-0001, HAZARD-0002) across video frames
using IoU overlap and normalized centroid Euclidean distance.
Tracks fire and smoke as distinct independent event streams.
"""

import math
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional, Any
from scipy.optimize import linear_sum_assignment

try:
    from app.ai.hazards.schemas import HazardType, HazardBoundingBox
except ImportError:
    from backend.app.ai.hazards.schemas import HazardType, HazardBoundingBox


def compute_iou(boxA: np.ndarray, boxB: np.ndarray) -> float:
    """Computes Intersection over Union (IoU) between two bounding boxes [x1, y1, x2, y2]."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter_w = max(0.0, xB - xA)
    inter_h = max(0.0, yB - yA)
    inter_area = inter_w * inter_h

    areaA = max(0.0, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    areaB = max(0.0, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

    union = areaA + areaB - inter_area
    return inter_area / union if union > 0.0 else 0.0


def compute_center_distance_norm(
    boxA: np.ndarray, boxB: np.ndarray, frame_w: float, frame_h: float
) -> float:
    """Computes Euclidean distance between box centers normalized by frame diagonal."""
    cA_x = (boxA[0] + boxA[2]) / 2.0
    cA_y = (boxA[1] + boxA[3]) / 2.0
    cB_x = (boxB[0] + boxB[2]) / 2.0
    cB_y = (boxB[1] + boxB[3]) / 2.0

    diag = math.hypot(frame_w, frame_h) if frame_w > 0 and frame_h > 0 else 800.0
    dist = math.hypot(cA_x - cB_x, cA_y - cB_y)
    return dist / diag


class HazardTrack:
    """
    State container for an individual hazard event.
    Tracks detection history, normalized centroid trajectory, and spatial stability.
    """

    def __init__(
        self,
        event_id: str,
        hazard_type: HazardType,
        bbox: np.ndarray,
        confidence: float,
        frame_idx: int,
        camera_id: str,
        zone_id: str,
        frame_shape: Tuple[int, int] = (480, 640),
    ):
        self.event_id = event_id
        self.hazard_type = hazard_type
        self.camera_id = camera_id
        self.zone_id = zone_id

        self.last_bbox = bbox.copy()
        self.last_confidence = float(confidence)
        self.raw_model_confidence = float(confidence)
        self.confidences: List[float] = [float(confidence)]

        now = datetime.now(timezone.utc)
        self.first_seen = now
        self.last_seen = now

        self.first_frame = frame_idx
        self.last_frame = frame_idx

        # Detection history tracking
        self.detection_frames: List[int] = [frame_idx]
        self.missed_frames = 0
        self.unseen_streak = 0
        self.is_active = True

        # Normalized centroid history [cx_norm, cy_norm] in [0.0, 1.0]
        frame_h, frame_w = frame_shape[:2]
        cx = ((bbox[0] + bbox[2]) / 2.0) / max(1.0, float(frame_w))
        cy = ((bbox[1] + bbox[3]) / 2.0) / max(1.0, float(frame_h))
        self.centroid_history: List[Tuple[float, float]] = [(cx, cy)]

    def update(
        self,
        bbox: np.ndarray,
        confidence: float,
        frame_idx: int,
        zone_id: str,
        frame_shape: Tuple[int, int] = (480, 640),
    ):
        self.last_bbox = bbox.copy()
        self.last_confidence = float(confidence)
        self.raw_model_confidence = float(confidence)
        self.confidences.append(float(confidence))
        self.last_seen = datetime.now(timezone.utc)
        self.last_frame = frame_idx
        self.detection_frames.append(frame_idx)
        self.unseen_streak = 0
        if zone_id and zone_id != "UNKNOWN":
            self.zone_id = zone_id

        # Update normalized centroid history
        frame_h, frame_w = frame_shape[:2]
        cx = ((bbox[0] + bbox[2]) / 2.0) / max(1.0, float(frame_w))
        cy = ((bbox[1] + bbox[3]) / 2.0) / max(1.0, float(frame_h))
        self.centroid_history.append((cx, cy))
        if len(self.centroid_history) > 60:
            self.centroid_history.pop(0)

    def mark_missed(self):
        self.missed_frames += 1
        self.unseen_streak += 1

    @property
    def detection_count(self) -> int:
        return len(self.detection_frames)

    @property
    def total_observed_frames(self) -> int:
        return max(1, self.last_frame - self.first_frame + 1)

    @property
    def persistence_ratio(self) -> float:
        return self.detection_count / float(self.total_observed_frames)

    @property
    def average_confidence(self) -> float:
        return float(np.mean(self.confidences)) if self.confidences else 0.0

    @property
    def max_confidence(self) -> float:
        return float(np.max(self.confidences)) if self.confidences else 0.0

    @property
    def duration_seconds(self) -> float:
        delta = (self.last_seen - self.first_seen).total_seconds()
        return max(0.0, float(delta))

    @property
    def spatial_consistency_score(self) -> float:
        """
        Computes spatial stability score between 0.0 (random jumps) and 1.0 (stable).
        Evaluates inter-frame centroid displacement.
        """
        if len(self.centroid_history) < 2:
            return 1.0
        jumps = []
        for i in range(1, len(self.centroid_history)):
            p0 = self.centroid_history[i - 1]
            p1 = self.centroid_history[i]
            dist = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            jumps.append(dist)
        avg_jump = float(np.mean(jumps))
        # Exponential decay: avg_jump=0.0 -> 1.0; avg_jump=0.15 -> 0.47; avg_jump=0.30 -> 0.22
        score = math.exp(-avg_jump * 5.0)
        return float(np.clip(score, 0.0, 1.0))

    @property
    def validated_confidence(self) -> float:
        """
        Calculates confirmation-weighted confidence score.
        Combines model confidence, temporal persistence, and spatial coherence.
        """
        return float(self.average_confidence * self.persistence_ratio * self.spatial_consistency_score)


class SpatialHazardTracker:
    """
    Spatial hazard tracking engine.
    Matches detections to existing tracks per hazard type using bipartite matching.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        track_cfg = cfg.get("tracking", {})
        self.iou_threshold = float(track_cfg.get("iou_threshold", 0.20))
        self.center_distance_threshold = float(track_cfg.get("center_distance_threshold", 0.25))
        self.max_unseen_frames = int(track_cfg.get("max_unseen_frames", 15))

        self.event_counter = 0
        self.active_tracks: List[HazardTrack] = []
        self.archived_tracks: List[HazardTrack] = []

    def _next_event_id(self) -> str:
        self.event_counter += 1
        return f"HAZARD-{self.event_counter:04d}"

    def reset(self):
        self.event_counter = 0
        self.active_tracks.clear()
        self.archived_tracks.clear()

    def update(
        self,
        hazard_detections: List[Dict[str, Any]],
        frame_idx: int,
        camera_id: str = "camera_01",
        frame_shape: Tuple[int, int] = (480, 640),
    ) -> List[HazardTrack]:
        """
        Updates hazard tracks with current frame detections.
        Each item in hazard_detections has:
          - 'hazard_type': HazardType
          - 'confidence': float
          - 'bbox': [x1, y1, x2, y2]
          - 'zone_id': str
        """
        frame_h, frame_w = frame_shape[:2]

        # Separate detections and active tracks by hazard type
        updated_tracks = []

        for htype in [HazardType.FIRE, HazardType.SMOKE]:
            type_dets = [d for d in hazard_detections if d["hazard_type"] == htype]
            type_tracks = [t for t in self.active_tracks if t.hazard_type == htype and t.camera_id == camera_id]

            if not type_tracks and not type_dets:
                continue

            if type_tracks and not type_dets:
                # No detections: mark all active tracks for this type as missed
                for t in type_tracks:
                    t.mark_missed()
                continue

            if not type_tracks and type_dets:
                # No existing tracks: initialize new tracks for all detections
                for d in type_dets:
                    eid = self._next_event_id()
                    new_track = HazardTrack(
                        event_id=eid,
                        hazard_type=htype,
                        bbox=np.array(d["bbox"]),
                        confidence=d["confidence"],
                        frame_idx=frame_idx,
                        camera_id=camera_id,
                        zone_id=d.get("zone_id", "UNKNOWN"),
                        frame_shape=(frame_h, frame_w),
                    )
                    self.active_tracks.append(new_track)
                continue

            # Both existing tracks and new detections exist: construct cost matrix
            n_tracks = len(type_tracks)
            n_dets = len(type_dets)
            cost_matrix = np.full((n_tracks, n_dets), 10.0, dtype=float)

            for i, trk in enumerate(type_tracks):
                for j, det in enumerate(type_dets):
                    det_box = np.array(det["bbox"])
                    iou = compute_iou(trk.last_bbox, det_box)
                    dist_norm = compute_center_distance_norm(trk.last_bbox, det_box, frame_w, frame_h)

                    # Association criterion: sufficient IoU or close centroid proximity
                    if iou >= self.iou_threshold:
                        cost_matrix[i, j] = 1.0 - iou
                    elif dist_norm <= self.center_distance_threshold:
                        cost_matrix[i, j] = 1.0 + dist_norm

            row_ind, col_ind = linear_sum_assignment(cost_matrix)

            matched_track_indices = set()
            matched_det_indices = set()

            for r, c in zip(row_ind, col_ind):
                if cost_matrix[r, c] < 2.0:  # Valid match threshold
                    track = type_tracks[r]
                    det = type_dets[c]
                    track.update(
                        bbox=np.array(det["bbox"]),
                        confidence=det["confidence"],
                        frame_idx=frame_idx,
                        zone_id=det.get("zone_id", "UNKNOWN"),
                        frame_shape=(frame_h, frame_w),
                    )
                    matched_track_indices.add(r)
                    matched_det_indices.add(c)

            # Unmatched tracks
            for i, trk in enumerate(type_tracks):
                if i not in matched_track_indices:
                    trk.mark_missed()

            # Unmatched detections initialize new tracks
            for j, det in enumerate(type_dets):
                if j not in matched_det_indices:
                    eid = self._next_event_id()
                    new_track = HazardTrack(
                        event_id=eid,
                        hazard_type=htype,
                        bbox=np.array(det["bbox"]),
                        confidence=det["confidence"],
                        frame_idx=frame_idx,
                        camera_id=camera_id,
                        zone_id=det.get("zone_id", "UNKNOWN"),
                        frame_shape=(frame_h, frame_w),
                    )
                    self.active_tracks.append(new_track)

        # Prune dead tracks that exceeded max_unseen_frames
        surviving_tracks = []
        for trk in self.active_tracks:
            if trk.unseen_streak > self.max_unseen_frames:
                trk.is_active = False
                self.archived_tracks.append(trk)
            else:
                surviving_tracks.append(trk)
        self.active_tracks = surviving_tracks

        return self.active_tracks
