"""
temporal.py — SafeSync Phase 6 v2
Robust 7-Stage Temporal Hazard State Machine with Spatial Consistency Validation.

State transitions:
  NO_HAZARD → CANDIDATE → DETECTING → CONFIRMED → ACTIVE → CLEARING → CLEARED → NO_HAZARD

Design goals:
  1. A single-frame detection NEVER generates an emergency alert.
  2. Spatially incoherent "jumping" detections are suppressed.
  3. Only CONFIRMED and ACTIVE states trigger P0/P1 safety events.
  4. CLEARING provides hysteresis to avoid rapid on/off alert cycles.
  5. All thresholds are config-driven — no hard-coded magic numbers.

Parameters (all from hazard.yaml → hazard: section):
  confirmation_frames          : detections needed before CONFIRMED
  minimum_observation_ratio    : fraction of frames that must be detected
  smoke_max_gap_frames /
  fire_max_gap_frames          : missed frames before DETECTING → CANDIDATE
  smoke_clear_frames /
  fire_clear_frames            : missed frames before CONFIRMED → CLEARING
  fire_confirmation_confidence : avg confidence required for fire CONFIRMED
  smoke_confirmation_confidence: avg confidence required for smoke CONFIRMED
  max_centroid_jump_normalized : max centroid movement per frame (normalized)
  min_consistent_detections    : spatial coherence gate before state advance
"""

import math
import logging
from typing import Dict, Any, List, Optional

try:
    from app.ai.hazards.schemas import (
        HazardState,
        HazardRelationship,
        HazardType,
        HAZARD_STATE_SEVERITY,
        is_alert_state,
    )
    from app.ai.hazards.tracker import HazardTrack
except ImportError:
    from backend.app.ai.hazards.schemas import (
        HazardState,
        HazardRelationship,
        HazardType,
        HAZARD_STATE_SEVERITY,
        is_alert_state,
    )
    from backend.app.ai.hazards.tracker import HazardTrack

logger = logging.getLogger("hazard.temporal")


