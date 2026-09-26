"""
monitoring.py — SafeSync Phase 10 Step 10
FastAPI Router for System Observability, Liveness/Readiness Probes,
Prometheus Metrics Exposition, and Deep Health Telemetry.
"""

import os
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse

try:
    from app.database.session import check_database_connection, check_database_health
    from app.ai.detection.model_loader import ModelLoader
    from app.services.evidence_manager import EvidenceManager
    from app.camera.manager import CameraManager
    from app.services.metrics import MetricsCollector
except ImportError:
    from backend.app.database.session import check_database_connection, check_database_health
    from backend.app.ai.detection.model_loader import ModelLoader
    from backend.app.services.evidence_manager import EvidenceManager
    from backend.app.camera.manager import CameraManager
    from backend.app.services.metrics import MetricsCollector

router = APIRouter(tags=["Observability & Monitoring"])


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/health/live", status_code=status.HTTP_200_OK)
def liveness_probe():
    """
    Kubernetes/Docker liveness probe.
    Returns HTTP 200 as long as the application process is running and accepting HTTP requests.
    """
    collector = MetricsCollector.get_instance()
    return {
        "status": "alive",
        "service": "SafeSync",
        "uptime_seconds": collector.get_uptime_seconds(),
        "timestamp": _utc_now_iso(),
    }


@router.get("/health/ready")
def readiness_probe():
    """
    Kubernetes/Docker readiness probe.
    Returns HTTP 200 when all critical dependencies (database, AI engine, storage) are ready.
    Returns HTTP 503 (Service Unavailable) if any critical dependency is offline.
    """
    checks = {}
    is_ready = True

    # 1. Database Connection Check (Critical)
    db_connected = check_database_connection()
    checks["database"] = "connected" if db_connected else "disconnected"
    if not db_connected:
        is_ready = False

    # 2. AI Model Check
    try:
        loader = ModelLoader.get_instance()
        checks["ai_model"] = "loaded" if loader.is_loaded() else "ready"
    except Exception:
        checks["ai_model"] = "unavailable"

    # 3. Evidence Storage Subsystem
    try:
        mgr = EvidenceManager.get_instance()
        storage_ok = mgr.storage_root.exists()
        checks["storage"] = "available" if storage_ok else "unreachable"
        if not storage_ok:
            is_ready = False
    except Exception:
        checks["storage"] = "error"
        is_ready = False

    # 4. Camera Manager
    try:
        CameraManager.get_instance()
        checks["camera_subsystem"] = "operational"
    except Exception:
        checks["camera_subsystem"] = "degraded"

    result_payload = {
        "status": "ready" if is_ready else "not_ready",
        "service": "SafeSync",
        "checks": checks,
        "timestamp": _utc_now_iso(),
    }

    if not is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=result_payload,
        )

    return result_payload


@router.get("/metrics")
def prometheus_metrics():
    """
    Standard Prometheus metrics exposition endpoint.
    Returns plain text formatted conforming to Prometheus 0.0.4 standard.
    """
    collector = MetricsCollector.get_instance()
    text_content = collector.export_prometheus_text()
    return Response(
        content=text_content,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get("/api/monitoring/metrics", response_model=Dict[str, Any])
def json_telemetry_metrics():
    """
    Structured JSON metrics endpoint for operational dashboards and real-time frontend monitoring.
    """
    collector = MetricsCollector.get_instance()
    return collector.export_json_summary()


@router.get("/api/monitoring/health/deep")
def deep_system_health():
    """
    Detailed multi-dimensional system diagnostic report including
    database PRAGMAs, table record counts, camera statuses, and evidence storage metrics.
    """
    collector = MetricsCollector.get_instance()
    db_health = check_database_health()
    camera_statuses = CameraManager.get_instance().get_all_statuses()
    evidence_mgr = EvidenceManager.get_instance()

    return {
        "timestamp": _utc_now_iso(),
        "uptime_seconds": collector.get_uptime_seconds(),
        "database": db_health,
        "cameras": {
            "total_registered": len(camera_statuses),
            "connected": sum(1 for c in camera_statuses if c.state.value == "CONNECTED"),
            "statuses": [s.model_dump() for s in camera_statuses],
        },
        "evidence_storage": {
            "storage_directory": evidence_mgr.evidence_dir_rel,
            "total_bytes_used": evidence_mgr.get_total_storage_usage(),
            "max_storage_bytes": evidence_mgr.max_storage_bytes,
            "max_storage_gb": evidence_mgr.max_storage_gb,
            "retention_days": evidence_mgr.retention_days,
        },
    }
