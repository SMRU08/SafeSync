# RAKSHYA VISION — Phase 10 Production Audit & Gap Analysis

**Document ID:** DOC-PHASE10-AUDIT  
**System:** RAKSHYA VISION (AI Vision-Based Safety Monitoring System)  
**Author:** Production Engineering, Computer Vision, Security & DevOps Team  
**Date:** 2026-09-21  
**Status:** **AUDIT COMPLETED — BASELINE VERIFIED**  
**Canonical Repository:** `https://github.com/SMRU08/RAKSHYA-VISION.git`  

---

## 1. Audit Scope & Methodology

Before introducing any operational or deployment modifications in Phase 10, a comprehensive audit of the entire repository was conducted across 20 distinct technical dimensions:
1. Complete repository layout & tree
2. Backend architecture (`backend/app/`)
3. Frontend architecture (`frontend/src/`)
4. Model artifacts, registries, and weights (`models/`)
5. Configuration architecture (`configs/`)
6. Database persistence & schema (`backend/app/models/`, `backend/app/database/`)
7. Camera & video ingestion pipeline (`backend/app/ai/detection/video_processor.py`, scripts)
8. Multi-worker tracking engine (`backend/app/ai/compliance/tracker.py`)
9. Spatial PPE anatomical association (`backend/app/ai/compliance/association.py`)
10. Fire & smoke hazard detection and tracking (`backend/app/ai/hazards/`)
11. Explainable risk calculation engine (`backend/app/services/risk_engine.py`)
12. Smart alert lifecycle & cooldown engine (`backend/app/services/alert_engine.py`)
13. WebSocket broadcaster & subscription channel (`backend/app/api/websocket.py`)
14. Automated test coverage (`backend/tests/`, `scripts/testing/`)
15. Docker & containerization manifests (currently absent)
16. System documentation (`docs/`, `README.md`, `PROJECT_STATUS.md`)
17. Repository version control exclusions (`.gitignore`)
18. Secrets, credential management, and `.env` handling
19. Git history and commit log
20. GitHub remote configuration and upstream connectivity

---

## 2. What Already Works & What is Production-Capable

| Subsystem | Components | Production Capability Assessment |
|---|---|---|
| **AI Inference Engine** | `models/detection/ppe_fire_smoke_v2/weights/best.pt`, `ModelLoader`, `Detector` | **PRODUCTION CAPABLE.** Ultralytics YOLOv8n V2 checkpoint with 7 canonical classes verified via SHA-256 (`490a4867d0c9...`). Benchmarked at 32-41ms latency on CPU. |
| **Worker Tracking** | `ByteTrack`, `KalmanBoxTracker` | **PRODUCTION CAPABLE.** Multi-stage Kalman filter tracking assigns stable anonymous integer IDs with low-confidence matching and track buffer aging. |
| **PPE Association** | `SpatialPPEAssociator` | **PRODUCTION CAPABLE.** Anatomy-aware spatial association assigns helmet (head), vest (torso), gloves (hands), and footwear (feet) with IoU mutual exclusion. |
| **Temporal State Machine** | `TemporalComplianceTracker`, `TemporalHazardStateMachine` | **PRODUCTION CAPABLE.** $N_{\text{confirm}}=3$ for PPE, $N_{\text{confirm}}=5$ for hazards. Completely eliminates single-frame false alarms and transient flickers. |
| **Mandatory PPE Rule** | `EventNormalizer`, `TemporalComplianceTracker` | **PRODUCTION CAPABLE.** `UNKNOWN` state (occlusion / boundary clipping) **strictly never** triggers a violation. Only verified `ABSENT` generates incidents. |
| **Risk Scoring Engine** | `RiskEngine` | **PRODUCTION CAPABLE.** Deterministic 0..100 scoring with explainable factors (base severity, persistence, worker count, repetition, zone multipliers). |
| **Alert Deduplication & Cooldown** | `AlertEngine` | **PRODUCTION CAPABLE.** In-memory deduplication cache and configurable per-event cooldowns prevent alert flooding. Full `ACTIVE` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `RESOLVED` $\rightarrow$ `DISMISSED` lifecycle. |
| **Database Persistence** | SQLAlchemy ORM, SQLite (`rakshya_vision.db`) | **EDGE CAPABLE.** 5 core tables (`incidents`, `alerts`, `alert_history`, `hazard_events`, `worker_compliance_events`). Thread-safe sessions verified. |
| **WebSocket Streaming** | `EventBroadcaster`, `WebSocketManager` (`/ws/alerts`) | **PRODUCTION CAPABLE.** Pub/Sub streaming with bi-directional ping/pong heartbeat, automatic disconnect cleanup. |
| **Frontend SOC Dashboard** | React 18, TypeScript, Tailwind, Vite | **PRODUCTION CAPABLE.** 1,907 modules build cleanly into a minified bundle (233 kB JS, 28 kB CSS). Zero fabricated/fake data. |
| **Test Coverage** | Pytest (`backend/tests/`), Integration Runner (`scripts/testing/`) | **EXCELLENT.** 81/81 automated pytest tests passing, 39/39 integration scenarios passing. |