class TemporalHazardStateMachine:
    """
    7-stage temporal hazard state machine with spatial consistency gating.

    Per-type parameters allow fire and smoke to have different sensitivities.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        h_cfg = cfg.get("hazard", {})

        # ── Temporal confirmation ────────────────────────────────────────────
        self.confirmation_frames = int(h_cfg.get("confirmation_frames", 8))
        self.minimum_observation_ratio = float(h_cfg.get("minimum_observation_ratio", 0.65))

        # ── Per-type gap tolerance (DETECTING → CANDIDATE decay) ─────────────
        self.smoke_max_gap_frames = int(h_cfg.get("smoke_max_gap_frames", 4))
        self.fire_max_gap_frames = int(h_cfg.get("fire_max_gap_frames", 3))

        # ── Clearing thresholds (CONFIRMED → CLEARING → CLEARED) ─────────────
        self.smoke_clear_frames = int(h_cfg.get("smoke_clear_frames", 15))
        self.fire_clear_frames = int(h_cfg.get("fire_clear_frames", 10))

        # ── Confirmation confidence gate ─────────────────────────────────────
        self.fire_confirmation_confidence = float(
            h_cfg.get("fire_confirmation_confidence", 0.40)
        )
        self.smoke_confirmation_confidence = float(
            h_cfg.get("smoke_confirmation_confidence", 0.45)
        )

        # ── Spatial consistency parameters ───────────────────────────────────
        self.max_centroid_jump = float(
            h_cfg.get("max_centroid_jump_normalized", 0.18)
        )
        self.min_consistent_detections = int(
            h_cfg.get("min_consistent_detections", 2)
        )

        # ── State registry ───────────────────────────────────────────────────
        self.event_states: Dict[str, HazardState] = {}
        # Tracks consecutive missed frames per event (separate from HazardTrack.unseen_streak
        # so we can apply per-type thresholds cleanly).
        self._clearing_counters: Dict[str, int] = {}

    def reset(self):
        self.event_states.clear()
        self._clearing_counters.clear()

    def _get_gap_frames(self, hazard_type: HazardType) -> int:
        return self.fire_max_gap_frames if hazard_type == HazardType.FIRE else self.smoke_max_gap_frames

    def _get_clear_frames(self, hazard_type: HazardType) -> int:
        return self.fire_clear_frames if hazard_type == HazardType.FIRE else self.smoke_clear_frames

    def _get_confirmation_confidence(self, hazard_type: HazardType) -> float:
        return (
            self.fire_confirmation_confidence
            if hazard_type == HazardType.FIRE
            else self.smoke_confirmation_confidence
        )

    def _is_spatially_coherent(self, track: HazardTrack) -> bool:
        """
        Returns True if the track has enough spatially consistent detections.

        Spatial coherence check:
          1. Track must have at least min_consistent_detections observations.
          2. The centroid movement history (stored in track) must not exceed
             max_centroid_jump per frame on average.

        If the track does not have centroid_history, we accept it (backward compat).
        """
        if track.detection_count < self.min_consistent_detections:
            return False
        # Check centroid jump history if available
        history = getattr(track, "centroid_history", [])
        if len(history) < 2:
            return True  # Not enough history to reject
        total_jump = 0.0
        for i in range(1, len(history)):
            prev = history[i - 1]
            curr = history[i]
            jump = math.hypot(curr[0] - prev[0], curr[1] - prev[1])
            total_jump += jump
        avg_jump = total_jump / (len(history) - 1)
        coherent = avg_jump <= self.max_centroid_jump
        if not coherent:
            logger.debug(
                "Spatial incoherence: track %s avg_centroid_jump=%.3f > threshold=%.3f — suppressing",
                track.event_id, avg_jump, self.max_centroid_jump
            )
        return coherent

    def _is_confirmation_qualified(self, track: HazardTrack) -> bool:
        """
        A track qualifies for CONFIRMED only if ALL of these hold:
          1. detection_count >= confirmation_frames
          2. persistence_ratio >= minimum_observation_ratio
          3. average_confidence >= per-type confirmation confidence threshold
          4. Spatial coherence check passes
        """
        if track.detection_count < self.confirmation_frames:
            return False
        if track.persistence_ratio < self.minimum_observation_ratio:
            return False
        if track.average_confidence < self._get_confirmation_confidence(track.hazard_type):
            logger.debug(
                "Track %s avg_conf=%.3f < required=%.3f — staying in DETECTING",
                track.event_id,
                track.average_confidence,
                self._get_confirmation_confidence(track.hazard_type),
            )
            return False
        if not self._is_spatially_coherent(track):
            return False
        return True

    # ──────────────────────────────────────────────────────────────────────────
    # MAIN STATE EVALUATION
    # ──────────────────────────────────────────────────────────────────────────

    def evaluate_track_state(self, track: HazardTrack) -> HazardState:
        """
        Evaluates the next state for a single hazard track.

        State machine transitions:
        NO_HAZARD  → CANDIDATE   (first detection seen)
        CANDIDATE  → DETECTING   (spatially coherent and detection_count >= 2)
        CANDIDATE  → NO_HAZARD   (unseen_streak > gap_frames)
        DETECTING  → CONFIRMED   (all confirmation criteria met)
        DETECTING  → CANDIDATE   (unseen_streak > gap_frames)
        CONFIRMED  → ACTIVE      (subsequent confirmed frames)
        ACTIVE     → CLEARING    (unseen_streak approaching clear_frames)
        ACTIVE     → ACTIVE      (detection re-seen)
        CLEARING   → ACTIVE      (detection re-seen while clearing)
        CLEARING   → CLEARED     (unseen_streak > clear_frames)
        CLEARED    → CANDIDATE   (new detection seen)
        CLEARED    → NO_HAZARD   (not re-detected)
        """
        eid = track.event_id
        current_state = self.event_states.get(eid, HazardState.NO_HAZARD)
        gap_frames = self._get_gap_frames(track.hazard_type)
        clear_frames = self._get_clear_frames(track.hazard_type)

        # ── Compute clearing counter (independent of HazardTrack.unseen_streak) ──
        if track.unseen_streak == 0:
            self._clearing_counters[eid] = 0
        else:
            self._clearing_counters[eid] = self._clearing_counters.get(eid, 0) + 1
        unseen = self._clearing_counters[eid]

        # ── Transitions ───────────────────────────────────────────────────────
        if current_state == HazardState.NO_HAZARD:
            if track.unseen_streak == 0:
                new_state = HazardState.CANDIDATE
            else:
                new_state = HazardState.NO_HAZARD

        elif current_state == HazardState.CANDIDATE:
            if track.unseen_streak > gap_frames:
                # Brief detection that vanished — probably noise
                new_state = HazardState.NO_HAZARD
                logger.debug("Track %s (CANDIDATE) vanished after %d frames — NO_HAZARD", eid, track.unseen_streak)
            elif self._is_spatially_coherent(track) and track.detection_count >= self.min_consistent_detections:
                new_state = HazardState.DETECTING
            else:
                new_state = HazardState.CANDIDATE

        elif current_state == HazardState.DETECTING:
            if track.unseen_streak > gap_frames:
                # Lost the detection stream — decay back to candidate
                new_state = HazardState.CANDIDATE
                logger.debug("Track %s (DETECTING) decayed to CANDIDATE — unseen=%d", eid, track.unseen_streak)
            elif self._is_confirmation_qualified(track):
                new_state = HazardState.CONFIRMED
                logger.info(
                    "Track %s CONFIRMED: type=%s conf=%.3f persistence=%.2f detections=%d",
                    eid, track.hazard_type.value,
                    track.average_confidence, track.persistence_ratio, track.detection_count
                )
            else:
                new_state = HazardState.DETECTING

        elif current_state == HazardState.CONFIRMED:
            if unseen >= clear_frames:
                new_state = HazardState.CLEARING
            elif track.unseen_streak == 0:
                new_state = HazardState.ACTIVE
            else:
                # Within gap tolerance — stay CONFIRMED
                new_state = HazardState.CONFIRMED

        elif current_state == HazardState.ACTIVE:
            if unseen >= clear_frames:
                new_state = HazardState.CLEARING
            elif track.unseen_streak == 0:
                new_state = HazardState.ACTIVE
            else:
                new_state = HazardState.ACTIVE

        elif current_state == HazardState.CLEARING:
            if track.unseen_streak == 0:
                # Re-detected while clearing — go back to ACTIVE
                new_state = HazardState.ACTIVE
                self._clearing_counters[eid] = 0
            elif unseen >= clear_frames * 2:
                # Fully absent long enough
                new_state = HazardState.CLEARED
            else:
                new_state = HazardState.CLEARING

        elif current_state == HazardState.CLEARED:
            if track.unseen_streak == 0:
                # New detection after clearing — restart from CANDIDATE
                new_state = HazardState.CANDIDATE
                self._clearing_counters[eid] = 0
            else:
                new_state = HazardState.NO_HAZARD

        else:
            new_state = HazardState.NO_HAZARD

        self.event_states[eid] = new_state
        return new_state

    def evaluate_scene_relationship(
        self, active_tracks: List[HazardTrack]
    ) -> HazardRelationship:
        """
        Determines the multi-modal relationship in the current scene.
        ONLY considers tracks in CONFIRMED or ACTIVE states.
        CANDIDATE/DETECTING/CLEARING tracks are internal states — not counted.
        """
        has_fire = False
        has_smoke = False

        for t in active_tracks:
            state = self.event_states.get(t.event_id, HazardState.NO_HAZARD)
            if is_alert_state(state):
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
        Computes the highest severity state across all active tracks.
        Uses HAZARD_STATE_SEVERITY ordering.
        """
        highest = HazardState.NO_HAZARD
        highest_sev = HAZARD_STATE_SEVERITY.get(highest, 1)

        for t in active_tracks:
            st = self.event_states.get(t.event_id, HazardState.NO_HAZARD)
            sev = HAZARD_STATE_SEVERITY.get(st, 1)
            if sev > highest_sev:
                highest = st
                highest_sev = sev

        return highest
