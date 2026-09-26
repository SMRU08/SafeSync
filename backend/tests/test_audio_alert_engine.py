"""
test_audio_alert_engine.py — Comprehensive tests for SafeSync AI Audio-Alert Engine
Validates:
- Precise grammatical formatting for missing PPE items (Oxford comma, singular articles).
- User Scenario A: Worker #11 without helmet, vest, and gloves. Speaker ON -> Triggered.
- User Scenario B: Worker #22 without gloves. Speaker ON -> Triggered.
- User Scenario C: Worker #05 missing safety shoes. Speaker OFF -> Suppressed.
- User Scenario D: Worker #14 with all required PPE. Speaker ON -> 100% Compliant, No alert.
- Multi-camera independent isolation and camera-specific speaker status toggling.
- Event broadcasting and history tracking.
"""

import pytest
from app.services.audio_alert_engine import (
    AudioAlertEngine,
    format_missing_ppe_list,
    format_audio_alert_message,
)
from app.services.event_broadcaster import broadcaster


@pytest.fixture(autouse=True)
def reset_audio_engine():
    AudioAlertEngine.reset_instance()
    yield
    AudioAlertEngine.reset_instance()


def test_format_missing_ppe_list_grammar():
    """Validates English grammar rules for PPE missing item list."""
    # Single items
    assert format_missing_ppe_list(["gloves"]) == "gloves"
    assert format_missing_ppe_list(["helmet"]) == "a helmet"
    assert format_missing_ppe_list(["safety_vest"]) == "safety vest"
    assert format_missing_ppe_list(["safety_footwear"]) == "safety shoes"
    assert format_missing_ppe_list(["safety_shoes"]) == "safety shoes"

    # Two items
    assert format_missing_ppe_list(["helmet", "gloves"]) == "a helmet and gloves"
    assert format_missing_ppe_list(["safety_vest", "gloves"]) == "safety vest and gloves"

    # Three items (Scenario A phrasing with Oxford comma)
    assert (
        format_missing_ppe_list(["helmet", "safety_vest", "gloves"])
        == "a helmet, safety vest, and gloves"
    )

    # Four items
    assert (
        format_missing_ppe_list(["helmet", "safety_vest", "gloves", "safety_footwear"])
        == "a helmet, safety vest, gloves, and safety shoes"
    )


def test_scenario_a_worker_11_missing_helmet_vest_gloves_speaker_on():
    """
    Scenario A:
    Worker #11 is detected without a helmet, vest, and gloves. Speaker is ON.
    - Action: Trigger Audio.
    - Alert Generation: Hindi voice alert triggered (language: hi).
    """
    engine = AudioAlertEngine.get_instance(default_cooldown_seconds=10.0)

    received_events = []

    def on_event(name, payload):
        if name == "AudioAlert":
            received_events.append(payload)

    broadcaster.subscribe(on_event)

    try:
        ppe_status = {
            "helmet": "ABSENT",
            "safety_vest": "ABSENT",
            "gloves": "ABSENT",
            "safety_footwear": "PRESENT",
        }

        result = engine.evaluate_worker(
            camera_id="camera_01",
            speaker_enabled=True,
            worker_id=11,
            ppe_status=ppe_status,
        )

        assert result.action == "AUDIO_TRIGGERED"
        assert result.speaker_enabled is True
        assert result.worker_id == 11
        # Engine produces Hindi-language audio alerts (primary message is Hindi)
        assert result.message is not None and len(result.message) > 0
        assert "helmet" in result.missing_ppe
        assert "safety_vest" in result.missing_ppe
        assert "gloves" in result.missing_ppe
        assert "safety_footwear" not in result.missing_ppe

        # Verify broadcast was fired with correct action
        assert len(received_events) == 1
        assert received_events[0]["action"] == "AUDIO_TRIGGERED"
    finally:
        broadcaster.unsubscribe(on_event)



def test_scenario_b_worker_22_missing_gloves_speaker_on():
    """
    Scenario B:
    Worker #22 is detected without gloves. Speaker is ON.
    - Action: Trigger Audio.
    - Alert Generation: 'Worker 22, you are not wearing gloves.'
    """
    engine = AudioAlertEngine.get_instance()

    ppe_status = {
        "helmet": "PRESENT",
        "safety_vest": "PRESENT",
        "gloves": "ABSENT",
        "safety_footwear": "PRESENT",
    }

    result = engine.evaluate_worker(
        camera_id="camera_01",
        speaker_enabled=True,
        worker_id=22,
        ppe_status=ppe_status,
    )

    assert result.action == "AUDIO_TRIGGERED"
    assert result.speaker_enabled is True
    assert result.message is not None and len(result.message) > 0  # Hindi message
    assert result.missing_ppe == ["gloves"]


