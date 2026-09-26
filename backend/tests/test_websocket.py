"""
test_websocket.py — SafeSync Phase 8
Unit tests for the live WebSocket alert and event broadcaster router.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.event_broadcaster import broadcaster


@pytest.fixture
def client():
    return TestClient(app)


def test_websocket_connect_and_welcome(client):
    """
    Verifies that a WebSocket client can connect to /ws/alerts and receives the initial welcome frame.
    """
    with client.websocket_connect("/ws/alerts") as ws:
        data = ws.receive_json()
        assert data["type"] == "connected"
        assert "SafeSync" in data["message"]
        assert data["active_connections"] >= 1
        assert "timestamp" in data


def test_websocket_ping_pong_heartbeat(client):
    """
    Verifies bi-directional ping/pong heartbeat over WebSocket.
    """
    with client.websocket_connect("/ws/alerts") as ws:
        # Initial greeting
        welcome = ws.receive_json()
        assert welcome["type"] == "connected"

        # Send ping
        ws.send_json({"type": "ping"})
        response = ws.receive_json()
        assert response["type"] == "pong"
        assert "timestamp" in response


def test_websocket_event_broadcasting(client):
    """
    Verifies that calling broadcaster.broadcast pushes real-time events to connected WebSocket clients.
    """
    with client.websocket_connect("/ws/alerts") as ws:
        # Consume welcome
        _ = ws.receive_json()

        # Trigger an event via broadcaster
        test_payload = {
            "alert_id": "ALT-TEST-9999",
            "severity": "HIGH",
            "title": "Missing Helmet in Fabrication Bay",
            "event_type": "MISSING_HELMET",
        }
        broadcaster.broadcast("AlertCreated", test_payload)

        # Receive streamed event
        msg = ws.receive_json()
        assert msg["type"] == "event"
        assert msg["event"] == "AlertCreated"
        assert msg["payload"]["alert_id"] == "ALT-TEST-9999"
        assert msg["payload"]["severity"] == "HIGH"
        assert "timestamp" in msg