---

## 3. What is Incomplete

1. **Camera Lifecycle Management:**
   - Currently, cameras are statically defined in `configs/cameras.yaml` with dummy sources (`source: "configured_elsewhere"`).
   - There is no background worker pool managing multiple persistent camera streams (RTSP, USB, HTTP).
   - No explicit lifecycle states (`CONNECTED`, `CONNECTING`, `DISCONNECTED`, `RECONNECTING`, `ERROR`, `DISABLED`).
   - No per-camera FPS, dropped-frame counters, or automatic reconnection backoff loop running as a persistent background daemon.
2. **Dedicated Camera API Router:**
   - While frontend has `CamerasView.tsx`, it currently queries `fetchHazardConfig()` instead of a dedicated `/api/cameras` REST router.
3. **External Alert Delivery Providers:**
   - `AlertEngine` currently only dispatches events to internal WebSocket clients and database.
   - Outbound delivery mechanisms (Email, Webhook, SMS) do not have concrete provider abstractions (`AlertProvider`, `EmailAlertProvider`, `WebhookAlertProvider`).
4. **Hardware Acceleration Telemetry:**
   - Current health endpoint `/health` reports only basic connectivity. It does not inspect CPU usage, RAM utilization, GPU VRAM, CUDA capability, or inference device details.
5. **Database Productionization & Retention Maintenance:**
   - SQLite lacks explicit WAL (Write-Ahead Logging) mode configuration for concurrent camera writers.
   - No automated database retention or purge jobs exist (e.g. 7-day, 30-day, 90-day incident retention policies).
   - PostgreSQL connection string and dialect support are not documented or abstracted for enterprise scale.

---

## 4. What is Unsafe

1. **Lack of Authentication & Role-Based Access Control (RBAC):**
   - All REST endpoints (`/api/alerts`, `/api/detection`, `/api/hazards`, etc.) and WebSocket endpoints (`/ws/alerts`) are currently completely unauthenticated.
   - Any client on the network can acknowledge, resolve, or dismiss safety incidents.
   - Production requirement: Minimum of 3 roles: `ADMIN`, `OPERATOR`, `VIEWER`.
2. **Hard-coded Secret & Credential Risks:**
   - While `.gitignore` correctly ignores `.env`, no `.env.example` template exists to guide administrators on safely configuring RTSP credentials, JWT secret keys, or database URLs.
3. **CORS Permissiveness:**
   - CORS is configured to allow `localhost:5173`, `127.0.0.1:5173`, and `localhost:3000`. In a production edge deployment, origin filtering must be strictly bound to deployment hostnames and secure origins.

---

## 5. What is Missing

1. **Containerization & Deployment Manifests:**
   - No `Dockerfile` (multi-stage backend and frontend).
   - No `docker-compose.yml` orchestrating backend, frontend, and optional services.
   - No `systemd` service unit files (`rakshya-vision-backend.service`, `rakshya-vision-cameras.service`).
2. **Model Registry Architecture:**
   - Models are stored in raw directory structure (`models/detection/ppe_fire_smoke_v2/`).
   - Missing centralized `models/registry/model_registry.yaml` documenting active, candidate, and archived models with strict checksum verification before runtime loading.
3. **Automated Backup & Disaster Recovery:**
   - Missing `scripts/backup.py` and `scripts/restore.py` for database, models, configurations, and incident audit metadata.
4. **Production Smoke Test & Validation Command:**
   - Missing single-entrypoint scripts: `scripts/production_smoke_test.py` and `scripts/validate_production.py`.
5. **Observability & Metrics Endpoints:**
   - Missing `/metrics` or `/health/ready` / `/health/live` Kubernetes/Prometheus-style observability endpoints.
6. **Incident Evidence Archival:**
   - While incidents and alerts are persisted to SQL, annotated keyframe snapshots are not automatically archived with strict retention policies.