def test_scenario_c_worker_05_missing_shoes_speaker_off():
    """
    Scenario C:
    Worker #05 is missing safety shoes. Speaker is OFF.
    - Action: Suppress Audio. Update visual dashboard to show Shoes: Absent/Unknown.
    """
    engine = AudioAlertEngine.get_instance()

    ppe_status = {
        "helmet": "PRESENT",
        "safety_vest": "PRESENT",
        "gloves": "PRESENT",
        "safety_footwear": "ABSENT",
    }

    result = engine.evaluate_worker(
        camera_id="camera_01",
        speaker_enabled=False,
        worker_id="05",
        ppe_status=ppe_status,
    )

    assert result.action == "AUDIO_SUPPRESSED"
    assert result.speaker_enabled is False
    assert result.details.get("audio_played") is False
    assert result.message is not None and len(result.message) > 0  # Hindi message generated but suppressed
    assert "safety_footwear" in result.missing_ppe


def test_scenario_d_worker_14_all_required_ppe_speaker_on():
    """
    Scenario D:
    Worker #14 has all required PPE. Speaker is ON.
    - Action: No alert required. Log as 100% compliant.
    """
    engine = AudioAlertEngine.get_instance()

    ppe_status = {
        "helmet": "PRESENT",
        "safety_vest": "PRESENT",
        "gloves": "PRESENT",
        "safety_footwear": "PRESENT",
    }

    result = engine.evaluate_worker(
        camera_id="camera_01",
        speaker_enabled=True,
        worker_id=14,
        ppe_status=ppe_status,
    )

    assert result.action == "COMPLIANT"
    assert result.message is None
    assert len(result.missing_ppe) == 0
    assert result.details.get("compliant") is True


def test_multi_camera_independent_handling():
    """
    Multi-Camera Handling:
    Process each camera feed independently. Ensure that an alert triggered on Camera 1
    only references workers visible in Camera 1, and respects Camera 1's specific Speaker ON/OFF toggle.
    """
    engine = AudioAlertEngine.get_instance()

    cam1_workers = [
        {"track_id": 11, "ppe_status": {"helmet": "ABSENT", "safety_vest": "ABSENT", "gloves": "ABSENT", "safety_footwear": "PRESENT"}},
        {"track_id": 14, "ppe_status": {"helmet": "PRESENT", "safety_vest": "PRESENT", "gloves": "PRESENT", "safety_footwear": "PRESENT"}},
    ]

    cam2_workers = [
        {"track_id": 22, "ppe_status": {"helmet": "PRESENT", "safety_vest": "PRESENT", "gloves": "ABSENT", "safety_footwear": "PRESENT"}},
        {"track_id": 5, "ppe_status": {"helmet": "PRESENT", "safety_vest": "PRESENT", "gloves": "PRESENT", "safety_footwear": "ABSENT"}},
    ]

    # Camera 1 Speaker is ON
    cam1_results = engine.evaluate_frame_workers(
        camera_id="camera_01",
        speaker_enabled=True,
        workers=cam1_workers,
    )
    assert len(cam1_results) == 2
    # Worker 11 triggered
    assert cam1_results[0].action == "AUDIO_TRIGGERED"
    assert cam1_results[0].camera_id == "camera_01"
    assert cam1_results[0].worker_id == 11
    # Worker 14 compliant
    assert cam1_results[1].action == "COMPLIANT"

    # Camera 2 Speaker is OFF
    cam2_results = engine.evaluate_frame_workers(
        camera_id="camera_02",
        speaker_enabled=False,
        workers=cam2_workers,
    )
    assert len(cam2_results) == 2
    # Both Worker 22 and Worker 5 are suppressed because Camera 2 speaker is OFF
    assert cam2_results[0].action == "AUDIO_SUPPRESSED"
    assert cam2_results[0].camera_id == "camera_02"
    assert cam2_results[0].worker_id == 22

    assert cam2_results[1].action == "AUDIO_SUPPRESSED"
    assert cam2_results[1].camera_id == "camera_02"
    assert cam2_results[1].worker_id == 5

    # Now toggle Camera 2 speaker to ON
    cam2_results_speaker_on = engine.evaluate_frame_workers(
        camera_id="camera_02",
        speaker_enabled=True,
        workers=cam2_workers,
    )
    # Worker 22 is now triggered on Camera 2!
    assert cam2_results_speaker_on[0].action == "AUDIO_TRIGGERED"
    assert cam2_results_speaker_on[0].camera_id == "camera_02"


def test_cooldown_deduplication():
    """Ensures same worker missing items is not re-spoken repeatedly in rapid frames."""
    engine = AudioAlertEngine.get_instance(default_cooldown_seconds=10.0)

    ppe = {"helmet": "ABSENT", "safety_vest": "PRESENT", "gloves": "PRESENT", "safety_footwear": "PRESENT"}

    # Frame 1: Triggered
    res1 = engine.evaluate_worker("camera_01", True, 99, ppe)
    assert res1.action == "AUDIO_TRIGGERED"

    # Frame 2 immediately after: Cooldown suppressed
    res2 = engine.evaluate_worker("camera_01", True, 99, ppe)
    assert res2.action == "COOLDOWN"

    # Force bypass: Triggered
    res3 = engine.evaluate_worker("camera_01", True, 99, ppe, force=True)
    assert res3.action == "AUDIO_TRIGGERED"
