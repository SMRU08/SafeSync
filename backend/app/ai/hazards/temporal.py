"""
temporal.py — SafeSync Phase 6
Temporal Hazard State Machine.
Evaluates state transitions: NO_HAZARD -> SUSPECTED -> CONFIRMED -> CLEARED -> NO_HAZARD.
Implements temporal evidence accumulation, gap tolerance, clearing rules, and
relationship categorization (FIRE_ONLY, SMOKE_ONLY, FIRE_AND_SMOKE, NO_HAZARD).
"""

from typing import Dict, Any, List, Optional
try:
    from app.ai.hazards.schemas import HazardState, HazardRelationship, HazardType
    from app.ai.hazards.tracker import HazardTrack
except ImportError:
    from backend.app.ai.hazards.schemas import HazardState, HazardRelationship, HazardType
    from backend.app.ai.hazards.tracker import HazardTrack


class TemporalHazardStateMachine:
    """
    Manages temporal hazard states for active tracks across video frames.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        h_cfg = cfg.get("hazard", {})
        self.confirmation_frames = int(h_cfg.get("confirmation_frames", 5))
        self.minimum_observation_ratio = float(h_cfg.get("minimum_observation_ratio", 0.60))
        self.clear_frames = int(h_cfg.get("clear_frames", 10))
        self.max_gap_frames = int(h_cfg.get("max_gap_frames", 5))

        # Maps event_id -> current HazardState
        self.event_states: Dict[str, HazardState] = {}

    def reset(self):
        self.event_states.clear()

    def evaluate_track_state(self, track: HazardTrack) -> HazardState:
        """
        Evaluates the current state for an individual hazard track.
        """
        eid = track.event_id
        current_state = self.event_states.get(eid, HazardState.NO_HAZARD)

        # 1. New or previously unobserved track
        if current_state == HazardState.NO_HAZARD:
            if track.detection_count >= self.confirmation_frames and track.persistence_ratio >= self.minimum_observation_ratio:
                new_state = HazardState.CONFIRMED
            else:
                new_state = HazardState.SUSPECTED
            self.event_states[eid] = new_state
            return new_state

        # 2. Currently in SUSPECTED state
        if current_state == HazardState.SUSPECTED:
            # Check if it exceeded max gap without confirmation (false positive decay)
            if track.unseen_streak >= self.max_gap_frames:
                new_state = HazardState.CLEARED
            # Check if confirmed
            elif (
                track.detection_count >= self.confirmation_frames
                and track.persistence_ratio >= self.minimum_observation_ratio
            ):
                new_state = HazardState.CONFIRMED
            else:
                new_state = HazardState.SUSPECTED

            self.event_states[eid] = new_state
            return new_state

        # 3. Currently in CONFIRMED state
        if current_state == HazardState.CONFIRMED:
            # Check if consecutive missed frames reach clearing threshold
            if track.unseen_streak >= self.clear_frames:
                new_state = HazardState.CLEARED
            else:
                # Within tolerance window (momentary flicker/dispersal tolerated)
                new_state = HazardState.CONFIRMED

            self.event_states[eid] = new_state
            return new_state

        # 4. Currently in CLEARED state
        if current_state == HazardState.CLEARED:
            # If re-detected again after clearing, restart evaluation
            if track.unseen_streak == 0:
                new_state = HazardState.SUSPECTED
            else:
                new_state = HazardState.NO_HAZARD

            self.event_states[eid] = new_state
            return new_state

        return HazardState.NO_HAZARD

    def evaluate_scene_relationship(
        self, active_tracks: List[HazardTrack]
    ) -> HazardRelationship:
        """
        Determines the multi-modal relationship in the current scene:
        FIRE_ONLY, SMOKE_ONLY, FIRE_AND_SMOKE, or NO_HAZARD.
        Only considers active tracks that are not CLEARED or NO_HAZARD.
        """
        has_fire = False
        has_smoke = False

        for t in active_tracks:
            state = self.event_states.get(t.event_id, HazardState.NO_HAZARD)
            if state in [HazardState.SUSPECTED, HazardState.CONFIRMED]:
                if t.hazard_type == HazardType.FIRE:
                    has_fire = True
                elif t.hazard_type == HazardType.SMOKE:
                    has_smoke = True

        if has_fire and has_smoke:
            return HazardRelationship.FIRE_AND_SMOKE
        if has_fire:
            return HazardRelationship.FIRE_ONLY
        if has_smoke:
            return HazardRelationship.SMOKE_ONLY
        return HazardRelationship.NO_HAZARD

    def evaluate_overall_scene_state(
        self, active_tracks: List[HazardTrack]
    ) -> HazardState:
        """
        Computes the highest severity state across all active tracks:
        CONFIRMED > SUSPECTED > CLEARED > NO_HAZARD.
        """
        highest = HazardState.NO_HAZARD
        order = {
            HazardState.CONFIRMED: 4,
            HazardState.SUSPECTED: 3,
            HazardState.CLEARED: 2,
            HazardState.NO_HAZARD: 1,
        }

        for t in active_tracks:
            st = self.event_states.get(t.event_id, HazardState.NO_HAZARD)
            if order.get(st, 0) > order.get(highest, 0):
                highest = st

        return highest
