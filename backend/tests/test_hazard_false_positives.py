"""
test_hazard_false_positives.py — SafeSync Phase 6 Requirement 11
Comprehensive Negative Example & False-Positive Stress Test Suite.

Tests that non-hazard optical artifacts do NOT produce CONFIRMED fire or smoke emergencies:
  1. White wall
  2. Bright sunlight / solar glare
  3. Window reflection
  4. Steam / water vapor
  5. Dust / particulates
  6. Vehicle exhaust
  7. Welding brightness / flash
  8. Orange / red clothing
  9. Skin tones
  10. Moving shadows
  11. Compression artifacts / block noise
  12. Normal indoor scene
"""

import pytest
import numpy as np
import cv2
from app.ai.hazards.hazard_engine import HazardAnalysisEngine
from app.ai.hazards.schemas import HazardState, is_alert_state
from app.services.safety_engine import SafetyEngine


@pytest.fixture(scope="module")
def hazard_engine():
    engine = HazardAnalysisEngine()
    return engine


@pytest.fixture(scope="module")
def safety_engine():
    return SafetyEngine()


def _make_negative_scene(scenario_type: str, w: int = 640, h: int = 480) -> np.ndarray:
    """Generates synthetic test frames representing common false-positive triggers."""
    img = np.zeros((h, w, 3), dtype=np.uint8)

    if scenario_type == "white_wall":
        # Uniform near-white surface with subtle sensor noise
        img[:] = 240
        noise = np.random.randint(-5, 5, (h, w, 3), dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    elif scenario_type == "bright_sunlight":
        # Glare circle with radial falloff
        img[:] = 160
        cv2.circle(img, (w // 2, h // 3), 120, (255, 255, 255), -1)
        img = cv2.GaussianBlur(img, (51, 51), 0)

    elif scenario_type == "window_reflection":
        # Rectangular window glare
        img[:] = 70
        cv2.rectangle(img, (w // 4, h // 4), (3 * w // 4, 3 * h // 4), (230, 240, 255), -1)
        img = cv2.GaussianBlur(img, (25, 25), 0)

    elif scenario_type == "steam":
        # Wispy diffuse light-gray cloud
        img[:] = 90
        overlay = img.copy()
        for offset in range(-30, 40, 15):
            cv2.ellipse(overlay, (w // 2 + offset, h // 2), (80, 40), 15, 0, 360, (210, 210, 210), -1)
        img = cv2.addWeighted(img, 0.4, overlay, 0.6, 0)
        img = cv2.GaussianBlur(img, (31, 31), 0)

    elif scenario_type == "dust":
        # Granular pepper noise over dim factory floor
        img[:] = 80
        num_dust = 1500
        ys = np.random.randint(0, h, num_dust)
        xs = np.random.randint(0, w, num_dust)
        img[ys, xs] = np.random.randint(180, 230, (num_dust, 3), dtype=np.uint8)

    elif scenario_type == "vehicle_exhaust":
        # Faint gray gradient patch
        img[:] = 60
        cv2.circle(img, (w // 2, h // 2), 60, (130, 130, 130), -1)
        img = cv2.GaussianBlur(img, (35, 35), 0)

    elif scenario_type == "welding_brightness":
        # Intense high-frequency point light
        img[:] = 30
        cv2.circle(img, (w // 2, h // 2), 25, (255, 255, 255), -1)
        img = cv2.GaussianBlur(img, (15, 15), 0)

    elif scenario_type == "orange_red_clothing":
        # Saturated orange and red rectangles simulating safety vest / workwear
        img[:] = 100
        # High-vis orange patch (BGR: [0, 120, 255])
        cv2.rectangle(img, (150, 100), (300, 350), (0, 120, 255), -1)
        # Deep red patch (BGR: [20, 20, 220])
        cv2.rectangle(img, (350, 100), (500, 350), (20, 20, 220), -1)

    elif scenario_type == "skin":
        # Human skin tone patch (BGR approximate: [120, 150, 210])
        img[:] = 110
        cv2.ellipse(img, (w // 2, h // 2), (90, 120), 0, 0, 360, (125, 155, 215), -1)

    elif scenario_type == "moving_shadows":
        # Gradient shadow band
        img[:] = 180
        cv2.rectangle(img, (0, 0), (w // 2, h), (40, 40, 40), -1)
        img = cv2.GaussianBlur(img, (61, 61), 0)

    elif scenario_type == "compression_artifacts":
        # Severe block quantization noise
        img = np.random.randint(80, 130, (h, w, 3), dtype=np.uint8)
        _, enc = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 5])
        img = cv2.imdecode(enc, cv2.IMREAD_COLOR)

    elif scenario_type == "normal_indoor_scene":
        # Typical ambient room: desk, walls, ambient light
        img[:] = 120
        cv2.rectangle(img, (50, 250), (w - 50, h), (80, 60, 50), -1)  # Desk
        cv2.rectangle(img, (100, 50), (250, 200), (190, 190, 190), -1) # Computer monitor

    return img


SCENARIOS = [
    "white_wall",
    "bright_sunlight",
    "window_reflection",
    "steam",
    "dust",
    "vehicle_exhaust",
    "welding_brightness",
    "orange_red_clothing",
    "skin",
    "moving_shadows",
    "compression_artifacts",
    "normal_indoor_scene",
]


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_negative_scenario_no_confirmed_emergency(hazard_engine, safety_engine, scenario):
    """
    Rigorously tests that 10 consecutive frames of a negative scenario NEVER
    transition to a CONFIRMED hazard or trigger emergency P0/P1 alarms.
    """
    hazard_engine.reset()
    frame = _make_negative_scene(scenario)

    confirmed_hazards = []
    emergency_events = []

    for _ in range(10):
        resp, _, _ = hazard_engine.process_frame(
            frame=frame,
            camera_id="camera_01",
            annotate=False,
        )

        assessment = safety_engine.assess_scene(
            camera_id="camera_01",
            zone_id="production_floor",
            hazard_response=resp,
        )

        for h in resp.hazards:
            if is_alert_state(h.state):
                confirmed_hazards.append(h)

        if assessment.events:
            for ev in assessment.events:
                if ev.details.get("priority") in ("P0", "P1"):
                    emergency_events.append(ev)

    assert len(confirmed_hazards) == 0, (
        f"Scenario '{scenario}' produced false confirmed hazards: "
        f"{[h.event_id for h in confirmed_hazards]}"
    )
    assert len(emergency_events) == 0, (
        f"Scenario '{scenario}' triggered emergency alarms: "
        f"{[ev.event_type for ev in emergency_events]}"
    )


def test_candidate_decay_on_vanishing_transient(hazard_engine):
    """
    Verifies that an isolated 1-frame transient detection does NOT reach
    CONFIRMED, and decays safely to NO_HAZARD after max_gap_frames.
    """
    from app.ai.hazards.tracker import HazardTrack
    from app.ai.hazards.schemas import HazardType, HazardState
    from app.ai.hazards.temporal import TemporalHazardStateMachine

    sm = TemporalHazardStateMachine(hazard_engine.config)
    track = HazardTrack(
        event_id="HAZARD-NOISE",
        hazard_type=HazardType.SMOKE,
        bbox=np.array([100, 100, 200, 200]),
        confidence=0.40,
        frame_idx=1,
        camera_id="camera_01",
        zone_id="production_floor",
    )

    # Frame 1: CANDIDATE
    st1 = sm.evaluate_track_state(track)
    assert st1 == HazardState.CANDIDATE
    assert not is_alert_state(st1)

    # Vanishes for gap tolerance frames
    for _ in range(sm.smoke_max_gap_frames + 2):
        track.mark_missed()
        st = sm.evaluate_track_state(track)

    # Must decay to NO_HAZARD
    assert st == HazardState.NO_HAZARD
    assert sm.event_states["HAZARD-NOISE"] == HazardState.NO_HAZARD
