# RAKSHYA VISION — Project Status

**System:** RAKSHYA VISION (AI Vision-Based Safety Monitoring System)  
**Problem Statement:** PS06 — Prototype AI system detecting safety gear compliance & environmental hazards  
**Target Domains:** Industrial manufacturing, construction sites, power generation, hazardous facilities  
**Repository:** [https://github.com/SMRU08/RAKSHYA-VISION.git](https://github.com/SMRU08/RAKSHYA-VISION.git)  
**Documentation Index:** [`docs/README.md`](./docs/README.md)  

---

## 1. Current System Status

RAKSHYA VISION is an operational, fully integrated edge AI safety monitoring and incident governance platform. The core pipeline continuously processes multi-stream video feeds, performs multi-task detection, tracks workers anonymously, evaluates anatomical personal protective equipment (PPE) compliance, confirms combustion hazards (fire and smoke), computes deterministic risk scores, archives tamper-evident visual evidence, and broadcasts real-time alerts to a Security Operations Center (SOC) dashboard.

---

## 2. Implemented Capabilities

### 2.1 Computer Vision & AI Inference
- **Ultralytics YOLOv8n Multi-Task Detector:** Single-pass inference across canonical 7 classes (`person`, `helmet`, `safety_vest`, `gloves`, `safety_footwear`, `fire`, `smoke`).
- **Cryptographic Model Registry:** Verifies SHA-256 weight integrity before loading into memory (`models/registry/model_registry.yaml`).
- **Decoupled Architecture:** Physical object detection is decoupled from temporal compliance logic and administrative zone policies.

### 2.2 Worker Tracking & PPE Compliance
- **ByteTrack Tracking:** 8-state Kalman Filter trajectory estimation and two-stage Hungarian matching providing persistent, anonymous worker track IDs without biometric data.
- **Anatomical Spatial Association:** Proportional body zone mapping (Head: 0–25%, Torso: 20–70%, Hands: 40–75%, Feet: 75–100%) isolating PPE items per worker with IoU mutual exclusion.
- **Temporal State Machine:** $N_{\text{confirm}} = 3$ frame confirmation eliminates single-frame false violations; $N_{\text{tol}} = 5$ frame tolerance absorbs brief glance-away occlusions.
- **Strict Ambiguity Invariant:** Enforces **`UNKNOWN != VIOLATION`**. Occlusions, boundary clipping, and low confidence never generate safety violations.

### 2.3 Hazard Detection & Risk Governance
- **Fire & Smoke Hazard Analysis:** Decoupled spatial tracking confirming hazards across $N_{\text{confirm}} = 5$ consecutive frames, evaluating co-occurrence relationships (`FIRE_ONLY`, `SMOKE_ONLY`, `FIRE_AND_SMOKE`).
- **Explainable Risk Engine:** Deterministic $0 \dots 100$ mathematical scoring factoring base severity, violation duration, worker density, and zone risk multipliers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **Smart Alert Engine:** Deduplicates rapid alerts against existing open incidents, enforces 60-second cooldown windows, and escalates severity for sustained violations.
- **Incident Lifecycle Management:** Auditable workflow (`OPEN` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `RESOLVED` / `DISMISSED`) with operator tracking and resolution notes.

### 2.4 Multi-Camera Ingestion & Hardware Support
- **Thread-Isolated Workers:** `CameraManager` oversees concurrent, thread-isolated `CameraWorker` instances across RTSP, USB/laptop webcams, and video files.
- **Bounded Exponential Backoff:** Automatic reconnection logic for intermittent network streams.
- **Credential Masking:** RTSP passwords masked in logs, telemetry, and API outputs.

### 2.5 Security, Storage & Operations
- **Role-Based Access Control (RBAC):** Cryptographic PBKDF2-HMAC-SHA256 password hashing (600,000 iterations) and JWT access tokens for `ADMIN`, `OPERATOR`, and `VIEWER` roles.
- **Tamper-Evident Evidence Archival:** Automated snapshot capture on incident creation with SHA-256 checksums, path traversal defenses, and storage quota management.
- **SQLite Write-Ahead Logging (WAL):** High-concurrency persistence with foreign key enforcement (`PRAGMA foreign_keys=ON`) and 5,000 ms busy timeout.
- **Observability & Health Probes:** Kubernetes liveness (`/health/live`), readiness (`/health/ready`), deep health (`/health/deep`), and Prometheus metrics (`/metrics`).
- **Real-Time SOC Dashboard:** React 18, TypeScript, Tailwind CSS, and WebSocket pub/sub streaming (`/ws/alerts`).

---

## 3. Validation & Testing Evidence

| Test Suite | Total Evaluated | Passed | Failed | Success Rate |
|---|:---:|:---:|:---:|:---:|
| **Backend Unit Tests (`backend/tests/`)** | 160 | 160 | 0 | **100%** |
| **System Integration Scenarios (`scripts/testing/`)** | 39 | 39 | 0 | **100%** |
| **Frontend Production Build (`npm run build`)** | 1,907 modules | 1,907 | 0 | **100% (3.44s)** |

- **End-to-End Latency Budget:** 45.5 ms mean latency on commodity 8-core CPU (comfortably under the 100 ms real-time threshold).
- **Memory Footprint:** 423.6 MB $\rightarrow$ 432.7 MB over 25 cycles (+9.1 MB transient cache warm-up, 0 memory leaks).
- **Security Audits:** Rejection of zero-byte uploads (HTTP 400), unsupported file formats (HTTP 415), and path traversal attacks (HTTP 404).

---

## 4. Production Readiness

- **Core Vision Pipeline:** **VERIFIED**
- **Worker Tracking & Compliance:** **VERIFIED**
- **Fire & Smoke Hazard Tracking:** **VERIFIED**
- **Risk Scoring & Incident Lifecycle:** **VERIFIED**
- **Webcam & Video File Ingestion:** **VERIFIED**
- **RTSP IP Camera Ingestion:** **PARTIALLY VERIFIED** (Synthetic & local RTSP verified; industrial CCTV pilot scheduled)
- **External Notifications (Webhooks & Email):** **IMPLEMENTED** (Configuration required)
- **Continuous Endurance Operations:** **NOT TESTED** (24/72-hour soak test scheduled)

---

## 5. Known Limitations

- **Small PPE Detection at Distance:** Protective gloves and footwear require $\ge 40 \times 40$ pixels on target; beyond 15 meters, the system safely defaults state to `UNKNOWN`.
- **Steep Camera Angles:** Overhead angles $> 60^\circ$ occlude torso vests and footwear; oblique mounting angles ($15^\circ$ to $45^\circ$) are recommended.
- **Industrial Steam Vents:** High-density boiler steam resembles smoke; requires configuring polygon exclusion masks around stationary vents.
- **Multi-Stream CPU Throughput:** Running $> 3$ simultaneous 30 FPS streams on CPU requires frame scheduling (`infer_interval_frames = 2`); dedicated edge GPUs recommended for $\ge 4$ cameras.

---

## 6. Future Roadmap

- **Edge GPU Acceleration:** TensorRT and ONNX Runtime optimizations for 10+ concurrent 4K camera streams.
- **Zone Geofencing Tooling:** Interactive polygon geofencing editor directly inside the React dashboard.
- **Industrial Protocols:** Modbus TCP, OPC-UA, and MQTT integrations for programmable logic controller (PLC) interlocks.
- **Expanded PPE Classes:** Face shields, ear protection, and safety harnesses for work-at-height operations.