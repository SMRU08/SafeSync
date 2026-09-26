"""
test_hazard_positive.py — SafeSync Phase 6 Requirement 12
Positive Fire & Smoke Hazard Validation Test Suite.

Verifies end-to-end positive detection and confirmation pipeline:
  1. Fire detection persistence -> CONFIRMED -> ACTIVE -> Rule 1 P0 Alarm
  2. Smoke detection persistence -> CONFIRMED -> ACTIVE -> Rule 2 P1/P0 Alarm
  3. Concurrent Fire + Smoke -> Rule 3 Multi-Hazard P0 Alarm
  4. Spatial coherence gating: stable tracks confirm, jumpy tracks suppressed
  5. Correct metadata propagation: camera_id, zone_id, timestamp, alert priority
"""

import pytest
import numpy as np
from app.ai.hazards.schemas import (
    HazardType,
    HazardState,
    HazardEventDetail,
    HazardBoundingBox,
    is_alert_state,
)
from app.ai.hazards.tracker import SpatialHazardTracker, HazardTrack
from app.ai.hazards.temporal import TemporalHazardStateMachine
from app.services.safety_engine import SafetyEngine
from app.ai.risk.schemas import EventType, AlarmPriority


@pytest.fixture
def hazard_config():
    return {
        "hazard": {
            "fire_candidate_confidence": 0.30,
            "smoke_candidate_confidence": 0.35,
            "fire_confirmation_confidence": 0.40,
            "smoke_confirmation_confidence": 0.45,
            "confirmation_frames": 5,
            "minimum_observation_ratio": 0.60,
            "smoke_max_gap_frames": 4,
            "fire_max_gap_frames": 3,
            "smoke_clear_frames": 10,
            "fire_clear_frames": 8,
            "max_centroid_jump_normalized": 0.18,
            "min_consistent_detections": 2,
        },
        "tracking": {
            "iou_threshold": 0.25,
            "center_distance_threshold": 0.18,
            "max_unseen_frames": 12,
        },
        "zones": {"enabled": True},
    }


def test_positive_fire_confirmation_and_p0_incident(hazard_config):
    """
    Simulates genuine persistent fire detection across frames.
    Verifies state reaches CONFIRMED and SafetyEngine produces Rule 1 P0 alert.
    """
    sm = TemporalHazardStateMachine(hazard_config)
    safety_engine = SafetyEngine()

    track = HazardTrack(
        event_id="HAZARD-FIRE-01",
        hazard_type=HazardType.FIRE,
        bbox=np.array([200, 200, 300, 350]),
        confidence=0.85,
        frame_idx=1,
        camera_id="camera_01",
        zone_id="production_floor",
        frame_shape=(480, 640),
    )

    # Frame 1: CANDIDATE -> NO ALERT
    st1 = sm.evaluate_track_state(track)
    assert st1 == HazardState.CANDIDATE
    assert not is_alert_state(st1)

    # Frames 2..4: DETECTING (spatially consistent, small shift)
    for f in range(2, 5):
        track.update(
            bbox=np.array([200 + f, 200 + f, 300 + f, 350 + f]),
            confidence=0.86,
            frame_idx=f,
            zone_id="production_floor",
            frame_shape=(480, 640),
        )
        st = sm.evaluate_track_state(track)
        assert st == HazardState.DETECTING
        assert not is_alert_state(st)

    # Frame 5: Reaches confirmation_frames=5 -> CONFIRMED
    track.update(
        bbox=np.array([205, 205, 305, 355]),
        confidence=0.88,
        frame_idx=5,
        zone_id="production_floor",
        frame_shape=(480, 640),
    )
    st5 = sm.evaluate_track_state(track)
    assert st5 == HazardState.CONFIRMED
    assert is_alert_state(st5)

    # Pass confirmed track to SafetyEngine
    detail = HazardEventDetail(
        event_id=track.event_id,
        hazard_type=track.hazard_type,
        state=st5,
        camera_id=track.camera_id,
        zone_id=track.zone_id,
        confidence=track.last_confidence,
        raw_model_confidence=track.last_confidence,
        average_confidence=track.average_confidence,
        max_confidence=track.max_confidence,
        validated_confidence=track.validated_confidence,
        bbox=HazardBoundingBox.from_xyxy(205, 205, 305, 355),
        first_seen=track.first_seen.isoformat(),
        last_seen=track.last_seen.isoformat(),
        duration_seconds=2.0,
        detection_count=track.detection_count,
        persistence_ratio=track.persistence_ratio,
        frames_detected=track.detection_count,
        frames_missed=0,
    )

    ev = safety_engine.enforce_rule_1_fire(detail)
    assert ev is not None, "Rule 1 must produce a NormalizedSafetyEvent for confirmed fire"
    assert ev.event_type == EventType.FIRE_DETECTED
    assert ev.details["priority"] == AlarmPriority.P0.value
    assert ev.details["audible"] is True
    assert ev.camera_id == "camera_01"
    assert ev.zone_id == "production_floor"


