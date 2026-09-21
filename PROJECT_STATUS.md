# RAKSHYA VISION — Project Status

## Project Overview
- **Project Name:** RAKSHYA VISION
- **Tagline:** AI Vision-Based Safety Monitoring
- **Current Phase:** Phase 7 — Risk Analysis + Smart Alert Engine (COMPLETED & VERIFIED)

---

## 1. Phase 1 Foundation Status
- **Backend:** Operational (FastAPI + SQLAlchemy + SQLite, pytest suite integrated).
- **Frontend:** Built and operational (React 18 + TypeScript + Vite, live health connection).
- **Git:** Version control maintained with structured commits.

---

## 2. Phase 2 Dataset Pipeline Status
- **Raw Datasets Preserved (`datasets/raw/`):** 4 datasets preserved with verified SHA-256 checksums (22,453 raw images).
- **Processed Split (`datasets/processed/`):** 22,453 images (Train: 15,717, Val: 4,490, Test: 2,246), 51,195 verified clean bounding boxes across canonical classes `0..6`.
- **Zero Leakage:** No overlap between splits.

---

## 3. Phase 3 & 3.1 Model Status (`ppe_fire_smoke_v2`)
- **Architecture:** Ultralytics YOLOv8n (nano), PyTorch 2.14.0+cpu
- **Checkpoint:** [`models/detection/ppe_fire_smoke_v2/weights/best.pt`](./models/detection/ppe_fire_smoke_v2/weights/best.pt)
- **Checkpoint SHA-256:** `490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3`
- **Canonical Classes (7):** `0: person`, `1: helmet`, `2: safety_vest`, `3: gloves`, `4: safety_footwear`, `5: fire`, `6: smoke`
- **Test Set Performance (conf=0.25):** Precision: 37.60% | Recall: 37.44% | mAP@50: 25.23% (3.61× over V1)
- **Per-Class Hazard Metrics (Test Split):**
  - `fire`: Precision: 41.99%, Recall: 30.62%, mAP@50: 20.15%
  - `smoke`: Precision: 57.74%, Recall: 30.48%, mAP@50: 22.62%

---

## 4. Phase 4 Real-Time & Video Detection Status (COMPLETED)
- **Inference Pipeline:** Single image, video files, local webcam, and simulated RTSP streams.
- **Strict Decoupling:** Bounding boxes draw only `[class_name] [conf]`; no compliance labels.
- **Endpoints:** `/api/detection/health`, `/api/detection/image`, `/api/detection/video`.

---

## 5. Phase 5 Worker Tracking + PPE Association + Compliance Status (COMPLETED)
- **Anonymous Tracking Engine:** Custom ByteTrack with 8-state Kalman Filter (`KalmanBoxTracker`) and two-stage Hungarian assignment.
- **Anatomy-Aware Spatial Association:** Relative body zones for helmet, vest, gloves, footwear.
- **Temporal State Machine:** $N_{\text{confirm}} = 3$, $N_{\text{tol}} = 5$, boundary clipping & occlusion triggering `UNKNOWN`.
- **Checklist HUD Visualization:** Compact non-destructive overlay above workers with track IDs and item status badges.
- **Endpoints:** `GET /api/compliance/config`, `POST /api/compliance/analyze`.

---

## 6. Phase 6 Fire & Smoke Hazard Analysis Status (COMPLETED)
- **Decoupled Hazard Extraction:** Detects `fire` (class 5) and `smoke` (class 6) without affecting worker PPE status.
- **Spatial Tracking Engine:** IoU + normalized centroid distance matching with anonymous IDs (`HAZARD-0001`, `HAZARD-0002`).
- **Temporal State Machine:** State sequence `NO_HAZARD -> SUSPECTED -> CONFIRMED -> CLEARED -> NO_HAZARD`.
- **Multi-Modal Relationship:** Evaluates `FIRE_ONLY`, `SMOKE_ONLY`, `FIRE_AND_SMOKE`, `NO_HAZARD`.
- **Zone & Camera Intelligence:** Resolves cameras and zones (`configs/cameras.yaml`) with optional polygon ROI containment.
- **Database Persistence:** SQLAlchemy models `HazardEvent` and `HazardObservation` in `backend/app/models/hazard.py`.
- **Endpoints:** `GET /api/hazards/config`, `POST /api/hazards/analyze`, `GET /api/hazards`, `GET /api/hazards/{event_id}`.

---

## 7. Phase 7 Risk Analysis + Smart Alert Engine Status (COMPLETED)
- **Unified Event Normalization:** Common envelope `NormalizedSafetyEvent` ingesting Phase 5 and Phase 6 events.
- **MANDATORY PPE RULE:** Phase 5 `UNKNOWN` state **never** generates a violation. Only confirmed `ABSENT` PPE creates alerts.
- **Explainable Risk Scoring:** Deterministic mathematical scoring ($0 \dots 100$) mapped to `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` based on configurable factors (`configs/risk_policy.yaml`).
- **Incident Management:** Continuous incident tracking with statuses `OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `DISMISSED`.
- **Smart Alerting:** Deduplication against frame flooding, configurable cooldown suppression (`configs/alert_policy.yaml`), and automatic severity escalation on persistence.
- **Human-Readable Alert Messages:** Natural language descriptions including worker track IDs, cameras, and zones.
- **Database Persistence:** SQLAlchemy models `Incident`, `Alert`, `AlertHistory` in `backend/app/models/risk_alert.py`.
- **WebSocket-Ready Event Dispatcher:** Pub/sub `EventBroadcaster` ready for Phase 8 live dashboard streaming.
- **Endpoints:**
  - `GET /api/risk/summary`
  - `GET /api/alerts`
  - `GET /api/alerts/{alert_id}`
  - `POST /api/alerts/{alert_id}/acknowledge`
  - `POST /api/alerts/{alert_id}/resolve`
  - `POST /api/alerts/{alert_id}/dismiss`
  - `GET /api/incidents`
  - `GET /api/incidents/{incident_id}`
- **Verification:**
  - Automated Tests: 72/72 passed (including 19 risk & alert tests).
  - Performance: 0.028 ms risk evaluation latency, 5.69 ms total event processing & DB latency (175.5 events/sec).

---

## 8. Automated Test Suite
- Full test suite passing: `pytest backend/tests -v` (72/72 tests passed).
  - `test_risk_alerts.py`: 19 tests passed.
  - `test_hazards.py`: 16 tests passed.
  - `test_compliance.py`: 14 tests passed.
  - `test_detection.py`: 19 tests passed.
  - `test_main.py`: 4 tests passed.

---

## 9. Next Steps — Phase 8
- Awaiting explicit user approval before beginning Phase 8 (Live Safety Dashboard & WebSocket Integration).