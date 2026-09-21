"""
tracker.py — RAKSHYA VISION Phase 5
ByteTrack Multi-Object Tracker for detected workers.
Maintains persistent anonymous track IDs across frames without facial recognition.
"""

import numpy as np
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
from scipy.optimize import linear_sum_assignment


class TrackState(int, Enum):
    New = 0
    Tracked = 1
    Lost = 2
    Removed = 3


class KalmanBoxTracker:
    """
    Kalman filter for tracking bounding boxes in image space.
    State vector: [x_center, y_center, s (area), r (aspect ratio), vx, vy, vs, vr]
    """
    count = 0

    def __init__(self, bbox: np.ndarray, score: float):
        # bbox: [x1, y1, x2, y2]
        self.track_id = KalmanBoxTracker.count + 1
        KalmanBoxTracker.count += 1

        self.score = float(score)
        self.state = TrackState.New
        self.is_activated = False

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
            self.hits = 0
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

        self.state = TrackState.Tracked
        self.is_activated = True
        self.last_bbox = self.get_bbox()

    def get_bbox(self) -> np.ndarray:
        """Returns current bounding box estimate in [x1, y1, x2, y2] format."""
        xc, yc, s, r = self.x[0], self.x[1], self.x[2], self.x[3]
        if s <= 0 or r <= 0:
            return self.last_bbox

        w = np.sqrt(s * r)
        h = s / max(1e-6, w)
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
    """

    def __init__(
        self,
        track_high_thresh: float = 0.30,
        track_low_thresh: float = 0.10,
        new_track_thresh: float = 0.40,
        track_buffer: int = 30,
        match_thresh: float = 0.80,
    ):
        self.track_high_thresh = track_high_thresh
        self.track_low_thresh = track_low_thresh
        self.new_track_thresh = new_track_thresh
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh

        self.tracked_stracks: List[KalmanBoxTracker] = []
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

    def update(self, detections: np.ndarray) -> List[Tuple[int, np.ndarray, float]]:
        """
        Updates tracking state with current frame detections.
        detections: array of shape (N, 5) with [x1, y1, x2, y2, score]

        Returns:
            List of (track_id, bbox_xyxy, score) for active confirmed tracks.
        """
        self.frame_id += 1
        activated_stracks = []
        refind_stracks = []
        lost_stracks = []
        removed_stracks = []

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

        # Predict Kalman states for all active and lost tracks
        unconfirmed = []
        tracked_stracks = []
        for track in self.tracked_stracks:
            if not track.is_activated:
                unconfirmed.append(track)
            else:
                tracked_stracks.append(track)

        strack_pool = tracked_stracks + self.lost_stracks
        for track in strack_pool:
            track.predict()

        # ─── First Association: High-score detections with pool ───
        if len(dets) > 0 and len(strack_pool) > 0:
            pool_boxes = np.array([t.last_bbox for t in strack_pool])
            ious = iou_batch(pool_boxes, dets)
            cost_matrix = 1.0 - ious

            row_ind, col_ind = linear_sum_assignment(cost_matrix)

            matched_track_indices = []
            matched_det_indices = []
            for r, c in zip(row_ind, col_ind):
                if cost_matrix[r, c] < (1.0 - (1.0 - self.match_thresh)):  # IoU >= match_thresh
                    matched_track_indices.append(r)
                    matched_det_indices.append(c)

            # Update matched tracks
            for r, c in zip(matched_track_indices, matched_det_indices):
                track = strack_pool[r]
                det = dets[c]
                score = scores_keep[c]
                if track.state == TrackState.Lost:
                    track.state = TrackState.Tracked
                    refind_stracks.append(track)
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

        # ─── Second Association: Low-score detections with unmatched tracks ───
        # Only match with tracks that were tracked in the previous frame
        unmatched_tracked = [t for t in unmatched_tracks_1 if t.state == TrackState.Tracked]
        if len(dets_second) > 0 and len(unmatched_tracked) > 0:
            pool_boxes_2 = np.array([t.last_bbox for t in unmatched_tracked])
            ious_2 = iou_batch(pool_boxes_2, dets_second)
            cost_matrix_2 = 1.0 - ious_2

            row_ind_2, col_ind_2 = linear_sum_assignment(cost_matrix_2)

            matched_track_indices_2 = []
            matched_det_indices_2 = []
            for r, c in zip(row_ind_2, col_ind_2):
                if cost_matrix_2[r, c] < 0.5:  # IoU >= 0.5 for second association
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

        # Unmatched tracks from pool go to lost
        for track in unmatched_tracks_2:
            if track.state != TrackState.Lost:
                track.mark_lost()
                lost_stracks.append(track)
                self.metrics["lost_count"] += 1

        # ─── Unconfirmed tracks association ───
        if len(unmatched_dets_1) > 0 and len(unconfirmed) > 0:
            unconf_boxes = np.array([t.last_bbox for t in unconfirmed])
            det_boxes_1 = np.array([d[0] for d in unmatched_dets_1])
            ious_u = iou_batch(unconf_boxes, det_boxes_1)
            cost_matrix_u = 1.0 - ious_u

            row_ind_u, col_ind_u = linear_sum_assignment(cost_matrix_u)
            matched_u = []
            matched_d = []
            for r, c in zip(row_ind_u, col_ind_u):
                if cost_matrix_u[r, c] < 0.3:
                    matched_u.append(r)
                    matched_d.append(c)

            for r, c in zip(matched_u, matched_d):
                unconfirmed[r].update(unmatched_dets_1[c][0], unmatched_dets_1[c][1])
                activated_stracks.append(unconfirmed[r])

            unmatched_dets_final = [
                unmatched_dets_1[i] for i in range(len(unmatched_dets_1)) if i not in matched_d
            ]
        else:
            unmatched_dets_final = unmatched_dets_1

        # ─── Initialize new tracks for unmatched high-score detections ───
        for det, score in unmatched_dets_final:
            if score >= self.new_track_thresh:
                new_track = KalmanBoxTracker(det, score)
                new_track.is_activated = True
                new_track.state = TrackState.Tracked
                activated_stracks.append(new_track)
                self.metrics["seen_track_ids"].add(new_track.track_id)
                self.metrics["total_unique_tracks"] = len(self.metrics["seen_track_ids"])

        # ─── Manage Lost Tracks Age ───
        current_lost = []
        for track in self.lost_stracks + lost_stracks:
            if track not in activated_stracks:
                if self.frame_id - (track.age - track.time_since_update) > self.track_buffer:
                    track.mark_removed()
                    removed_stracks.append(track)
                else:
                    current_lost.append(track)

        self.tracked_stracks = [t for t in activated_stracks if t.state == TrackState.Tracked]
        self.lost_stracks = current_lost
        self.removed_stracks.extend(removed_stracks)

        # Track duration updates
        for t in self.tracked_stracks:
            tid = t.track_id
            self.metrics["track_durations"][tid] = self.metrics["track_durations"].get(tid, 0) + 1

        # Format output
        output_tracks = []
        for t in self.tracked_stracks:
            bbox = t.get_bbox()
            # Ensure coordinates are within valid bounds
            x1, y1, x2, y2 = max(0, int(bbox[0])), max(0, int(bbox[1])), int(bbox[2]), int(bbox[3])
            output_tracks.append((t.track_id, np.array([x1, y1, x2, y2]), t.score))

        return output_tracks
