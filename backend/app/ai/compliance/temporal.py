"""
temporal.py — SafeSync Phase 5
Temporal validation and state machine for worker-level PPE compliance.
Eliminates single-frame detection flicker, honors occlusions with UNKNOWN state,
and evaluates stable COMPLIANT / NON_COMPLIANT / UNKNOWN classifications.
"""

from collections import deque
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

try:
    from app.ai.compliance.schemas import (
        PPEItemType,
        PPEState,
        OverallComplianceState,
        PPEObservation,
        WorkerTrack,
        WorkerBoundingBox,
    )
except ImportError:
    from backend.app.ai.compliance.schemas import (
        PPEItemType,
        PPEState,
        OverallComplianceState,
        PPEObservation,
        WorkerTrack,
        WorkerBoundingBox,
    )


class TemporalComplianceTracker:
    """
    Maintains temporal sliding-window history for active worker tracks.
    Applies configurable confirmation and missing tolerance thresholds.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        temp_cfg = cfg.get("temporal", {})

        self.confirmation_frames = temp_cfg.get("confirmation_frames", 3)
        self.missing_detection_tolerance = temp_cfg.get("missing_detection_tolerance", 5)
        self.history_window_frames = temp_cfg.get("history_window_frames", 30)
        self.prune_lost_after_frames = temp_cfg.get("prune_lost_after_frames", 60)

        # Policy requirements
        req_cfg = cfg.get("required_ppe", {})
        self.required_ppe = {
            PPEItemType.HELMET: req_cfg.get("helmet", True),
            PPEItemType.SAFETY_VEST: req_cfg.get("safety_vest", True),
            PPEItemType.GLOVES: req_cfg.get("gloves", True),
            PPEItemType.SAFETY_FOOTWEAR: req_cfg.get("safety_footwear", True),
        }

        # Internal state per track_id:
        # track_id -> { item_type: deque([bool or None]) }
        self._history: Dict[int, Dict[PPEItemType, deque]] = {}
        # track_id -> { item_type: int }
        self._consecutive_seen: Dict[int, Dict[PPEItemType, int]] = {}
        self._consecutive_missed: Dict[int, Dict[PPEItemType, int]] = {}
        # track_id -> { item_type: PPEState }
        self._confirmed_state: Dict[int, Dict[PPEItemType, PPEState]] = {}
        # track_id -> metadata
        self._last_seen_frame: Dict[int, int] = {}
        self._total_frames_seen: Dict[int, int] = {}

        self.current_frame = 0

    def reset(self):
        self._history.clear()
        self._consecutive_seen.clear()
        self._consecutive_missed.clear()
        self._confirmed_state.clear()
        self._last_seen_frame.clear()
        self._total_frames_seen.clear()
        self.current_frame = 0

    def _init_track_if_needed(self, track_id: int):
        if track_id not in self._history:
            self._history[track_id] = {
                item: deque(maxlen=self.history_window_frames) for item in PPEItemType
            }
            self._consecutive_seen[track_id] = {item: 0 for item in PPEItemType}
            self._consecutive_missed[track_id] = {item: 0 for item in PPEItemType}
            self._confirmed_state[track_id] = {item: PPEState.UNKNOWN for item in PPEItemType}
            self._total_frames_seen[track_id] = 0

    def update_worker(
        self,
        track_id: int,
        worker_bbox: np.ndarray,
        confidence: float,
        associations: Dict[str, Optional[Dict[str, Any]]],
        is_occluded_flags: Dict[PPEItemType, bool],
        zone_id: Optional[str] = None,
    ) -> WorkerTrack:
        """
        Updates temporal state for a single tracked worker.
        Zone-aware: respects zone-specific required/optional/disabled PPE policies.
        """
        self._init_track_if_needed(track_id)
        self._last_seen_frame[track_id] = self.current_frame
        self._total_frames_seen[track_id] += 1
        frames_seen = self._total_frames_seen[track_id]

        wb = WorkerBoundingBox(
            x1=int(worker_bbox[0]),
            y1=int(worker_bbox[1]),
            x2=int(worker_bbox[2]),
            y2=int(worker_bbox[3]),
        )

        ppe_summary: Dict[str, PPEState] = {}
        ppe_details: Dict[str, PPEObservation] = {}
        has_any_occlusion = False

        for item_type in PPEItemType:
            raw_match = associations.get(item_type.value)
            is_occluded = is_occluded_flags.get(item_type, False)
            if is_occluded:
                has_any_occlusion = True

            hist = self._history[track_id][item_type]

            if raw_match is not None:
                # PPE detected and associated in this frame
                hist.append(True)
                self._consecutive_seen[track_id][item_type] += 1
                self._consecutive_missed[track_id][item_type] = 0

                c_seen = self._consecutive_seen[track_id][item_type]
                if c_seen >= self.confirmation_frames:
                    self._confirmed_state[track_id][item_type] = PPEState.PRESENT
                else:
                    # Still gathering temporal confirmation evidence
                    self._confirmed_state[track_id][item_type] = PPEState.UNKNOWN

                match_box = None
                if "bbox" in raw_match:
                    mb = raw_match["bbox"]
                    match_box = WorkerBoundingBox(
                        x1=int(mb[0]), y1=int(mb[1]), x2=int(mb[2]), y2=int(mb[3])
                    )

                obs = PPEObservation(
                    item_type=item_type,
                    state=self._confirmed_state[track_id][item_type],
                    confidence=raw_match.get("confidence"),
                    bbox=match_box,
                    consecutive_seen=c_seen,
                    consecutive_missed=0,
                    evidence_ratio=round(sum(1 for x in hist if x is True) / len(hist), 2),
                    is_occluded=is_occluded,
                    details=f"Seen for {c_seen} frame(s)",
                )
            else:
                # PPE not detected / not associated in this frame
                hist.append(False)
                self._consecutive_seen[track_id][item_type] = 0

                if is_occluded:
                    # Occluded body zone: Do NOT penalize worker with ABSENT
                    # Also reset consecutive_missed so clearing occlusion doesn't trigger ABSENT immediately
                    self._consecutive_missed[track_id][item_type] = 0
                    self._confirmed_state[track_id][item_type] = PPEState.UNKNOWN
                    details_str = "Body zone occluded or clipped by frame boundary"
                else:
                    self._consecutive_missed[track_id][item_type] += 1
                    c_missed = self._consecutive_missed[track_id][item_type]

                    if c_missed >= self.missing_detection_tolerance:
                        self._confirmed_state[track_id][item_type] = PPEState.ABSENT
                        details_str = f"Confirmed absent ({c_missed} consecutive missed frames)"
                    elif frames_seen < self.confirmation_frames:
                        # New track, insufficient observations to declare absent
                        self._confirmed_state[track_id][item_type] = PPEState.UNKNOWN
                        details_str = f"Initializing observation ({frames_seen}/{self.confirmation_frames} frames)"
                    else:
                        # Within tolerance: maintain prior confirmed state or UNKNOWN
                        prior = self._confirmed_state[track_id][item_type]
                        if prior == PPEState.PRESENT:
                            # Tolerating temporary detector flicker
                            details_str = f"Temporary detection drop ({c_missed}/{self.missing_detection_tolerance} tolerance frames)"
                        else:
                            self._confirmed_state[track_id][item_type] = PPEState.UNKNOWN
                            details_str = f"Unconfirmed ({c_missed} frames missing)"

                c_missed = self._consecutive_missed[track_id][item_type]
                obs = PPEObservation(
                    item_type=item_type,
                    state=self._confirmed_state[track_id][item_type],
                    confidence=None,
                    bbox=None,
                    consecutive_seen=0,
                    consecutive_missed=c_missed,
                    evidence_ratio=round(sum(1 for x in hist if x is True) / len(hist), 2),
                    is_occluded=is_occluded,
                    details=details_str,
                )

            ppe_summary[item_type.value] = self._confirmed_state[track_id][item_type]
            ppe_details[item_type.value] = obs

        # ─── Compute Overall Compliance State ───
        # Rule:
        # 1. NON_COMPLIANT if ANY required PPE is confirmed ABSENT with temporal evidence
        # 2. COMPLIANT if ALL required PPE are confirmed PRESENT
        # 3. UNKNOWN if any required PPE is UNKNOWN and no item is confirmed ABSENT
        # Optional/Disabled PPE in this zone does NOT trigger NON_COMPLIANT.
        overall_status = OverallComplianceState.COMPLIANT

        has_absent = False
        has_unknown = False

        # Resolve active required policy per zone (PS06: "gloves where applicable")
        active_required = dict(self.required_ppe)
        if zone_id:
            try:
                try:
                    from app.ai.compliance.ppe_policy import ZonePPEPolicyEngine
                except ImportError:
                    from backend.app.ai.compliance.ppe_policy import ZonePPEPolicyEngine
                policy = ZonePPEPolicyEngine.get_instance().get_policy_for_zone(zone_id)
                active_required = {
                    item_type: policy.is_required(item_type.value)
                    for item_type in PPEItemType
                }
            except Exception:
                active_required = dict(self.required_ppe)

        for item_type, is_req in active_required.items():
            if not is_req:
                continue
            item_state = ppe_summary[item_type.value]
            if item_state == PPEState.ABSENT:
                has_absent = True
            elif item_state == PPEState.UNKNOWN:
                has_unknown = True

        if has_absent:
            overall_status = OverallComplianceState.NON_COMPLIANT
        elif has_unknown:
            overall_status = OverallComplianceState.UNKNOWN
        else:
            overall_status = OverallComplianceState.COMPLIANT

        return WorkerTrack(
            track_id=track_id,
            bbox=wb,
            confidence=float(confidence),
            ppe=ppe_summary,
            ppe_details=ppe_details,
            overall_status=overall_status,
            history_length=len(self._history[track_id][PPEItemType.HELMET]),
            is_partially_occluded=has_any_occlusion,
        )

    def prune_stale_tracks(self):
        """Removes memory for tracks not seen in prune_lost_after_frames."""
        stale_tids = [
            tid
            for tid, last_f in self._last_seen_frame.items()
            if (self.current_frame - last_f) > self.prune_lost_after_frames
        ]
        for tid in stale_tids:
            self._history.pop(tid, None)
            self._consecutive_seen.pop(tid, None)
            self._consecutive_missed.pop(tid, None)
            self._confirmed_state.pop(tid, None)
            self._last_seen_frame.pop(tid, None)
            self._total_frames_seen.pop(tid, None)
