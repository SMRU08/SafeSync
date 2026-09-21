# RAKSHYA VISION — Phase 10 Step 10: Observability, Metrics & Operational Monitoring

## 1. Executive Summary
Phase 10 Step 10 establishes a unified observability and operational monitoring subsystem for RAKSHYA VISION. The subsystem exposes standard Kubernetes/Docker liveness and readiness probes, exports Prometheus 0.0.4 metrics, serves structured JSON telemetry for dashboard visualizations, performs multi-dimensional deep health diagnostics, and provides bounded rotating file logging.

---

## 2. Observability Architecture

```
                               ┌───────────────────────────┐
                               │  Kubernetes / K8s Ingress │
                               └─────────────┬─────────────┘
                                             │ HTTP
                      ┌──────────────────────┼──────────────────────┐
                      │                      │                      │
                      ▼                      ▼                      ▼
             GET /health/live        GET /health/ready         GET /metrics
             (Liveness Probe)       (Readiness Probe)      (Prometheus Scrape)
                      │                      │                      │
                      │                      │                      │
                      ▼                      ▼                      ▼
┌───────────────────────────┐ ┌──────────────────────────┐ ┌───────────────────────────┐
│ Process Uptime & Liveness │ │ Deep Subsystem Checks:   │ │ MetricsCollector          │
│ - HTTP 200: Healthy       │ │ - SQLite WAL Database    │ │ - Frames & Dropped Counts │
│                           │ │ - AI Model Availability  │ │ - Class Detections        │
│                           │ │ - Evidence Storage Root  │ │ - Incidents & Alerts      │
│                           │ │ - Multi-Camera Workers   │ │ - External Dispatches     │
│                           │ │ => HTTP 200 / HTTP 503   │ │ - System CPU & Memory RSS │
└───────────────────────────┘ └──────────────────────────┘ └───────────────────────────┘
```

---

## 3. Endpoints & API Reference

### 3.1 Probes
| Endpoint | Method | Success Code | Failure Code | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `/health/live` | `GET` | `200 OK` | `500` / Timeout | Fast liveness probe verifying process responsiveness. |
| `/health/ready` | `GET` | `200 OK` | `503 Service Unavailable` | Deep readiness probe verifying database, AI weights, and storage. |

#### Sample Readiness Response (Healthy):
```json
{
  "status": "ready",
  "service": "RAKSHYA VISION",
  "checks": {
    "database": "connected",
    "ai_model": "loaded",
    "storage": "available",
    "camera_subsystem": "operational"
  },
  "timestamp": "2026-09-21T18:25:30.123456+00:00"
}
```

### 3.2 Metrics & Telemetry
| Endpoint | Method | Format | Description |
| :--- | :--- | :--- | :--- |
| `/metrics` | `GET` | `text/plain; version=0.0.4` | Prometheus scraping endpoint conforming strictly to Prometheus standard format. |
| `/api/monitoring/metrics` | `GET` | `application/json` | Consolidated JSON telemetry report for dashboards and operational alerts. |
| `/api/monitoring/health/deep` | `GET` | `application/json` | Multi-dimensional diagnostics: DB PRAGMAs, table record counts, camera worker states, and storage utilization. |

---

## 4. Exported Prometheus Metrics Inventory

| Metric Name | Type | Description | Labels |
| :--- | :--- | :--- | :--- |
| `rakshya_pipeline_frames_total` | Counter | Total video frames ingested and processed | `camera_id` |
| `rakshya_pipeline_dropped_frames_total` | Counter | Total video frames dropped due to buffer/inference lag | `camera_id` |
| `rakshya_detections_total` | Counter | Total AI object detections by class | `class_name` |
| `rakshya_incidents_total` | Counter | Total safety incidents created | `risk_level`, `camera_id` |
| `rakshya_alerts_total` | Counter | Total smart alerts generated | `severity`, `event_type` |
| `rakshya_alert_actions_total` | Counter | Lifecycle transitions | `action` (`CREATED`, `ACKNOWLEDGED`, `RESOLVED`, `DISMISSED`, `ESCALATED`) |
| `rakshya_alert_dispatches_total` | Counter | External notification delivery attempts | `provider`, `status` (`success`, `failed`, `error`) |
| `rakshya_camera_workers_active` | Gauge | Active camera worker threads | None |
| `rakshya_evidence_storage_bytes` | Gauge | Current filesystem bytes consumed by evidence artifacts | None |
| `rakshya_uptime_seconds` | Gauge | Running time of RAKSHYA VISION service in seconds | None |
| `rakshya_process_cpu_percent` | Gauge | Current process CPU utilization percentage | None |
| `rakshya_process_memory_rss_bytes` | Gauge | Process Resident Set Size memory consumption in bytes | None |

---

## 5. Structured Operational Logging

### Configuration (`configs/production.yaml`):
```yaml
logging:
  level: "INFO"
  format: "text"
  log_file: "outputs/logs/rakshya_vision.log"
  max_bytes: 10485760  # 10 MB
  backup_count: 5
```

### Guarantees:
- **Bounded Rotation**: Automatically rotates log files when reaching 10 MB, preserving up to 5 backups. Prevents unbounded disk consumption on edge deployments.
- **Consistent Format**: Standard timestamp, severity level, logger/module name, and message format.
- **Secret Redaction**: Zero API keys, passwords, or bearer tokens are printed to logs.

---

## 6. Verification Results
- **Observability Test Suite**: `backend/tests/test_observability_phase10.py` (8/8 PASSED).
- **Full Backend Pytest Regression**: 154/154 PASSED.
