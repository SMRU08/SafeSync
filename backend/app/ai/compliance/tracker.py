"""
tracker.py — SafeSync Phase 5 & 10
Production Multi-Object Tracker (ByteTrack) for safety-critical worker tracking.
Maintains persistent anonymous track IDs across frames without facial recognition.
Implements robust track lifecycles: TENTATIVE -> ACTIVE -> LOST -> REMOVED.
Prevents single-frame ghost workers via configurable confirmation frames.
"""

import numpy as np
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
from scipy.optimize import linear_sum_assignment


class TrackState(int, Enum):
    New = 0         # Tentative / pending confirmation
    Tentative = 0   # Alias for New
    Tracked = 1     # Confirmed active worker track
    Active = 1      # Alias for Tracked
    Lost = 2        # Temporarily lost (occlusion / missed detection)
    Removed = 3     # Permanently removed / expired
    Expired = 3     # Alias for Removed


class KalmanBoxTracker:
    """
    Kalman filter for tracking worker bounding boxes in image space.
    State vector: [x_center, y_center, s (area), r (aspect ratio), vx, vy, vs, vr]
    """
    count = 0

    def __init__(self, bbox: np.ndarray, score: float, confirmation_frames: int = 2):
        self.track_id = KalmanBoxTracker.count + 1
        KalmanBoxTracker.count += 1

        self.score = float(score)
        self.confirmation_frames = max(1, confirmation_frames)
        self.state = TrackState.New
        self.is_activated = (self.confirmation_frames <= 1)
        if self.is_activated:
            self.state = TrackState.Tracked

        # Measurement matrix (4x8)
        self.H = np.zeros((4, 8))
        self.H[0, 0] = 1
        self.H[1, 1] = 1
        self.H[2, 2] = 1
        self.H[3, 3] = 1

        # Transition matrix (8x8)
        self.F = np.eye(8)
        for i in range(4):
            self.F[i, i + 4] = 1.0

        # Covariance matrices
        self.P = np.eye(8) * 10.0
        self.P[4:, 4:] *= 100.0

        self.Q = np.eye(8) * 1.0
        self.Q[4:, 4:] *= 0.01

        self.R = np.eye(4) * 1.0

        # Initialize state
        w = max(1.0, float(bbox[2] - bbox[0]))
        h = max(1.0, float(bbox[3] - bbox[1]))
        xc = bbox[0] + w / 2.0
        yc = bbox[1] + h / 2.0
        s = w * h
        r = w / h

        self.x = np.array([xc, yc, s, r, 0, 0, 0, 0], dtype=float)

        self.time_since_update = 0
        self.history = []
        self.hits = 1
        self.age = 1
        self.last_bbox = bbox.copy()

    def predict(self) -> np.ndarray:
        """Advance the state vector and returns the predicted bounding box estimate."""
        if self.x[6] + self.x[2] <= 0:
            self.x[6] = 0.0

        self.x = np.dot(self.F, self.x)
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q

        self.age += 1
        if self.time_since_update > 0:
            self.hits = max(0, self.hits - 1)
        self.time_since_update += 1

        self.last_bbox = self.get_bbox()
        return self.last_bbox

    def update(self, bbox: np.ndarray, score: float):
        """Updates the state vector with observed bbox."""
        self.time_since_update = 0
        self.hits += 1
        self.score = float(score)

        w = max(1.0, float(bbox[2] - bbox[0]))
        h = max(1.0, float(bbox[3] - bbox[1]))
        xc = bbox[0] + w / 2.0
        yc = bbox[1] + h / 2.0
        s = w * h
        r = w / h
        z = np.array([xc, yc, s, r], dtype=float)

        # Kalman gain
        y = z - np.dot(self.H, self.x)
        S = np.dot(np.dot(self.H, self.P), self.H.T) + self.R
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))

        # Update state and covariance
        self.x = self.x + np.dot(K, y)
        self.P = self.P - np.dot(np.dot(K, self.H), self.P)

        if not self.is_activated:
            if self.hits >= self.confirmation_frames:
                self.is_activated = True
                self.state = TrackState.Tracked
        else:
            self.state = TrackState.Tracked

        self.last_bbox = self.get_bbox()

    def get_bbox(self) -> np.ndarray:
        """Returns current bounding box estimate in [x1, y1, x2, y2] format."""
        xc, yc, s, r = self.x[0], self.x[1], self.x[2], self.x[3]
        if s <= 0 or r <= 0:
            return self.last_bbox

        w = np.sqrt(s * r)
        h = s / max(1e-6, w)
        # Prevent runaway dimensions
        w = max(5.0, min(w, 5000.0))
        h = max(10.0, min(h, 5000.0))
        x1 = xc - w / 2.0
        y1 = yc - h / 2.0
        x2 = xc + w / 2.0
        y2 = yc + h / 2.0
        return np.array([x1, y1, x2, y2], dtype=float)

    def mark_lost(self):
        self.state = TrackState.Lost

    def mark_removed(self):
        self.state = TrackState.Removed


