# System Monitoring & Observability

SafeSync exposes comprehensive health checks, real-time performance telemetry, Prometheus scrape endpoints, and structured logging for production operations and container orchestration.

---

## 1. Health Probes & Readiness Architecture

```
                               ┌───────────────────────────┐
                               │  Kubernetes / Ingress     │
                               └─────────────┬─────────────┘
                                             │ HTTP
                      ┌──────────────────────┼──────────────────────┐
                      │                      │                      │
                      ▼                      ▼                      ▼
             GET /health/live        GET /health/ready         GET /metrics
             (Liveness Probe)       (Readiness Probe)      (Prometheus Scrape)
                      │                      │                      │
                      ▼                      ▼                      ▼
        ┌───────────────────────────┐ ┌──────────────────────────┐ ┌───────────────────────────┐
        │ Process Uptime & Liveness │ │ Deep Subsystem Checks:   │ │ MetricsCollector          │
        │ - HTTP 200: Healthy       │ │ - SQLite WAL Database    │ │ - Frames & Dropped Counts │
        │                           │ │ - AI Model Availability  │ │ - Class Detections        │
        │                           │ │ - Storage Disk Quota     │ │ - Incidents & Alerts      │
        │                           │ │ - Multi-Camera Workers   │ │ - System CPU & Memory RSS │
        └───────────────────────────┘ └──────────────────────────┘ └───────────────────────────┘
```

---

## 2. Health Check Endpoints

| Endpoint | Method | Success Code | Failure Code | Description |
|---|---|---|---|---|
| `/health/live` | `GET` | `200 OK` | `500` / Timeout | Verifies FastAPI process responsiveness. |
| `/health/ready` | `GET` | `200 OK` | `503 Service Unavailable` | Deep readiness probe verifying database, model weights, and camera subsystems. |
| `/health/database` | `GET` | `200 OK` | `503 Service Unavailable` | Checks SQLite WAL mode, foreign keys, and connectivity. |

### Sample Readiness Response (`GET /health/ready`)
```json
{
  "status": "ready",
  "service": "SafeSync",
  "checks": {
    "database": "connected",
    "ai_model": "loaded",
    "storage": "available",
    "camera_subsystem": "operational"
  },
  "timestamp": "2026-09-21T18:25:30.123456+00:00"
}
```

---

## 3. Prometheus Metrics (`GET /metrics`)

The system exports standard Prometheus text format metrics:

```prometheus
# HELP safesync_pipeline_frames_total Total video frames processed by camera
# TYPE safesync_pipeline_frames_total counter
safesync_pipeline_frames_total{camera_id="camera_01"} 14250.0

# HELP safesync_pipeline_dropped_frames_total Total corrupted or dropped frames
# TYPE safesync_pipeline_dropped_frames_total counter
safesync_pipeline_dropped_frames_total{camera_id="camera_01"} 3.0

# HELP safesync_inference_latency_seconds Latency of neural detection pass
# TYPE safesync_inference_latency_seconds gauge
safesync_inference_latency_seconds{model="ppe_fire_smoke_v2"} 0.0382

# HELP safesync_active_workers Current detected workers tracked across cameras
# TYPE safesync_active_workers gauge
safesync_active_workers{zone="zone_a"} 4.0

# HELP safesync_incidents_total Total safety incidents created by event type
# TYPE safesync_incidents_total counter
safesync_incidents_total{event_type="MISSING_HELMET"} 12.0
safesync_incidents_total{event_type="FIRE_DETECTED"} 0.0
```

---

## 4. Structured Logging & Rotation

- **Format:** Structured JSON logging in production mode (`configs/production.yaml`).
- **Rotation Policy:** 50 MB max file size with 5 backup generations (`RotatingFileHandler`).
- **Log Location:** `logs/safesync.log`.
- **Sensitive Data Redaction:** URL credentials and auth tokens are stripped prior to writing to disk.
