"""
test_alarm_priority.py — RAKSHYA VISION Safety Intelligence Pipeline
Tests for AlarmEngine priorities (P0, P1, P2, P3), audible siren policies, deduplication, and cooldowns.
"""

import pytest
import uuid
from datetime import datetime, timezone
from app.services.alert_engine import AlertEngine
from app.services.risk_engine import RiskEngine
from app.ai.risk.schemas import EventType, RiskLevel, AlarmPriority, NormalizedSafetyEvent


@pytest.fixture
def alert_engine():
    return AlertEngine()


def test_priority_assignment_fire_p0(alert_engine):
    """Fire events must always be P0 with audible siren enabled."""
    ev = NormalizedSafetyEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.FIRE_DETECTED,
        timestamp=datetime.now(timezone.utc).isoformat(),
        camera_id="camera_01",
        zone_id="electrical_room",
        confidence=0.92,
        duration_seconds=3.0,
    )
    risk = alert_engine.risk_engine.evaluate(event_type=ev.event_type)
    priority, audible = alert_engine._get_priority_for_event(ev, risk)
    assert priority == AlarmPriority.P0
    assert audible is True


def test_priority_assignment_smoke_p1_and_escalation(alert_engine):
    """Smoke events start at P1 with siren, escalating to P0 if persistent >= 10s."""
    ev_short = NormalizedSafetyEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.SMOKE_DETECTED,
        timestamp=datetime.now(timezone.utc).isoformat(),
        camera_id="camera_01",
        zone_id="production_floor",
        confidence=0.80,
        duration_seconds=4.0,
    )
    risk_short = alert_engine.risk_engine.evaluate(event_type=ev_short.event_type, duration_seconds=4.0)
    p_short, aud_short = alert_engine._get_priority_for_event(ev_short, risk_short)
    assert p_short == AlarmPriority.P1
    assert aud_short is True

    ev_long = NormalizedSafetyEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.SMOKE_DETECTED,
        timestamp=datetime.now(timezone.utc).isoformat(),
        camera_id="camera_01",
        zone_id="production_floor",
        confidence=0.85,
        duration_seconds=12.0,
    )
    risk_long = alert_engine.risk_engine.evaluate(event_type=ev_long.event_type, duration_seconds=12.0)
    p_long, aud_long = alert_engine._get_priority_for_event(ev_long, risk_long)
    assert p_long == AlarmPriority.P0
    assert aud_long is True


def test_priority_assignment_ppe_violations_p2_no_siren(alert_engine):
    """PPE violations must be P2 with audible siren STRICTLY disabled."""
    for ppe_type in [
        EventType.MISSING_HELMET,
        EventType.MISSING_SAFETY_VEST,
        EventType.MISSING_GLOVES,
        EventType.MISSING_SAFETY_FOOTWEAR,
        EventType.PPE_VIOLATION,
    ]:
        ev = NormalizedSafetyEvent(
            event_id=str(uuid.uuid4()),
            event_type=ppe_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            camera_id="camera_01",
            zone_id="loading_dock",
            track_id=42,
            confidence=0.88,
            duration_seconds=5.0,
        )
        risk = alert_engine.risk_engine.evaluate(event_type=ev.event_type)
        priority, audible = alert_engine._get_priority_for_event(ev, risk)
        assert priority == AlarmPriority.P2, f"Failed for {ppe_type}"
        assert audible is False, f"PPE violation {ppe_type} must NOT have audible siren"


def test_priority_assignment_system_advisory_p3(alert_engine):
    """Camera failure and system failure must be P3 with audible siren disabled."""
    for sys_type in [EventType.CAMERA_FAILURE, EventType.SYSTEM_FAILURE]:
        ev = NormalizedSafetyEvent(
            event_id=str(uuid.uuid4()),
            event_type=sys_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            camera_id="camera_01",
            zone_id="loading_dock",
            confidence=1.0,
        )
        risk = alert_engine.risk_engine.evaluate(event_type=ev.event_type)
        priority, audible = alert_engine._get_priority_for_event(ev, risk)
        assert priority == AlarmPriority.P3
        assert audible is False


def test_alert_engine_cooldown_suppression(alert_engine):
    """Repeated alerts for same target within cooldown window are suppressed."""
    ev = NormalizedSafetyEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.MISSING_HELMET,
        timestamp=datetime.now(timezone.utc).isoformat(),
        camera_id="camera_01",
        zone_id="loading_dock",
        track_id=99,
        confidence=0.85,
        duration_seconds=2.0,
    )
    # First alert -> CREATED
    alert1, inc1, action1 = alert_engine.process_event(ev)
    assert action1 == "CREATED"
    assert alert1 is not None
    assert alert1.priority == AlarmPriority.P2
    assert alert1.is_audible is False

    # Second alert immediately after -> COOLDOWN_SUPPRESSED
    alert2, inc2, action2 = alert_engine.process_event(ev)
    assert action2 == "COOLDOWN_SUPPRESSED"
    assert alert2 is None