def iou_batch(boxes_a: np.ndarray, boxes_b: np.ndarray) -> np.ndarray:
    """Computes pairwise IoU between two sets of bounding boxes."""
    if len(boxes_a) == 0 or len(boxes_b) == 0:
        return np.zeros((len(boxes_a), len(boxes_b)))

    # boxes: [x1, y1, x2, y2]
    xA = np.maximum(boxes_a[:, None, 0], boxes_b[None, :, 0])
    yA = np.maximum(boxes_a[:, None, 1], boxes_b[None, :, 1])
    xB = np.minimum(boxes_a[:, None, 2], boxes_b[None, :, 2])
    yB = np.minimum(boxes_a[:, None, 3], boxes_b[None, :, 3])

    inter_w = np.maximum(0.0, xB - xA)
    inter_h = np.maximum(0.0, yB - yA)
    inter_area = inter_w * inter_h

    area_a = (boxes_a[:, 2] - boxes_a[:, 0]) * (boxes_a[:, 3] - boxes_a[:, 1])
    area_b = (boxes_b[:, 2] - boxes_b[:, 0]) * (boxes_b[:, 3] - boxes_b[:, 1])

    union_area = area_a[:, None] + area_b[None, :] - inter_area
    union_area = np.maximum(1e-6, union_area)

    return inter_area / union_area