def test_positive_smoke_confirmation_and_p1_incident(hazard_config):
    """
    Simulates genuine persistent smoke detection across frames.
    Verifies state reaches CONFIRMED and SafetyEngine produces Rule 2 P1 alert.
    """
    sm = TemporalHazardStateMachine(hazard_config)
    safety_engine = SafetyEngine()

    track = HazardTrack(
        event_id="HAZARD-SMOKE-01",
        hazard_type=HazardType.SMOKE,
        bbox=np.array([150, 50, 400, 300]),
        confidence=0.72,
        frame_idx=1,
        camera_id="camera_02",
        zone_id="storage_area",
        frame_shape=(480, 640),
    )

    # Accumulate 5 spatially coherent frames
    for f in range(2, 6):
        track.update(
            bbox=np.array([150 + f, 50 - f, 400 + f, 300 + f]),
            confidence=0.75,
            frame_idx=f,
            zone_id="storage_area",
            frame_shape=(480, 640),
        )
        sm.evaluate_track_state(track)

    assert sm.event_states[track.event_id] == HazardState.CONFIRMED

    detail = HazardEventDetail(
        event_id=track.event_id,
        hazard_type=track.hazard_type,
        state=HazardState.CONFIRMED,
        camera_id=track.camera_id,
        zone_id=track.zone_id,
        confidence=track.last_confidence,
        raw_model_confidence=track.last_confidence,
        average_confidence=track.average_confidence,
        max_confidence=track.max_confidence,
        validated_confidence=track.validated_confidence,
        bbox=HazardBoundingBox.from_xyxy(155, 45, 405, 305),
        first_seen=track.first_seen.isoformat(),
        last_seen=track.last_seen.isoformat(),
        duration_seconds=3.0,
        detection_count=track.detection_count,
        persistence_ratio=track.persistence_ratio,
        frames_detected=track.detection_count,
        frames_missed=0,
    )

    ev = safety_engine.enforce_rule_2_smoke(detail)
    assert ev is not None, "Rule 2 must produce a NormalizedSafetyEvent for confirmed smoke"
    assert ev.event_type == EventType.SMOKE_DETECTED
    assert ev.details["priority"] == AlarmPriority.P1.value
    assert ev.details["audible"] is True
    assert ev.camera_id == "camera_02"
    assert ev.zone_id == "storage_area"


def test_concurrent_fire_and_smoke_multi_hazard_escalation(hazard_config):
    """
    Tests that simultaneous confirmed fire and smoke triggers Rule 3 MULTIPLE_HAZARDS P0.
    """
    safety_engine = SafetyEngine()

    f_detail = HazardEventDetail(
        event_id="HAZARD-F01",
        hazard_type=HazardType.FIRE,
        state=HazardState.CONFIRMED,
        camera_id="cam_01",
        zone_id="welding_area",
        confidence=0.90,
        average_confidence=0.88,
        max_confidence=0.92,
        bbox=HazardBoundingBox.from_xyxy(100, 100, 200, 200),
        first_seen="2026-09-26T12:00:00Z",
        last_seen="2026-09-26T12:00:05Z",
        duration_seconds=5.0,
        detection_count=10,
        persistence_ratio=0.90,
        frames_detected=10,
        frames_missed=1,
    )

    s_detail = HazardEventDetail(
        event_id="HAZARD-S01",
        hazard_type=HazardType.SMOKE,
        state=HazardState.CONFIRMED,
        camera_id="cam_01",
        zone_id="welding_area",
        confidence=0.80,
        average_confidence=0.78,
        max_confidence=0.82,
        bbox=HazardBoundingBox.from_xyxy(120, 80, 250, 220),
        first_seen="2026-09-26T12:00:00Z",
        last_seen="2026-09-26T12:00:05Z",
        duration_seconds=5.0,
        detection_count=10,
        persistence_ratio=0.85,
        frames_detected=10,
        frames_missed=2,
    )

    multi_ev = safety_engine.enforce_rule_3_multi_hazard([f_detail, s_detail], "cam_01", "welding_area")
    assert multi_ev is not None
    assert multi_ev.event_type == EventType.MULTIPLE_HAZARDS
    assert multi_ev.details["priority"] == AlarmPriority.P0.value


def test_spatial_incoherence_suppression(hazard_config):
    """
    Tests that erratic jumping detections across the screen (e.g. reflection flicker)
    are REJECTED by the spatial consistency check and stay in CANDIDATE/DETECTING.
    """
    sm = TemporalHazardStateMachine(hazard_config)
    track = HazardTrack(
        event_id="HAZARD-JUMPY",
        hazard_type=HazardType.SMOKE,
        bbox=np.array([50, 50, 100, 100]),
        confidence=0.80,
        frame_idx=1,
        camera_id="cam_01",
        zone_id="zone_01",
        frame_shape=(480, 640),
    )

    # Jump randomly across the frame on each update (huge centroid jumps)
    positions = [
        [50, 50, 100, 100],     # Top left
        [500, 400, 550, 450],   # Bottom right
        [50, 400, 100, 450],    # Bottom left
        [500, 50, 550, 100],    # Top right
        [250, 200, 300, 250],   # Center
    ]

    for f, pos in enumerate(positions[1:], start=2):
        track.update(
            bbox=np.array(pos),
            confidence=0.80,
            frame_idx=f,
            zone_id="zone_01",
            frame_shape=(480, 640),
        )
        st = sm.evaluate_track_state(track)

    # Because detections jumped all over the image, spatial coherence check failed!
    assert sm.event_states["HAZARD-JUMPY"] != HazardState.CONFIRMED, (
        "Jumping detection must NOT be confirmed due to spatial incoherence!"
    )