7. **Production Configuration Separation:**
   - Missing `configs/production.yaml` consolidating production logging, camera reconnect budgets, model registry paths, retention periods, and alert provider configs.
8. **Git & Repository Hygiene:**
   - Missing canonical GitHub remote setup (`origin` -> `https://github.com/SMRU08/RAKSHYA-VISION.git`).
   - Missing open-source/enterprise governance documents: `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `.github/workflows/ci.yml`.

---

## 6. What Must Be Changed

1. **`backend/app/main.py`:**
   - Mount new `/api/cameras` router, `/api/auth` router, and structured health endpoints (`/health/live`, `/health/ready`, `/metrics`).
   - Initialize the multi-camera manager daemon during the FastAPI lifespan context.
   - Enable SQLite WAL mode on database startup.
2. **`backend/app/config.py`:**
   - Expand `Settings` with JWT secret key, auth enable/disable flag, model registry path, production config path, and alert provider credentials.
3. **`backend/app/services/alert_engine.py`:**
   - Integrate pluggable `AlertProvider` pipeline with concrete `WebhookAlertProvider`, `EmailAlertProvider`, and `SMSAlertProvider`.
   - Never report "SENT" if credentials are missing; report "NOT CONFIGURED".
4. **`backend/app/ai/detection/model_loader.py`:**
   - Integrate model registry lookup and enforce pre-load SHA-256 checksum verification. Halt loading if checksum fails.
5. **`frontend/src/services/api.ts` & `CamerasView.tsx`:**
   - Connect live camera status, stream controls (start, stop, restart), and telemetry to the new camera API router.

---

## 7. What Cannot Be Verified in Current Environment

1. **Physical Industrial CCTV Hardware:**
   - The current development environment is a Windows server workstation without physical IP cameras, industrial RTSP streams, or connected USB cameras.
   - Physical RTSP streams will be marked **`NOT TESTED — HARDWARE NOT PRESENT (SERVER ENVIRONMENT)`** and simulated via loopback/synthetic RTSP streams and recorded industrial test videos.
2. **True 24-Hour / 72-Hour Continuous Run:**
   - An interactive agent session cannot block for 24–72 hours.
   - We will execute a controlled 60-second / 5-minute extended run, measure resource metrics, and provide an automated 24-hour / 72-hour acceptance testing script and procedure for site engineers.
3. **NVIDIA GPU / CUDA Acceleration:**
   - Current environment runs on CPU (`device: cpu`). Hardware detection logic will verify CPU inference, identify CUDA as not present, and log clear diagnostic reasons.

---

## 8. Approved Phase 10 Action Plan

With the audit complete, Phase 10 proceeds along the following structured implementation sequence:

```
[Step 1] Full Project Audit (DOC-PHASE10-AUDIT completed)
    ↓
[Step 2] Model Registry & Verified V2 Checksum Enforcer (models/registry/model_registry.yaml)
    ↓
[Step 3] Centralized Production Configuration & Secret Template (configs/production.yaml, .env.example)
    ↓
[Step 4] SQLite WAL Mode, Connection Hardening & Data Retention Manager (scripts/cleanup_retention.py)
    ↓
[Step 5] Production Multi-Camera Manager & Daemon (RTSP, Webcams, MP4 test streams, auto-reconnect)
    ↓
[Step 6] Camera API Router & Dashboard Integration (/api/cameras)
    ↓
[Step 7] Security, Authentication & Role-Based Access Control (/api/auth, JWT, ADMIN/OPERATOR/VIEWER)
    ↓
[Step 8] Alert Provider Abstraction & Dispatcher (Webhook, Email, SMS, status tracking)
    ↓
[Step 9] Incident Evidence Archival Engine (Snapshots, bounding box overlays, retention)
    ↓
[Step 10] Production Observability, System Telemetry & Metrics (/health/live, /health/ready, /metrics)
    ↓
[Step 11] Structured Logging & Log Rotation
    ↓
[Step 12] Process Supervision & Deployment Manifests (Docker, Docker Compose, systemd)
    ↓
[Step 13] Backup & Disaster Recovery Scripts (scripts/backup.py, scripts/restore.py)
    ↓
[Step 14] Production Validation & Smoke Test Suite (scripts/validate_production.py, scripts/production_smoke_test.py)
    ↓
[Step 15] Documentation, GitHub Governance, CI Workflow & Real-World Acceptance Protocols
```