class ByteTrack:
    """
    ByteTrack implementation for multi-worker tracking.
    Uses high-confidence and low-confidence detection matching tiers.
    Enforces track lifecycle with TENTATIVE confirmation to eliminate ghost false workers.
    """

    def __init__(
        self,
        track_high_thresh: float = 0.25,
        track_low_thresh: float = 0.10,
        new_track_thresh: float = 0.35,
        track_buffer: int = 30,
        match_thresh: float = 0.70,
        confirmation_frames: int = 1,
        lost_tolerance_frames: int = 15,
        **kwargs,
    ):
        self.track_high_thresh = track_high_thresh
        self.track_low_thresh = track_low_thresh
        self.new_track_thresh = new_track_thresh
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        self.confirmation_frames = max(1, confirmation_frames)
        self.lost_tolerance_frames = lost_tolerance_frames

        self.tracked_stracks: List[KalmanBoxTracker] = []
        self.tentative_stracks: List[KalmanBoxTracker] = []
        self.lost_stracks: List[KalmanBoxTracker] = []
        self.removed_stracks: List[KalmanBoxTracker] = []

        self.frame_id = 0
        KalmanBoxTracker.count = 0

        # Metrics for tracking audit
        self.metrics = {
            "total_unique_tracks": 0,
            "seen_track_ids": set(),
            "id_switches": 0,
            "lost_count": 0,
            "recovered_count": 0,
            "track_durations": {},  # track_id -> frames active
        }

    def reset(self):
        self.tracked_stracks.clear()
        self.tentative_stracks.clear()
        self.lost_stracks.clear()
        self.removed_stracks.clear()
        self.frame_id = 0
        KalmanBoxTracker.count = 0
        self.metrics = {
            "total_unique_tracks": 0,
            "seen_track_ids": set(),
            "id_switches": 0,
            "lost_count": 0,
            "recovered_count": 0,
            "track_durations": {},
        }

    def get_track_telemetry(self) -> List[Dict[str, Any]]:
        """Returns comprehensive debug telemetry for all managed tracks."""
        records = []
        all_tracks = self.tracked_stracks + self.tentative_stracks + self.lost_stracks
        for t in all_tracks:
            b = t.get_bbox()
            status_name = "ACTIVE" if (t.state == TrackState.Tracked and t.is_activated) else (
                "TENTATIVE" if t.state == TrackState.New else "LOST"
            )
            records.append({
                "track_id": t.track_id,
                "status": status_name,
                "is_confirmed": t.is_activated,
                "age_frames": t.age,
                "hits": t.hits,
                "lost_frames": t.time_since_update,
                "confidence": round(t.score, 3),
                "bbox": [round(float(v), 1) for v in b],
            })
        return records

    def update(self, detections: np.ndarray) -> List[Tuple[int, np.ndarray, float]]:
        """
        Updates tracking state with current frame detections.
        detections: array of shape (N, 5) with [x1, y1, x2, y2, score]

        Returns:
            List of (track_id, bbox_xyxy, score) for active confirmed tracks.
        """
        self.frame_id += 1
        activated_stracks: List[KalmanBoxTracker] = []
        lost_stracks: List[KalmanBoxTracker] = []
        removed_stracks: List[KalmanBoxTracker] = []

        if len(detections) > 0:
            scores = detections[:, 4]
            bboxes = detections[:, :4]

            # Split into high and low confidence detections
            remain_inds = scores >= self.track_high_thresh
            inds_low = (scores >= self.track_low_thresh) & (scores < self.track_high_thresh)

            dets = bboxes[remain_inds]
            scores_keep = scores[remain_inds]

            dets_second = bboxes[inds_low]
            scores_second = scores[inds_low]
        else:
            dets = np.empty((0, 4))
            scores_keep = np.empty((0,))
            dets_second = np.empty((0, 4))
            scores_second = np.empty((0,))

        # Predict Kalman states for all active, tentative, and lost tracks
        for track in self.tracked_stracks + self.lost_stracks + self.tentative_stracks:
            track.predict()

        strack_pool = self.tracked_stracks + self.lost_stracks

        # ─── First Association: High-score detections with confirmed pool ───
        if len(dets) > 0 and len(strack_pool) > 0:
            pool_boxes = np.array([t.last_bbox for t in strack_pool])
            ious = iou_batch(pool_boxes, dets)
            cost_matrix = 1.0 - ious

            row_ind, col_ind = linear_sum_assignment(cost_matrix)

            matched_track_indices = []
            matched_det_indices = []
            for r, c in zip(row_ind, col_ind):
                if cost_matrix[r, c] < self.match_thresh:  # 1.0 - IoU < match_thresh (i.e. IoU > 1.0 - match_thresh)
                    matched_track_indices.append(r)
                    matched_det_indices.append(c)

            # Update matched tracks
            for r, c in zip(matched_track_indices, matched_det_indices):
                track = strack_pool[r]
                det = dets[c]
                score = scores_keep[c]
                if track.state == TrackState.Lost:
                    track.state = TrackState.Tracked
                    self.metrics["recovered_count"] += 1
                track.update(det, score)
                activated_stracks.append(track)

            unmatched_tracks_1 = [
                strack_pool[i] for i in range(len(strack_pool)) if i not in matched_track_indices
            ]
            unmatched_dets_1 = [
                (dets[i], scores_keep[i]) for i in range(len(dets)) if i not in matched_det_indices
            ]
        else:
            unmatched_tracks_1 = list(strack_pool)
            unmatched_dets_1 = [(dets[i], scores_keep[i]) for i in range(len(dets))]

        # ─── Second Association: Low-score detections with unmatched active tracks ───
        unmatched_tracked = [t for t in unmatched_tracks_1 if t.state == TrackState.Tracked]
        if len(dets_second) > 0 and len(unmatched_tracked) > 0:
            pool_boxes_2 = np.array([t.last_bbox for t in unmatched_tracked])
            ious_2 = iou_batch(pool_boxes_2, dets_second)
            cost_matrix_2 = 1.0 - ious_2

            row_ind_2, col_ind_2 = linear_sum_assignment(cost_matrix_2)

            matched_track_indices_2 = []
            matched_det_indices_2 = []
            for r, c in zip(row_ind_2, col_ind_2):
                if cost_matrix_2[r, c] < 0.50:  # IoU >= 0.50 for second association
                    matched_track_indices_2.append(r)
                    matched_det_indices_2.append(c)

            for r, c in zip(matched_track_indices_2, matched_det_indices_2):
                track = unmatched_tracked[r]
                det = dets_second[c]
                score = scores_second[c]
                track.update(det, score)
                activated_stracks.append(track)

            unmatched_tracks_2 = [
                unmatched_tracked[i]
                for i in range(len(unmatched_tracked))
                if i not in matched_track_indices_2
            ]
        else:
            unmatched_tracks_2 = unmatched_tracked

        # Unmatched confirmed tracks transition to Lost
        for track in unmatched_tracks_2:
            if track.state != TrackState.Lost:
                track.mark_lost()
                lost_stracks.append(track)
                self.metrics["lost_count"] += 1

        # ─── Third Association: Unmatched high-score detections with tentative tracks ───
        tentative_pool = list(self.tentative_stracks)
        tentative_survived = []
        if len(unmatched_dets_1) > 0 and len(tentative_pool) > 0:
            unconf_boxes = np.array([t.last_bbox for t in tentative_pool])
            det_boxes_1 = np.array([d[0] for d in unmatched_dets_1])
            ious_u = iou_batch(unconf_boxes, det_boxes_1)
            cost_matrix_u = 1.0 - ious_u

            row_ind_u, col_ind_u = linear_sum_assignment(cost_matrix_u)
            matched_u = []
            matched_d = []
            for r, c in zip(row_ind_u, col_ind_u):
                if cost_matrix_u[r, c] < self.match_thresh:
                    matched_u.append(r)
                    matched_d.append(c)

            for r, c in zip(matched_u, matched_d):
                t_track = tentative_pool[r]
                d_box, d_score = unmatched_dets_1[c]
                t_track.update(d_box, d_score)
                if t_track.is_activated:
                    activated_stracks.append(t_track)
                    self.metrics["seen_track_ids"].add(t_track.track_id)
                    self.metrics["total_unique_tracks"] = len(self.metrics["seen_track_ids"])
                else:
                    tentative_survived.append(t_track)

            unmatched_dets_final = [
                unmatched_dets_1[i] for i in range(len(unmatched_dets_1)) if i not in matched_d
            ]
            # Unmatched tentative tracks: drop them immediately to reject single-frame noise
            for i, t_track in enumerate(tentative_pool):
                if i not in matched_u:
                    t_track.mark_removed()
                    removed_stracks.append(t_track)
        else:
            unmatched_dets_final = unmatched_dets_1
            # Unmatched tentative tracks without new detections
            for t_track in tentative_pool:
                if t_track.time_since_update > 1:
                    t_track.mark_removed()
                    removed_stracks.append(t_track)
                else:
                    tentative_survived.append(t_track)

        # ─── Initialize new tracks for unmatched high-score detections ───
        for det, score in unmatched_dets_final:
            if score >= self.new_track_thresh:
                new_track = KalmanBoxTracker(det, score, confirmation_frames=self.confirmation_frames)
                if new_track.is_activated or score >= 0.50 or self.confirmation_frames <= 1:
                    new_track.is_activated = True
                    new_track.state = TrackState.Tracked
                    activated_stracks.append(new_track)
                    self.metrics["seen_track_ids"].add(new_track.track_id)
                    self.metrics["total_unique_tracks"] = len(self.metrics["seen_track_ids"])
                else:
                    tentative_survived.append(new_track)

        # ─── Manage Lost Tracks Age & Expiration ───
        current_lost = []
        for track in self.lost_stracks + lost_stracks:
            if track not in activated_stracks:
                if track.time_since_update > self.track_buffer:
                    track.mark_removed()
                    removed_stracks.append(track)
                else:
                    current_lost.append(track)

        self.tracked_stracks = [t for t in activated_stracks if t.state == TrackState.Tracked and t.is_activated]
        self.tentative_stracks = tentative_survived
        self.lost_stracks = current_lost
        self.removed_stracks.extend(removed_stracks)

        # Track duration updates
        for t in self.tracked_stracks:
            tid = t.track_id
            self.metrics["track_durations"][tid] = self.metrics["track_durations"].get(tid, 0) + 1

        # Format output: return only confirmed active tracks within lost tolerance
        output_tracks = []
        for t in self.tracked_stracks:
            if t.time_since_update <= self.lost_tolerance_frames:
                bbox = t.get_bbox()
                x1 = max(0, int(bbox[0]))
                y1 = max(0, int(bbox[1]))
                x2 = max(x1 + 1, int(bbox[2]))
                y2 = max(y1 + 1, int(bbox[3]))
                output_tracks.append((t.track_id, np.array([x1, y1, x2, y2]), t.score))

        return output_tracks
