import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    if response.headers.get("content-type", "").startswith("application/json"):
        data = response.json()
        assert data["project"] == "SafeSync"
        assert data["status"] == "running"
    else:
        assert "<!doctype html>" in response.text.lower() or "<html" in response.text.lower()


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    ai_status = data["ai_engine"]["status"] if isinstance(data["ai_engine"], dict) else data["ai_engine"]
    assert ai_status in ("healthy", "Connected", "Ready", "Not Connected", "available", "Available")
    assert "api" in data
    assert "database" in data
    assert "websocket" in data


def test_invalid_endpoint_returns_404():
    response = client.get("/api/non-existent-route")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_invalid_method_returns_405():
    response = client.post("/health", json={"dummy": "value"})
    assert response.status_code == 405
