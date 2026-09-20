import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "RAKSHYA VISION"
    assert data["status"] == "running"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["ai_engine"] == "Not Connected"


def test_invalid_endpoint_returns_404():
    response = client.get("/non-existent-route")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_invalid_method_returns_405():
    response = client.post("/health", json={"dummy": "value"})
    assert response.status_code == 405
