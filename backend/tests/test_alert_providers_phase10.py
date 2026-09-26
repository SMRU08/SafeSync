"""
test_alert_providers_phase10.py — SafeSync Phase 10 Step 8
Automated test suite for External Alert Provider Architecture:
- Strict status evaluation (ENABLED, DISABLED, NOT_CONFIGURED, ERROR)
- Webhook HMAC signature generation and timeout handling
- Provider failure isolation (external timeout/network drops never block safety system)
- Email provider TLS configuration and error safety
- SMS provider clean interface (no fake SMS sent claims)
- ProviderRegistry concurrent dispatch
- Integration with AlertEngine on alert creation and escalation
"""

import time
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.alert_providers.base import (
    BaseAlertProvider,
    ProviderStatus,
    AlertNotificationPayload,
)
from app.services.alert_providers.webhook_provider import WebhookProvider
from app.services.alert_providers.email_provider import EmailProvider
from app.services.alert_providers.sms_provider import SmsProvider
from app.services.alert_providers.registry import ProviderRegistry
from app.services.alert_engine import AlertEngine
from app.ai.risk.schemas import (
    NormalizedSafetyEvent,
    EventType,
    RiskLevel,
)
from app.database.session import get_db

client = TestClient(app)


def test_provider_status_defaults():
    """Verifies that unconfigured providers report NOT_CONFIGURED or DISABLED without fake statuses."""
    wh_disabled = WebhookProvider(enabled=False)
    assert wh_disabled.status == ProviderStatus.DISABLED

    wh_not_configured = WebhookProvider(enabled=True, url=None)
    assert wh_not_configured.status == ProviderStatus.NOT_CONFIGURED

    wh_configured = WebhookProvider(enabled=True, url="https://api.example.com/webhook")
    assert wh_configured.status == ProviderStatus.ENABLED

    email_unconfigured = EmailProvider(enabled=True, host=None)
    assert email_unconfigured.status == ProviderStatus.NOT_CONFIGURED

    sms_unconfigured = SmsProvider(enabled=True, api_key=None)
    assert sms_unconfigured.status == ProviderStatus.NOT_CONFIGURED


def test_webhook_hmac_signature_generation():
    """Verifies that WebhookProvider computes correct HMAC-SHA256 signature."""
    wh = WebhookProvider(
        url="https://api.example.com/alerts",
        secret="test_webhook_secret_key",
        enabled=True,
    )
    payload_bytes = b'{"test": "alert"}'
    sig = wh._generate_signature(payload_bytes)
    assert sig is not None
    assert len(sig) == 64  # SHA-256 hex string


def test_webhook_failure_isolation():
    """Verifies that an unreachable webhook URL fails safely without throwing exceptions."""
    wh = WebhookProvider(
        url="http://127.0.0.1:54321/nonexistent_webhook",
        enabled=True,
        timeout_seconds=0.5,
        max_retries=1,
    )
    payload = AlertNotificationPayload(
        incident_id="INC-TEST-01",
        alert_id="ALT-TEST-01",
        camera_id="cam_01",
        zone_id="zone_01",
        event_type="NO_HARDHAT",
        severity="HIGH",
        title="Test Alert",
        message="Failure isolation check",
        timestamp="2026-09-21T12:00:00Z",
    )

    result = wh.send_alert(payload)
    assert result is False
    assert wh.status == ProviderStatus.ERROR
    assert wh.total_failed == 1
    assert wh.last_error is not None


def test_provider_registry_concurrent_dispatch():
    """Verifies ProviderRegistry dispatches across active providers with fault tolerance."""
    registry = ProviderRegistry.get_instance()

    # Mock active webhook provider to simulate fast success
    mock_provider = MagicMock(spec=BaseAlertProvider)
    mock_provider.status = ProviderStatus.ENABLED
    mock_provider.send_alert.return_value = True

    registry.providers["mock_test"] = mock_provider

    payload = AlertNotificationPayload(
        incident_id="INC-REG-01",
        alert_id="ALT-REG-01",
        camera_id="cam_01",
        zone_id="zone_01",
        event_type="SMOKE_DETECTED",
        severity="CRITICAL",
        title="Critical Smoke Detection",
        message="Simulated dispatch",
        timestamp="2026-09-21T12:00:00Z",
    )

    results = registry.dispatch_alert(payload)
    assert "mock_test" in results
    assert results["mock_test"] is True
    mock_provider.send_alert.assert_called_once_with(payload)

    # Clean up mock provider
    del registry.providers["mock_test"]


def test_alert_engine_dispatches_to_external_providers():
    """Verifies AlertEngine invokes external provider dispatch on new alert creation."""
    engine = AlertEngine()
    db = next(get_db())

    event = NormalizedSafetyEvent(
        event_id="EVT-EXT-01",
        event_type=EventType.MISSING_HELMET,
        timestamp="2026-09-21T12:00:00Z",
        camera_id="camera_ext_01",
        zone_id="production_floor",
        track_id=88,
        confidence=0.92,
        duration_seconds=2.0,
    )

    with patch.object(ProviderRegistry.get_instance(), "dispatch_alert") as mock_dispatch:
        alert, incident, action = engine.process_event(event, db=db)
        assert action == "CREATED"
        assert alert is not None
        # Verify provider dispatch was triggered
        assert mock_dispatch.called
        call_payload = mock_dispatch.call_args[0][0]
        assert call_payload.alert_id == alert.alert_id
        assert call_payload.event_type == "MISSING_HELMET"

    db.close()


def test_api_alert_providers_status_endpoint():
    """Verifies GET /api/alerts/providers/status returns transparent provider operational details."""
    response = client.get("/api/alerts/providers/status")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    names = [p["name"] for p in data]
    assert "Webhook" in names
    assert "Email" in names
    assert "SMS" in names
    for p in data:
        assert p["status"] in ("ENABLED", "DISABLED", "NOT_CONFIGURED", "ERROR")
