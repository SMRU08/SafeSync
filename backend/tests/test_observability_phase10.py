"""
test_observability_phase10.py — RAKSHYA VISION Phase 10 Step 10
Unit & Integration Test Suite for Observability, Liveness/Readiness Probes,
Prometheus Metrics, JSON Telemetry, and Structured Logging.
"""

import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.metrics import MetricsCollector
from app.config import get_settings, setup_production_logging

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_metrics():
    MetricsCollector.reset_instance()
    yield
    MetricsCollector.reset_instance()


def test_liveness_probe():
    """Verifies GET /health/live returns HTTP 200 with status 'alive' and uptime."""
    resp = client.get("/health/live")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "alive"
    assert data["service"] == "RAKSHYA VISION"
    assert isinstance(data["uptime_seconds"], (int, float))
    assert "timestamp" in data


def test_readiness_probe_healthy():
    """Verifies GET /health/ready returns HTTP 200 when all core components are available."""
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert "checks" in data
    assert data["checks"]["database"] == "connected"
    assert data["checks"]["storage"] == "available"
    assert data["checks"]["camera_subsystem"] == "operational"


def test_readiness_probe_unhealthy():
    """Verifies GET /health/ready returns HTTP 503 if database check fails."""
    with patch("app.api.monitoring.check_database_connection", return_value=False):
        resp = client.get("/health/ready")
        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "not_ready"
        assert data["checks"]["database"] == "disconnected"


def test_prometheus_metrics_format():
    """Verifies GET /metrics outputs compliant Prometheus 0.0.4 text format with help/type annotations."""
    collector = MetricsCollector.get_instance()
    collector.increment_counter("rakshya_pipeline_frames_total", value=5, labels={"camera_id": "CAM_01"})
    collector.increment_counter("rakshya_incidents_total", value=1, labels={"risk_level": "HIGH", "camera_id": "CAM_01"})

    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    text = resp.text

    # Verify standard Prometheus header formatting
    assert "# HELP rakshya_pipeline_frames_total" in text
    assert "# TYPE rakshya_pipeline_frames_total counter" in text
    assert 'rakshya_pipeline_frames_total{camera_id="CAM_01"} 5' in text
    assert "# HELP rakshya_uptime_seconds" in text
    assert "# TYPE rakshya_uptime_seconds gauge" in text


def test_json_telemetry_metrics():
    """Verifies GET /api/monitoring/metrics returns clean structured operational telemetry."""
    collector = MetricsCollector.get_instance()
    collector.increment_counter("rakshya_alerts_total", value=2, labels={"severity": "CRITICAL", "event_type": "FIRE_DETECTED"})

    resp = client.get("/api/monitoring/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "uptime_seconds" in data
    assert "system_resources" in data
    assert "counters" in data
    assert "gauges" in data
    assert "rakshya_alerts_total" in data["counters"]
    entry = data["counters"]["rakshya_alerts_total"][0]
    assert entry["labels"]["severity"] == "CRITICAL"
    assert entry["value"] == 2.0


def test_deep_system_health():
    """Verifies GET /api/monitoring/health/deep returns multi-dimensional diagnostic report."""
    resp = client.get("/api/monitoring/health/deep")
    assert resp.status_code == 200
    data = resp.json()
    assert "database" in data
    assert "cameras" in data
    assert "evidence_storage" in data
    assert "total_bytes_used" in data["evidence_storage"]
    assert "total_registered" in data["cameras"]


def test_metrics_collector_unit():
    """Unit test for thread-safe MetricsCollector counters and gauges."""
    collector = MetricsCollector.get_instance()
    collector.increment_counter("test_counter", 10.0, labels={"env": "prod"})
    collector.increment_counter("test_counter", 5.0, labels={"env": "prod"})
    collector.set_gauge("test_gauge", 99.5, labels={"zone": "ZONE_A"})

    summary = collector.export_json_summary()
    assert summary["counters"]["test_counter"][0]["value"] == 15.0
    assert summary["gauges"]["test_gauge"][0]["value"] == 99.5


def test_structured_logging_initialization():
    """Verifies production structured logging setup executes safely without errors."""
    setup_production_logging()
    settings = get_settings()
    assert settings.LOG_MAX_BYTES > 0
    assert settings.LOG_BACKUP_COUNT > 0
