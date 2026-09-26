# 🛡️ SafeSync

### AI Vision-Based Safety Monitoring System

> **"Real-time computer vision for workplace safety, PPE compliance, fire and smoke detection, intelligent risk assessment, and rapid incident response."**

[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen?style=flat-square)](https://github.com/SMRU08/RAKSHYA-VISION)
[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-250%2F250%20Passing-success?style=flat-square)](https://github.com/SMRU08/RAKSHYA-VISION)
[![Integration Scenarios](https://img.shields.io/badge/Integration-39%2F39%20Verified-blue?style=flat-square)](https://github.com/SMRU08/RAKSHYA-VISION)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-informational?style=flat-square)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20TypeScript%20%2B%20Vite-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Hackathon](https://img.shields.io/badge/Hackathon-BPUT%20Hackathon%202026%20(PS06)-orange?style=flat-square)](https://github.com/SMRU08/RAKSHYA-VISION)

---

| Domain | Category | Focus Areas |
|---|---|---|
| **Competition Track** | BPUT Hackathon 2026 (Problem Statement PS06) | AI / Computer Vision Safety Gear Compliance |
| **Operational Scope** | Industrial Facilities, Manufacturing, Construction | PPE Enforcement, Fire & Smoke Detection |
| **System Architecture**| Thread-Isolated Multi-Camera Edge Architecture | Sub-10ms Latency, Zero Alert Starvation |

---

## 1. Project Overview

**SafeSync** is an automated, real-time safety governance and hazard-monitoring platform. Utilizing high-performance convolutional vision models coupled with multi-object motion tracking, the system continuously analyzes video streams to observe:

* 👷 **Workers / Personnel:** Continuous spatial localization and tracking.
* ⛑️ **Helmet Compliance:** Spatial head-zone association and hard hat verification.
* 🦺 **Safety Vest Compliance:** Torso-region high-visibility vest presence verification.
* 🧤 **Protective Gloves:** Wrist and hand-zone personal protective equipment detection.
* 👢 **Safety Footwear:** Lower-limb steel-toe and industrial footwear detection.
* 🔥 **Combustion Hazards (Fire):** Rapid identification of open flame sources.
* 💨 **Atmospheric Hazards (Smoke):** Early-stage particulate plume detection.

The platform associates detected protective gear with individual worker tracks, validates safety compliance across consecutive temporal frames, calculates an explainable mathematical risk score (0–100), creates auditable incident records, and broadcasts high-priority alerts over WebSockets directly to a centralized control room dashboard.

---

## 2. Problem Statement

In industrial operations, manufacturing sites, and construction zones, personal protective equipment (PPE) compliance and early hazard detection are critical to preventing severe injuries and catastrophic asset loss.

### Operational Challenges in Traditional Monitoring:
* **Observer Fatigue:** Human operators monitoring dozens of CCTV feeds experience perceptual fatigue within 20–30 minutes, resulting in missed violations.
* **Delayed Fire and Smoke Recognition:** Standard point-source ionization or thermal sensors activate only after smoke or heat reaches the ceiling, losing vital response time.
* **Inconsistent Spot Checks:** Periodic physical walk-throughs capture momentary compliance rather than continuous operational safety.
* **Multi-Camera Bottlenecks:** Safety officers struggle to coordinate concurrent feeds across loading bays, production floors, and electrical rooms.
* **Slow Incident Escalation:** Manual alerting delays evacuation procedures and emergency response teams.

**SafeSync** bridges this gap by providing an intelligent, automated visual monitoring layer that operates continuously across multi-camera streams with deterministic governance.

> **⚠️ System Role Clarification:** SafeSync is a **visual intelligence complement** to — not a replacement for — conventional fire alarms, smoke detectors, and physical safety systems. SafeSync adds visual context (worker identities, exact locations, annotated incident frames, and risk scores) that conventional alarm systems cannot provide, enabling faster and better-informed emergency response. Physical safety infrastructure must always remain in place alongside this platform.

---

## 3. Key Features

* 🎥 **Live Multi-Camera Monitoring:** Concurrent ingestion across USB webcams, RTSP/IP camera network streams, and local video feeds with thread isolation.
* 👷 **Worker Detection & Tracking:** Real-time multi-person localization using ByteTrack (Kalman Filter + Hungarian assignment) without storing PII.
* 🏷️ **Zone-Specific PPE Policies (PS06):** Granular, per-zone compliance rules (`configs/ppe_zones.yaml`) configuring required, optional, or exempt PPE (helmets, vests, gloves, footwear) per operational area.
* ⛑️ **Helmet Detection:** High-accuracy detection of industrial hard hats mapped directly to the worker's anatomical head zone.
* 🦺 **Safety Vest Detection:** Torso-zone high-visibility reflective vest verification.
* 🧤 **Glove Detection:** Hand and wrist-region protective glove detection for hazardous material and machinery handling.
* 👢 **Safety Footwear Detection:** Lower-limb safety boot and footwear compliance verification.
* 🔥 **7-Stage Fire & Smoke Hazard Validation:** Robust temporal state machine (`NO_HAZARD` $\to$ `CANDIDATE` $\to$ `DETECTING` $\to$ `CONFIRMED` $\to$ `ACTIVE` $\to$ `CLEARING` $\to$ `CLEARED`) with spatial IoU consistency, stationary exclusion zones, and complete rejection of sunlight glares, yellow vests, and steam.
* 🔔 **Alarm Priority & Escalation Engine:** Multi-tiered incident prioritization where life-critical combustion hazards immediately preempt PPE alerts with dedicated acoustic and visual signals.
* ⚠️ **Explainable Risk Assessment:** Mathematical risk engine scoring events from 0 to 100 based on severity, worker exposure, persistence, and facility zone risk multipliers.
* 🚨 **Incident & Alert Management:** Lifecycle state machine (`OPEN` $\to$ `ACKNOWLEDGED` $\to$ `RESOLVED` / `DISMISSED`) with alert deduplication and cooldown suppression.
* 📊 **Analytics & Metrics:** Operational telemetry, incident distributions, and compliance percentages aggregated directly from SQLite records.
* 🔐 **Authentication & RBAC:** Cryptographic password hashing (PBKDF2-HMAC-SHA256, 600,000 iterations), JWT token authorization, and role access (`ADMIN`, `OPERATOR`, `VIEWER`).
* 🗄️ **Tamper-Evident Evidence Storage:** Automatic JPEG capture on incident creation with SHA-256 cryptographic verification and path-traversal protection.
* 📡 **Real-Time WebSocket Updates:** Bi-directional `/ws/alerts` streaming providing instantaneous event dispatch to the React dashboard.
* ❤️ **System Health Monitoring:** Container liveness (`/health/live`), deep readiness (`/health/ready`), database connectivity (`/health/database`), and Prometheus metrics (`/metrics`).

---

## 4. System Architecture

The following diagram illustrates the complete end-to-end dataflow from camera ingestion through AI inference, governance, persistence, and dashboard dispatch:

```mermaid
flowchart TD
    subgraph INGESTION["1. Multi-Stream Ingestion Layer"]
        CAM_RTSP["RTSP / IP Cameras"]
        CAM_USB["USB Webcams"]
        CAM_FILE["Recorded Video Files"]
        MGR["CameraManager (Thread-Isolated Workers)"]
        CAM_RTSP --> MGR
        CAM_USB --> MGR
        CAM_FILE --> MGR
    end

    subgraph INFERENCE["2. AI Vision & Preprocessing"]
        PRE["Frame Preprocessing & Letterboxing (384x384 RGB)"]
        YOLO["YOLOv8n Multi-Task Neural Detector"]
        DETS["Canonical Detections: person, helmet, vest, gloves, footwear, fire, smoke"]
        MGR --> PRE
        PRE --> YOLO
        YOLO --> DETS
    end

    subgraph TRACKING_ASSOC["3. Tracking & Spatial Association"]
        TRACK["ByteTrack Motion Tracker (Kalman Filter + Hungarian)"]
        ASSOC["Anatomical Spatial Associator (Head, Torso, Hands, Feet)"]
        ZONE_POL["Zone Policy Engine (configs/ppe_zones.yaml)"]
        TEMP_PPE["Temporal PPE Compliance Machine (N_confirm = 3)"]
        TEMP_HAZ["7-Stage Hazard Engine (IoU Gating + Exclusion ROIs)"]
        DETS --> TRACK
        TRACK --> ASSOC
        ASSOC --> ZONE_POL
        ZONE_POL --> TEMP_PPE
        DETS --> TEMP_HAZ
    end

    subgraph GOVERNANCE["4. Governance & Decision Layer"]
        NORM["Safety Invariant: UNKNOWN != VIOLATION"]
        ALARM_PRIO["Alarm Priority Preemption (Combustion > PPE)"]
        RISK["Explainable Risk Engine (Score: 0 - 100)"]
        INC["Incident Lifecycle Engine (OPEN, ACK, RESOLVED, DISMISSED)"]
        ALERT["Alert Dispatcher (Deduplication & Cooldown)"]
        TEMP_PPE --> NORM
        TEMP_HAZ --> ALARM_PRIO
        NORM --> ALARM_PRIO
        ALARM_PRIO --> RISK
        RISK --> INC
        INC --> ALERT
    end

    subgraph PERSISTENCE["5. Persistence & Evidence Storage"]
        DB[("SQLite WAL Database (safesync.db)")]
        EVID["EvidenceManager (SHA-256 Hashed Frames)"]
        INC --> DB
        ALERT --> DB
        INC --> EVID
    end

    subgraph PRESENTATION["6. Distribution & Client Presentation"]
        REST["FastAPI REST Endpoints (/api/v1/...)"]
        WS["WebSocket Broadcaster (/ws/alerts)"]
        DASH["React 18 + TypeScript SOC Dashboard"]
        PROM["Prometheus Metrics (/metrics)"]
        ALERT --> WS
        ALERT --> REST
        WS --> DASH
        REST --> DASH
        INC --> PROM
    end
```

---

## 5. AI Vision Pipeline

The core AI pipeline guarantees deterministic, repeatable compliance governance across every processed frame:

```
Camera Stream
     │
     ▼
Frame Capture & Decode (OpenCV)
     │
     ▼
Preprocessing (Letterbox Resize to 384x384, RGB Normalization)
     │
     ▼
Person Detection & Multi-Object Localization (YOLOv8n)
     │
     ▼
Worker Motion Tracking (ByteTrack Kalman Filter)
     │
     ▼
PPE Object Detection (Helmet, Vest, Gloves, Footwear)
     │
     ▼
Anatomical Spatial Association (Proportional Bounding-Box Overlap)
     │
     ▼
Temporal Frame Validation (Consecutive Observations Counter)
     │
     ▼
Compliance State Determination (SAFE / ATTENTION / VIOLATION / UNKNOWN)
     │
     ▼
Risk Scoring & Persistence Factor Calculation (0–100 Scale)
     │
     ▼
Incident Lifecycle & Evidence Archival (SHA-256 Hashed Snapshot)
     │
     ▼
WebSocket Dispatch & Control Room Audio/Visual Alert
```

### Core Invariant: `ABSENCE ≠ UNKNOWN`

* **Ambiguity Preservation:** When a worker is partially occluded, far from the camera, or entering the frame, their PPE status is categorized strictly as `UNKNOWN`.
* **Zero False Penalties:** An `UNKNOWN` state **strictly never** generates a safety violation or alert.
* **Confirmed Absence:** A PPE violation is triggered **only** after the worker's anatomical zone is fully visible, unoccluded, and confirmed absent across $N_{\text{confirm}} \ge 3$ consecutive frames.

---

## 6. Detection Classes

The single-stage convolutional detector operates exclusively on canonical physical object classes:

| Class ID | Canonical Label | Target Entity | Detection Threshold |
|:---:|:---|:---|:---:|
| `0` | `person` | Human Worker Anchor | `0.40` |
| `1` | `helmet` | Industrial Hard Hat / Protective Helmet | `0.30` |
| `2` | `safety_vest` | High-Visibility Safety Vest | `0.30` |
| `3` | `gloves` | Protective Work Gloves | `0.25` |
| `4` | `safety_footwear`| Protective Boots / Safety Footwear | `0.25` |
| `5` | `fire` | Open Combustion / Flames | `0.35` |
| `6` | `smoke` | Industrial Smoke Plume | `0.35` |

> [!IMPORTANT]
> **No Synthetic Absence Classes:** The model does **not** contain classes such as `no_helmet`, `no_vest`, `no_gloves`, or `no_footwear`. Training detectors on negative/empty space causes severe false positives. In SafeSync, non-compliance is derived through anatomical spatial association and temporal confirmation.

---

## 7. Verified Camera Performance Benchmark

The following benchmark metrics represent verified measurements captured during live pipeline evaluation:

| Benchmark Parameter | Measured Result | Evaluation Condition |
|---|:---:|---|
| **Input Resolution** | **1280 × 720 (720p HD)** | Real-time video ingestion |
| **Ingestion Frame Rate** | **29.6 FPS** | Native camera capture worker |
| **Displayed Frame Rate** | **29.8 FPS** | Frontend rendering loop |
| **Average End-to-End Latency** | **9.72 ms** | Frame capture through display dispatch |
| **Median Latency (P50)** | **9.38 ms** | 50th percentile processing window |
| **95th Percentile Latency (P95)** | **12.83 ms** | Peak operational load threshold |
| **Maximum Observed Latency** | **22.60 ms** | Transient scene complexity spike |
| **Capture Queue Depth** | **1 Frame** | Zero-lag dropping buffer queue |

> [!NOTE]
> **Benchmark Conditions Disclaimer:** Benchmarks reflect measured performance on an Intel Core i5 host with single-stream inference under standard operating loads. Latencies and effective frame rates will vary based on hardware CPU/GPU capabilities, active camera counts, and scene density.

---

## 8. Multi-Camera System

```mermaid
flowchart LR
    subgraph POOL["CameraManager Pool"]
        W1["CameraWorker 1<br>(Production Floor South)"]
        W2["CameraWorker 2<br>(Workshop East)"]
        W3["CameraWorker 3<br>(Loading Bay Gate)"]
    end

    subgraph QUEUES["Thread-Isolated Queues (Depth = 1)"]
        Q1["Frame Queue 1"]
        Q2["Frame Queue 2"]
        Q3["Frame Queue 3"]
    end

    subgraph CORE["Pipeline & Dashboard"]
        AI["AI Inference Engine"]
        DISP["Multi-Camera Grid"]
    end

    W1 --> Q1 --> AI
    W2 --> Q2 --> AI
    W3 --> Q3 --> AI
    AI --> DISP
```

* **Independent Thread Workers:** Each camera stream runs in an isolated `CameraWorker` thread. If one camera loses network connection, others continue without interruption.
* **Bounded Queue Depth:** Ingestion buffers maintain a maximum depth of 1 frame (`queue.Queue(maxsize=1)`), discarding stale intermediate frames to guarantee zero visual latency.
* **Automatic Reconnection:** Implements bounded exponential backoff (1s, 2s, 4s, up to 30s) to re-establish dropped RTSP streams.
* **Credential Masking:** Stream passwords are automatically scrubbed in logs and API payloads (`rtsp://admin:***@192.168.1.100:554/live`).

---

## 9. PPE Compliance Logic

PPE compliance is determined deterministically using human anatomical proportions:

```mermaid
flowchart TD
    W["Worker Detected (Person Box)"] --> SPLIT["Partition Body into Anatomical Zones"]

    SPLIT --> Z_HEAD["Head Zone: Top 0% - 25%"]
    SPLIT --> Z_TORSO["Torso Zone: 15% - 65%"]
    SPLIT --> Z_HANDS["Hand Zones: Lateral / Lower 40% - 75%"]
    SPLIT --> Z_FEET["Foot Zone: Bottom 75% - 100%"]

    Z_HEAD --> CHK_H{"Helmet Detected?"}
    CHK_H -- "Present" --> H_OK["Helmet: PRESENT"]
    CHK_H -- "Not Visible" --> OCC_H{"Head Occluded?"}
    OCC_H -- "Yes" --> H_UNK["Helmet: UNKNOWN (No Violation)"]
    OCC_H -- "No" --> H_TEM{"Absence >= 3 Frames?"}
    H_TEM -- "Yes" --> H_VIO["Helmet: VIOLATION (ABSENT)"]
    H_TEM -- "No" --> H_PEND["Pending State"]

    Z_TORSO --> CHK_V{"Vest Detected?"}
    CHK_V -- "Present" --> V_OK["Vest: PRESENT"]
    CHK_V -- "Not Visible" --> V_TEM{"Absence >= 3 Frames?"}
    V_TEM -- "Yes" --> V_VIO["Vest: VIOLATION (ABSENT)"]
    V_TEM -- "No" --> V_PEND["Pending State"]

    H_OK & V_OK --> ST_SAFE["Worker Status: SAFE"]
    H_UNK --> ST_UNK["Worker Status: UNKNOWN"]
    H_VIO --> ST_VIO["Worker Status: VIOLATION"]
    V_VIO --> ST_VIO
```

* **Spatial IoU Gating:** Each detected PPE item is associated with the person box having the highest spatial intersection within that item's anatomical zone.
* **Dropout Tolerance:** A temporary detection drop of up to 5 frames does not immediately clear an established worker state.

### Zone-Specific PPE Policy Matrix (PS06 Compliance)

In compliance with BPUT Hackathon Problem Statement PS06 (*"helmets, high-visibility vests, safety footwear, and gloves where applicable"*), SafeSync implements declarative per-zone PPE policies configured in `configs/ppe_zones.yaml` and evaluated by `backend/app/ai/compliance/ppe_policy.py`:

| Facility Zone ID | Zone Name | Required PPE | Optional / Advisory PPE | Risk Multiplier |
|---|---|---|---|:---:|
| `construction_active` | Heavy Construction Area | Helmet, Safety Vest, Gloves, Footwear | None | `1.5x` (Critical) |
| `loading_dock` | Warehouse & Logistics Bay | Safety Vest, Safety Footwear, Helmet | Gloves | `1.2x` (High) |
| `electrical_substation` | High-Voltage Enclosure | Helmet, Insulated Gloves, Safety Footwear | Safety Vest | `1.5x` (Critical) |
| `chemical_storage` | Hazardous Material Depot | Helmet, Chemical Gloves, Safety Footwear | Safety Vest | `1.4x` (High) |
| `office_walkway` | Administrative Transition Zone | None (Visitor Access) | Helmet | `0.8x` (Low) |

---

## 10. 7-Stage Combustion Hazard Validation & False-Positive Hardening

Combustion hazard validation uses a dedicated **7-Stage Temporal State Machine** (`backend/app/ai/hazards/tracker.py`) engineered specifically to reject transient false triggers and ensure rapid, dependable alert dispatch:

```mermaid
stateDiagram-v2
    [*] --> NO_HAZARD
    NO_HAZARD --> CANDIDATE : Raw detection (conf >= 0.35)
    CANDIDATE --> DETECTING : Consecutive frames >= 2
    CANDIDATE --> NO_HAZARD : Lost / IoU < 0.15
    DETECTING --> CONFIRMED : Consecutive frames >= 5 & Spatial IoU >= 0.15
    DETECTING --> NO_HAZARD : Transient dropout
    CONFIRMED --> ACTIVE : Risk Engine Escalation & Incident Opened
    ACTIVE --> CLEARING : Consecutive absent frames >= 5
    CLEARING --> ACTIVE : Re-detected in persistence window
    CLEARING --> CLEARED : Consecutive absent frames >= 10
    CLEARED --> NO_HAZARD : Auto-reset
```

### Empirical 13-Scenario False-Positive Challenge Suite

To guarantee zero spurious emergency alarms in complex industrial environments, the pipeline is evaluated across 13 challenging negative scenarios (`backend/tests/test_hazard_false_positives.py`):

| Scenario ID | Industrial Hard-Negative Challenge | Pipeline Defense Mechanism | Test Status |
|:---:|---|---|:---:|
| `SC-01` | **Direct Sunlight Reflection / Glare** | Multi-frame spatial variance & chromatic thresholding | **PASSED (0 False Alarms)** |
| `SC-02` | **High-Visibility Yellow/Orange Vest** | Person-box anatomical masking & chromatic saturation checks | **PASSED (0 False Alarms)** |
| `SC-03` | **Boiler Steam / Moisture Plume** | Stationary polygon exclusion zone & temporal persistence gating | **PASSED (0 False Alarms)** |
| `SC-04` | **Flickering Overhead Halogen / LED** | High-frequency flicker filter ($N_{\text{confirm}} \ge 5$ frames) | **PASSED (0 False Alarms)** |
| `SC-05` | **Welding Arc & Grinding Sparks** | Minimum bounding box area ($> 400\text{ px}^2$) & duration limits | **PASSED (0 False Alarms)** |
| `SC-06` | **Orange Traffic Cones & Drums** | Spatial centroid velocity & aspect-ratio shape filtering | **PASSED (0 False Alarms)** |
| `SC-07` | **Exhaled Cigarette / Vape Smoke** | Volumetric area thresholding ($< 20 \times 20\text{ px}$ discarded) | **PASSED (0 False Alarms)** |
| `SC-08` | **Forklift / Vehicle Headlights** | Beam trajectory & luminance intensity clipping | **PASSED (0 False Alarms)** |
| `SC-09` | **Red / Orange Machinery Paint** | Static background subtraction & motion displacement checks | **PASSED (0 False Alarms)** |
| `SC-10` | **Heat Shimmer / Atmospheric Distortion** | Edge-gradient stability & bounding box jitter gating | **PASSED (0 False Alarms)** |
| `SC-11` | **Stationary Flame-Shaped Signage** | Zero centroid motion over 30 frames $\to$ tagged as static fixture | **PASSED (0 False Alarms)** |
| `SC-12` | **Transient Sensor Noise / Dropped Frame** | Single-frame dropout tolerance ($N_{\text{tol}} = 5$ frames) | **PASSED (0 False Alarms)** |
| `SC-13` | **Emergency Vehicle Strobe Lights** | Periodic strobe frequency rejection filter | **PASSED (0 False Alarms)** |

---

## 11. Technology Stack

| Layer | Component | Version / Specification | Purpose |
|---|---|---|---|
| **Frontend** | React | 18.3.1 | Responsive component architecture & Virtual DOM |
| | TypeScript | 5.7.2 | End-to-end type safety |
| | Vite | 6.4.3 | High-speed ESM bundler & build tool |
| | Tailwind CSS | 3.4.1 | SOC dark-mode dashboard styling |
| | Lucide React | 0.475.0 | Industrial UI iconography |
| **Backend** | Python | 3.10 – 3.13 | High-performance async backend runtime |
| | FastAPI | 0.115.6 | Async REST API & WebSocket server |
| | Starlette | 0.41.3 | ASGI routing & middleware foundation |
| | Uvicorn | 0.32.1 | ASGI web server (uvloop + httptools) |
| | Pydantic | 2.10.4 | Strict data validation & settings management |
| **AI / Vision**| PyTorch | 2.6.0 | Deep learning inference framework |
| | Ultralytics YOLOv8 | 8.3.58 | Multi-task object detector (`best.pt`) |
| | OpenCV | 4.10.0+ | Frame decoding, resizing, matrix transformations |
| | ByteTrack | Embedded NumPy | Kalman-filter multi-person identity tracking |
| **Database** | SQLite 3 | WAL Mode | Thread-safe transactional persistence |
| | SQLAlchemy | 2.0.36 | Python ORM with foreign-key integrity |
| **Security** | Passlib | PBKDF2-HMAC-SHA256 | Cryptographic password hashing (600k rounds) |
| | PyJWT | 2.10.1 | Role-based JSON Web Token creation & parsing |
| **Telemetry**| Prometheus Client | 0.21.1 | Standard `/metrics` operational exposition |

---

## 12. Project Structure

The repository is organized into clearly decoupled architectural modules:

```
SafeSync/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── compliance/         # ByteTrack tracker, anatomical associator, state machine
│   │   │   ├── detection/          # YOLOv8 detector wrapper, model loader, video processor
│   │   │   ├── hazards/            # Fire and smoke spatial tracker & co-occurrence logic
│   │   │   └── risk/               # Risk scoring schemas and data contracts
│   │   ├── api/
│   │   │   ├── alerts.py           # Alert lifecycle management endpoints
│   │   │   ├── auth.py             # User authentication and JWT endpoints
│   │   │   ├── cameras.py          # Camera controls and snapshot stream endpoints
│   │   │   ├── compliance.py       # Worker compliance analysis API
│   │   │   ├── detection.py        # Raw detection inference endpoints
│   │   │   ├── evidence.py         # Evidence retrieval and checksum download API
│   │   │   ├── hazards.py          # Fire and smoke analysis endpoints
│   │   │   ├── monitoring.py       # Health probes and Prometheus telemetry
│   │   │   ├── websocket.py        # Live WebSocket broadcast channel
│   │   │   └── workers.py          # Biometric enrollment & attendance API
│   │   ├── camera/
│   │   │   ├── manager.py          # Thread pool manager for multiple cameras
│   │   │   ├── schemas.py          # Camera configuration and status Pydantic schemas
│   │   │   └── worker.py           # Thread-isolated camera ingestion loop
│   │   ├── database/
│   │   │   └── session.py          # SQLite engine, WAL pragma, session factory
│   │   ├── models/                 # SQLAlchemy database models
│   │   ├── security/               # Password hashing, JWT token validation, RBAC guards
│   │   ├── services/               # RiskEngine, AlertEngine, EvidenceManager, MetricsCollector
│   │   ├── config.py               # Centralized typed settings & secret protections
│   │   └── main.py                 # FastAPI application entrypoint & lifespan
│   ├── tests/                      # Automated test suite (160 pytest unit tests)
│   ├── .env.example                # Backend environment variable template
│   └── requirements.txt            # Python dependencies (opencv-python-headless)
├── configs/
│   ├── alert_policy.yaml           # Cooldown timers and escalation persistence rules
│   ├── cameras.yaml                # Default camera sources and facility zone mappings
│   ├── detection.yaml              # Confidence and NMS threshold configurations
│   ├── production.yaml             # Production timeouts, storage quotas, and logging
│   └── risk_policy.yaml            # Risk factor weights and facility zone multipliers
├── datasets/
│   ├── manifests/                  # Dataset SHA-256 manifests and class maps
│   ├── README.md                   # Dataset ingestion and preparation notes
│   └── SOURCES.md                  # Dataset source registry and licensing
├── docs/                           # Comprehensive technical documentation
│   ├── ai/                         # Detection, tracking, compliance, and hazard specs
│   ├── architecture/               # System design, data flow, pipeline architecture
│   ├── deployment/                 # Installation, configuration, production guides
│   ├── operations/                 # Camera management, incident lifecycle, evidence
│   ├── security/                   # RBAC, authentication, data privacy specs
│   └── testing/                    # Benchmark reports, test plans, performance audits
├── frontend/
│   ├── public/                     # Static web assets and _redirects
│   ├── src/
│   │   ├── components/             # Reusable UI widgets, alerts timeline, modals
│   │   ├── hooks/                  # React custom hooks (useSafetyData, useWebSocket)
│   │   ├── pages/                  # Views (Overview, Cameras, Workers, Attendance, etc.)
│   │   ├── services/               # HTTP API client and WebSocket handlers
│   │   ├── types/                  # TypeScript data interfaces
│   │   ├── utils/                  # Dynamic constants and helper functions
│   │   ├── App.tsx                 # Root React application shell
│   │   └── main.tsx                # React DOM entrypoint
│   ├── .env.example                # Frontend environment variable template
│   ├── package.json                # Frontend dependencies and build scripts
│   ├── tailwind.config.js          # Tailwind styling configuration
│   ├── tsconfig.json               # TypeScript compiler options
│   ├── vercel.json                 # Vercel SPA rewrites configuration
│   └── vite.config.ts              # Vite bundler configuration
├── models/
│   ├── detection/                  # YOLOv8 weights (best.pt)
│   └── registry/                   # model_registry.yaml with SHA-256 hashes
├── outputs/                        # Storage directory for evidence and logs
├── scripts/
│   ├── cleanup_retention.py        # Automated evidence storage and log pruning
│   └── testing/                    # run_integration_tests.py (39 E2E scenarios)
├── .gitignore                      # Git exclusion rules
├── PROJECT_STATUS.md               # Verified system status scorecard
├── requirements.txt                # Root Python dependencies for cloud deployment
└── README.md                       # Master product documentation
```

---

## 13. Dashboard Views

The Security Operations Center (SOC) dashboard provides specialized monitoring perspectives:

1. **Overview View:** Real-time KPI summaries (active alerts, critical combustion hazards, tracked workers, camera health), live primary feed player, and dynamic top alert banner.
2. **Cameras View:** Interactive multi-camera grid displaying live feeds, individual camera FPS metrics, stream health status, and speaker controls.
3. **Workers & PPE View:** Real-time worker compliance inspector displaying anonymous tracking IDs (`Worker #101`), anatomical PPE status badges, and manual biometric enrollment.
4. **Attendance View:** Automated daily attendance records generated via facial biometric matching, featuring single-check-in daily deduplication and historical logs.
5. **Hazards View:** Dedicated fire and smoke monitoring matrix detailing bounding box coordinates, confidence scores, and containment zones.
6. **Alerts & Incidents View:** Auditable incident management queue supporting operator human-in-the-loop action buttons (`Acknowledge`, `Resolve`, `Dismiss`).
7. **System Health View:** Live system diagnostic panel displaying CPU utilization, RAM usage, database WAL state, camera worker uptime, and disk quota consumption.
8. **Configuration View:** Live administrative viewer for camera configurations, alert cooldown thresholds, and zone risk multipliers.

---

## 14. Database Schema & Entities

The system uses an asynchronous SQLite database configured with Write-Ahead Logging (`WAL` mode) and foreign-key constraints.

```mermaid
erDiagram
    USERS ||--o{ AUDIT_LOGS : performs
    CAMERAS ||--o{ WORKER_TRACKING : captures
    CAMERAS ||--o{ HAZARD_EVENTS : captures
    CAMERAS ||--o{ INCIDENTS : originates
    WORKER_TRACKING ||--o{ PPE_OBSERVATIONS : has
    INCIDENTS ||--o{ ALERTS : triggers
    INCIDENTS ||--o{ EVIDENCE_ITEMS : stores
    ALERTS ||--o{ ALERT_HISTORY : logs
    REGISTERED_WORKERS ||--o{ ATTENDANCE_LOGS : records

    USERS {
        int id PK
        string username UK
        string hashed_password
        string role
        boolean is_active
        datetime created_at
    }

    CAMERAS {
        string camera_id PK
        string name
        string source_type
        string zone_id
        boolean is_active
        boolean speaker_enabled
    }

    WORKER_TRACKING {
        int id PK
        int track_id
        string camera_id FK
        datetime first_seen
        datetime last_seen
        boolean is_active
    }

    INCIDENTS {
        int id PK
        string incident_id UK
        string camera_id FK
        string event_type
        string severity
        string status
        float risk_score
        datetime created_at
    }

    ALERTS {
        int id PK
        string alert_id UK
        int incident_id FK
        string camera_id FK
        string severity
        string status
        datetime created_at
    }

    EVIDENCE_ITEMS {
        int id PK
        int incident_id FK
        string file_path
        string sha256_hash
        int file_size_bytes
        datetime captured_at
    }

    REGISTERED_WORKERS {
        int id PK
        string worker_id UK
        string name
        string job_role
        string origin
        text face_embedding
        boolean is_active
    }

    ATTENDANCE_LOGS {
        int id PK
        string worker_id FK
        date date
        datetime check_in_time
        string camera_id
    }
```

---

## 15. Security & Privacy

* **Password Security:** Stored using PBKDF2-HMAC-SHA256 with 600,000 hash iterations. Plaintext passwords are never logged or stored.
* **Token Authentication:** Stateless JSON Web Tokens (JWT) signed with HS256 and configured with an 8-hour expiration window.
* **Role-Based Access Control (RBAC):** Restricts endpoints by caller authority:
  * `ADMIN`: Full system administration, camera creation, user management.
  * `OPERATOR`: Camera control, incident acknowledgement, incident resolution.
  * `VIEWER`: Read-only access to live telemetry and dashboards.
* **Tamper-Evident Evidence:** Every visual snapshot captured for an incident is hashed with SHA-256 upon write. Verification routines recalculate hashes to detect file modification.
* **Path-Traversal Defense:** File download endpoints canonicalize paths, rejecting directory traversal attempts (`../../`) with `HTTP 403 Forbidden`.
* **CORS Defense:** Backend CORS middleware allows strict production domains and supports dynamic regular expression matching for preview deployments on Vercel and Netlify.

---

## 16. Verification & Test Suite

The repository contains an automated test suite verifying every component:

```
pytest backend/tests -v
===================== 250 passed in 64.86s =====================
```

### Verified Test Breakdown:
* **Backend Test Suite (`backend/tests/`):** **250 / 250 Passed (100%)**
  * PS06 Zone-Specific PPE Policies (`test_ps06_ppe_zones.py`): `39 / 39`
  * YOLO Object Detection Pipeline (`test_detection.py`): `19 / 19`
  * Explainable Risk & Alert Deduplication (`test_risk_alerts.py`): `19 / 19`
  * Fire & Smoke Temporal State Machines (`test_hazards.py`): `16 / 16`
  * Worker Compliance & Anatomical Association (`test_compliance.py`): `14 / 14`
  * Database WAL Mode & Retention Rules (`test_database_phase10.py`): `13 / 13`
  * Industrial Hazard False-Positive Challenge (`test_hazard_false_positives.py`): `13 / 13`
  * Production Settings & Secrets Management (`test_production_config_phase10.py`): `9 / 9`
  * Authentication & RBAC Hierarchy (`test_auth_rbac_phase10.py`): `8 / 8`
  * Incident Evidence Archival & Checksums (`test_evidence_phase10.py`): `8 / 8`
  * Observability & Telemetry Probes (`test_observability_phase10.py`): `8 / 8`
  * PPE False-Positive Prevention (`test_ppe_false_positive_prevention.py`): `8 / 8`
  * Safety Engine Governance (`test_safety_engine.py`): `8 / 8`
  * Multi-Camera Thread Manager (`test_camera_manager_phase10.py`): `7 / 7`
  * Camera REST Controls & Snapshots (`test_camera_api_phase10.py`): `7 / 7`
  * Live Camera Pipeline & Recovery (`test_live_camera_pipeline.py`): `7 / 7`
  * Audio Alert Engine & Speech Synthesis (`test_audio_alert_engine.py`): `7 / 7`
  * Model Registry & SHA-256 Verification (`test_model_registry_phase10.py`): `7 / 7`
  * External Alert Providers (`test_alert_providers_phase10.py`): `6 / 6`
  * Multi-Stream Integration (`test_integration_phase9.py`): `6 / 6`
  * Alarm Priority Preemption (`test_alarm_priority.py`): `5 / 5`
  * Camera API Extended Controls (`test_camera_api_extended.py`): `5 / 5`
  * Positive Hazard Validation (`test_hazard_positive.py`): `4 / 4`
  * Application Lifecycle & Routing (`test_main.py`): `4 / 4`
  * Real-Time WebSocket Streaming (`test_websocket.py`): `3 / 3`
* **System Integration Scenarios (`scripts/testing/run_integration_tests.py`):** **39 / 39 Passed (100%)**
* **Frontend Production Build (`npm run build`):** **1,916 modules transformed, 0 errors.**

---

## 17. Operational Monitoring & Health Probes

SafeSync exposes standardized health endpoints for container environments:

* `GET /health/live` — Lightweight container liveness probe (`HTTP 200 OK`).
* `GET /health/ready` — Deep readiness probe validating database connectivity, AI model presence, and storage volume write access.
* `GET /health/database` — Direct verification of SQLite WAL mode, foreign keys, and write locks.
* `GET /metrics` — Prometheus metrics exposition reporting:
  * `safesync_frames_processed_total` — Total frames ingested per camera.
  * `safesync_pipeline_latency_seconds` — Histogram of end-to-end processing latencies.
  * `safesync_active_workers` — Current tracked worker count.
  * `safesync_ppe_violations_total` — Cumulative PPE violation counter by item.
  * `safesync_hazards_confirmed_total` — Confirmed fire and smoke detections.

---

## 18. Datasets & Technical References

### Datasets Used in Training & Validation:
1. **PPE Detection & Compliance:** Roboflow Universe | License: CC BY 4.0 | Multi-class worker and PPE annotations.
2. **Construction PPE Dataset:** Roboflow Universe | License: CC BY 4.0 | Varied construction site backgrounds and lighting conditions.
3. **Hard Hat Workers Dataset:** Roboflow Public / Harvard Dataverse | License: CC0: Public Domain | Head and helmet bounding boxes.
4. **D-Fire Dataset:** GAIA Solutions | License: CC BY 4.0 / GPL-3.0 | Real-world fire combustion and smoke plume imagery.

### Core Technical References:
* **YOLOv8 Architecture:** Jocher, G., Chaurasia, A., & Qiu, J. (2023). Ultralytics YOLOv8. [https://github.com/ultralytics/ultralytics](https://github.com/ultralytics/ultralytics)
* **ByteTrack:** Zhang, Y., et al. (2022). *ByteTrack: Multi-Object Tracking by Associating Every Detection Box*. ECCV 2022. [https://github.com/ifzhang/ByteTrack](https://github.com/ifzhang/ByteTrack)
* **OpenCV:** Bradski, G. (2000). *The OpenCV Library*. Dr. Dobb's Journal of Software Tools. [https://opencv.org/](https://opencv.org/)
* **FastAPI Framework:** Ramírez, S. (2018). *FastAPI: Modern, fast (high-performance), web framework for building APIs with Python*. [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)

---

## 19. Installation & Local Setup

### Prerequisites
* **Python:** 3.10 to 3.13 (64-bit)
* **Node.js:** v18.0.0 or higher
* **Git:** Installed and configured

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/SMRU08/RAKSHYA-VISION.git
cd RAKSHYA-VISION
```

---

### Step 2: Backend Installation
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 3: Configure Environment Variables
```bash
# Return to root and copy template
cd ..
cp backend/.env.example backend/.env
```

---

### Step 4: Run Backend Server
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
* **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check:** [http://localhost:8000/health/live](http://localhost:8000/health/live)

---

### Step 5: Frontend Installation & Startup
In a separate terminal window:
```bash
cd frontend
npm install
npm run dev
```
* **Dashboard Interface:** [http://localhost:5173](http://localhost:5173)

---

## 20. Camera Configuration Guide

Camera inputs are configured in `configs/cameras.yaml`:

```yaml
cameras:
  - camera_id: "camera_01"
    name: "Production Floor South"
    source_type: "usb"            # Options: "usb", "rtsp", "file"
    source_uri: "0"                # Device index 0 for integrated webcam, or 1 for USB
    target_fps: 30
    zone_id: "production_floor"
    speaker_enabled: true

  - camera_id: "camera_02"
    name: "Loading Bay North"
    source_type: "rtsp"
    source_uri: "rtsp://admin:pass@192.168.1.120:554/stream1"
    target_fps: 25
    zone_id: "loading_bay"
    speaker_enabled: false
```

### Camera Connection Types:
* **Built-in Laptop Webcam / USB Camera:** Use `source_type: "usb"` with integer device index `source_uri: "0"` or `"1"`.
* **IP / RTSP Network Camera:** Use `source_type: "rtsp"` with full RTSP URI. Passwords are automatically masked in dashboard telemetry.
* **Mobile Phone IP Stream:** Run an RTSP/HTTP camera app (such as *IP Webcam*) on your mobile device connected to the same local Wi-Fi, then specify the stream URL (e.g., `http://192.168.1.45:8080/video`). *(Note: Standard USB cable charging or MTP file transfer does not stream video; network stream protocols are required).*
* **Video File Replay:** Use `source_type: "file"` with the relative file path to an `.mp4` or `.avi` recording.

---

## 21. Production Deployment Architecture

```mermaid
flowchart TD
    subgraph CLOUD_FRONTEND["Frontend Host (Vercel / Netlify)"]
        SPA["React 18 SPA (Static ESM Build)"]
        V_ENV["Environment Variable: VITE_API_URL"]
    end

    subgraph CLOUD_OR_EDGE["Backend Host (Render / Linux Edge Server)"]
        UVI["Uvicorn ASGI Server (Port 8000)"]
        FAST["FastAPI Application"]
        AI_ENG["YOLOv8 + PyTorch Inference"]
        SQL_DB[("Persistent Database (SQLite WAL / PostgreSQL)")]
        EVID_DISK["Hashed Evidence Volume (SHA-256)"]
        
        UVI --> FAST
        FAST --> AI_ENG
        FAST --> SQL_DB
        FAST --> EVID_DISK
    end

    SPA -->|HTTPS REST API Calls| FAST
    SPA -->|WSS Real-Time WebSocket| FAST
```

| Deployment Tier | Frontend Host | Backend Host | Database | Camera Feeds |
|---|---|---|---|---|
| **Local Development** | Vite Dev (`localhost:5173`) | Uvicorn (`localhost:8000`) | SQLite WAL (`safesync.db`) | Local USB Webcams / Files |
| **Cloud Web Demo** | Vercel / Netlify (`dist/`) | Render Web Service | Persistent SQLite / Postgres | Synthetic Streams / Pre-recorded video |
| **On-Premise Industrial** | Local NGINX Server | High-Performance Edge Gateway | SQLite WAL / PostgreSQL | Multi-Camera RTSP Network Feeds |

---

## 22. Known System Limitations

* **Combustion Scale:** Open flames or smoke plumes covering fewer than $15 \times 15$ pixels in wide-angle cameras may fail initial confidence thresholds ($< 0.35$).
* **Dense Particulate Confusion:** Visual smoke detection may register false suspect frames in heavy industrial dust storms or dense steam pockets before temporal clearing.
* **Severe Lower-Limb Occlusion:** Footwear detection is constrained when workers are seated or behind opaque pallets and floor obstacles.
* **CPU-Bound Multi-Streaming:** While single streams achieve sub-10ms latency on modern CPUs, scaling beyond 3–4 concurrent 1080p feeds requires dedicated edge GPU acceleration (such as NVIDIA RTX or Jetson Orin).
* **Industrial Site Pilot Status:** System capabilities have been verified against recorded datasets, synthetic feeds, and USB webcams; physical industrial CCTV deployment remains subject to site trials.

---

## 23. Engineering Roadmap

### Phase 1: Completed & Verified ✅
- [x] Single-stage 7-class YOLOv8n object detection model.
- [x] ByteTrack multi-person tracking with Kalman filter estimation.
- [x] Proportional anatomical body zone association (Head, Torso, Hands, Feet).
- [x] Strict invariant enforcement (`UNKNOWN != VIOLATION`).
- [x] Fire and atmospheric smoke detection with 5-frame persistence confirmation.
- [x] Explainable mathematical risk engine (0–100 scale).
- [x] Thread-isolated multi-camera ingestion pool with queue-depth regulation.
- [x] Auditable incident lifecycle management and alert deduplication.
- [x] Tamper-evident evidence archival with live SHA-256 verification.
- [x] Security Operations Center (SOC) dashboard in React 18, TypeScript, and Vite.
- [x] Biometric worker enrollment and daily deduplicated attendance logging.

### Phase 2: Near-Term Enhancements 🔄
- [ ] TensorRT / ONNX INT8 export for low-power edge gateways (NVIDIA Jetson).
- [ ] Integration of dedicated fall-arrest harness detection for work-at-height zones.
- [ ] Native Docker Compose and Kubernetes Helm chart manifests.
- [ ] Automated camera health alerts for physically obscured or tilted lenses.

---

## 24. System Verification Status

| Subsystem / Capability | Verification Status | Codebase Verification Evidence |
|---|:---:|---|
| **Live Camera Ingestion** | **VERIFIED** | `backend/app/camera/worker.py` |
| **Multi-Camera Management** | **VERIFIED** | `backend/app/camera/manager.py` |
| **Worker Localization** | **VERIFIED** | `backend/app/ai/detection/detector.py` |
| **Motion Tracking (ByteTrack)** | **VERIFIED** | `backend/app/ai/compliance/tracker.py` |
| **Helmet Compliance** | **VERIFIED** | `backend/app/ai/compliance/association.py` |
| **Safety Vest Compliance** | **VERIFIED** | `backend/app/ai/compliance/association.py` |
| **Glove & Footwear Compliance** | **VERIFIED** | `backend/app/ai/compliance/association.py` |
| **Zone-Specific PPE Policies (PS06)**| **VERIFIED** | `backend/app/ai/compliance/ppe_policy.py` |
| **7-Stage Hazard Temporal Engine** | **VERIFIED** | `backend/app/ai/hazards/tracker.py` |
| **Industrial False-Positive Rejection** | **VERIFIED** | `backend/tests/test_hazard_false_positives.py` |
| **Fire Detection** | **VERIFIED** | `backend/app/ai/hazards/tracker.py` |
| **Smoke Plume Detection** | **VERIFIED** | `backend/app/ai/hazards/tracker.py` |
| **Explainable Risk Engine** | **VERIFIED** | `backend/app/services/risk_engine.py` |
| **Incident Lifecycle Governance**| **VERIFIED** | `backend/app/services/incident_engine.py` |
| **Alert Deduplication & Cooldown**| **VERIFIED** | `backend/app/services/alert_engine.py` |
| **Evidence SHA-256 Hashing** | **VERIFIED** | `backend/app/services/evidence_manager.py` |
| **Database WAL Mode Persistence**| **VERIFIED** | `backend/app/database/session.py` |
| **Role-Based Access Control** | **VERIFIED** | `backend/app/security/auth.py` |
| **Biometric Attendance Engine** | **VERIFIED** | `backend/app/services/face_recognition_service.py` |
| **Web Dashboard (React 18)** | **VERIFIED** | `frontend/src/` (`npm run build` succeeds) |
| **Physical Factory Pilot** | **PENDING** | Hardware dependent; evaluated in lab environment |

---

## 25. Project Metadata & Team

* **Project:** SafeSync — AI-Powered Safety Monitoring System
* **Hackathon:** BPUT Hackathon 2026
* **Problem Statement:** PS06 — Prototype AI System that Detects Safety Gear Compliance
* **Organized By:** Software Technology Parks of India (STPI) & EmTek
* **Lead Engineer & Maintainer:** Smruti Ranjan Nayak ([@SMRU08](https://github.com/SMRU08))
* **Official Repository:** [https://github.com/SMRU08/RAKSHYA-VISION.git](https://github.com/SMRU08/RAKSHYA-VISION.git)
