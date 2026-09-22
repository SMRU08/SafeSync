# RAKSHYA VISION

> **AI Vision-Based Safety Monitoring System**  
> Real-Time PPE Compliance Analysis, Multi-Worker Tracking, Fire & Smoke Detection, Risk Assessment, and Incident Awareness.

**BPUT Hackathon 2026**  
**Problem Statement:** PS06 — Build a prototype AI system that detects safety gear compliance  
**Organization:** Software Technology Parks of India (STPI) & EmTek  
**Repository:** [https://github.com/SMRU08/RAKSHYA-VISION.git](https://github.com/SMRU08/RAKSHYA-VISION.git)  
**System Status:** Complete & Verified (160/160 Unit Tests Passing, 39/39 Integration Scenarios Verified)  
**Documentation Index:** [docs/README.md](docs/README.md) | [BPUT Hackathon Deck](BPUT-HACKATHON-2026/README.md) | [BPUT Executive Summary](BPUT-HACKATHON-2026/README2.md) | [VS Code Run Guide](VSCODE_GUIDE.md)  

---


## 1. Problem Statement

Industrial workplaces, construction sites, manufacturing floors, and hazardous infrastructure require continuous adherence to Personal Protective Equipment (PPE) standards to prevent severe injury and loss of life. Standard regulatory requirements stipulate mandatory protective gear including:

- **Safety Helmets:** Head protection from falling objects, collisions, and overhead hazards.
- **High-Visibility Safety Vests:** Torso visibility for heavy machinery operators and vehicular traffic.
- **Protective Gloves:** Hand safety against chemical, thermal, and mechanical hazards.
- **Safety Footwear:** Toe and puncture protection against crush risks and sharp floor objects.

Simultaneously, unexpected environmental emergencies such as **combustion (fire)** and **atmospheric emissions (smoke)** pose catastrophic threats if not detected in their earliest developmental seconds.

### Operational Challenges in Traditional Monitoring:
- **Continuous Human Observation Fatigue:** Safety officers cannot simultaneously maintain vigilance across dozens of CCTV feeds for hours without perceptual lapses.
- **Inconsistent Enforcement:** Manual spot-checks capture isolated moments rather than continuous operational compliance.
- **Delayed Emergency Response:** Traditional localized smoke alarms or manual call points often activate only after combustion has propagated significantly.
- **Lack of Actionable Evidence:** Incident investigations frequently suffer from missing visual context, ambiguous timestamps, or unverified logs.

### Intended Objectives:
RAKSHYA VISION addresses Problem Statement **PS06** by delivering an automated, edge-ready artificial intelligence vision system capable of ingesting video feeds (recorded video, USB webcams, IP cameras, and network streams), performing multi-task object detection, tracking individual workers anonymously, verifying anatomical PPE compliance, confirming fire and smoke signatures, calculating explainable risk scores, and alerting human operators in real time.

---

## 2. The RAKSHYA VISION Approach

RAKSHYA VISION is engineered as a deterministic, decoupled multi-stage computer vision and safety operations pipeline. Rather than treating safety monitoring as a monolithic neural network classifier, the system decouples spatial detection from temporal state machines and risk governance:

```
Camera Observations → Detected Objects → Worker Tracks → PPE Associations → Compliance States → Hazard States → Risk Information → Incidents → Operator Alerts
```

### Core Engineering Principles:
1. **Canonical Class Object Detection:** A single-stage, multi-task convolutional detector predicts physical objects (`person`, `helmet`, `safety_vest`, `gloves`, `safety_footwear`, `fire`, `smoke`).
2. **Absence Derived Through Anatomical Association:** The model does not attempt to learn noisy negative classes such as `no_helmet` or `no_vest`. Non-compliance is derived deterministically by checking whether a detected PPE item spatially belongs to a specific worker's anatomical zone (head, torso, hands, feet).
3. **Strict Policy on Ambiguity (`UNKNOWN != VIOLATION`):** Temporary occlusion, poor camera angles, or boundary clipping place a PPE item in an `UNKNOWN` state. The system **never** marks an unknown state as a violation. Only persistent, confirmed `ABSENT` observations generate safety violations.
4. **Temporal State Confirmation:** Single-frame flickers or detection dropouts never trigger alarms. Violations require $N_{\text{confirm}} = 3$ consecutive frames; hazards require $N_{\text{confirm}} = 5$ frames.
5. **Deterministic, Explainable Risk Scoring:** Safety risks are scored on a scale from $0$ to $100$ using clear, mathematically transparent factors rather than opaque neural predictions.
6. **Fault-Isolated Architecture:** A failure in video capture, disk quota, or external notification never halts the core monitoring pipeline or incident recording.

---

## 3. System Architecture

```mermaid
flowchart TD
    subgraph INGESTION["1. Ingestion Layer"]
        C1["RTSP / IP Camera"]
        C2["USB Webcam"]
        C3["Recorded Video / File"]
        C4["Network Stream / Phone"]
        CM["Multi-Camera Manager"]
        C1 --> CM
        C2 --> CM
        C3 --> CM
        C4 --> CM
    end

    subgraph VISION["2. AI Vision & Inference"]
        PRE["Frame Acquisition & Preprocessing<br>384x384 RGB"]
        YOLO["YOLOv8 Multi-Task Detector<br>best.pt"]
        DET["Detections: person, helmet, vest,<br>gloves, footwear, fire, smoke"]
        PRE --> YOLO
        YOLO --> DET
    end

    subgraph TRACKING["3. Tracking & Association"]
        BT["ByteTrack Algorithm<br>Kalman Filter + Hungarian"]
        ANAT["Anatomical Spatial Associator<br>Head, Torso, Hands, Feet"]
        TEMP_PPE["Temporal Compliance Tracker<br>N_confirm = 3"]
        TEMP_HAZ["Hazard Tracker & State Machine<br>N_confirm = 5"]
        BT --> ANAT
        ANAT --> TEMP_PPE
    end

    subgraph RISK_ALERT["4. Risk, Incident & Alert Governance"]
        NORM["Event Normalizer<br>UNKNOWN != VIOLATION Rule"]
        RISK["Risk Engine<br>0–100 Score & Zone Multipliers"]
        INC["Incident Lifecycle Engine<br>OPEN, ACK, RESOLVED, DISMISSED"]
        ALERT["Alert Engine<br>Deduplication & Cooldown"]
        NORM --> RISK
        RISK --> INC
        INC --> ALERT
    end

    subgraph EVIDENCE["5. Evidence Storage & DB"]
        EV_MGR["Evidence Manager<br>SHA-256 Checksum & Quota"]
        EV_DISK["outputs/evidence/<br>Hashed JPEG Frames"]
        DB["SQLite Database<br>WAL Mode: rakshya_vision.db"]
        EV_MGR --> EV_DISK
    end

    subgraph PRESENTATION["6. Distribution & Dashboard"]
        EXT["External Dispatcher<br>Webhook, Email SMTP, Slack"]
        WS["WebSocket Broadcaster<br>/ws/alerts"]
        REST["FastAPI REST Endpoints<br>/api/v1/..."]
        SOC["React 18 / Vite SOC<br>Web Dashboard"]
    end

    CM --> PRE
    DET --> BT
    DET --> TEMP_HAZ
    TEMP_PPE --> NORM
    TEMP_HAZ --> NORM
    INC --> EV_MGR
    INC --> DB
    ALERT --> DB
    ALERT --> EXT
    ALERT --> WS
    ALERT --> REST
    WS --> SOC
    REST --> SOC
```

---

## 4. End-to-End Processing Pipeline

```mermaid
flowchart LR
    subgraph S1["1. Ingestion"]
        direction TB
        IN["Video / RTSP / Webcam"] --> PRE["Resize & Normalize<br>(384x384 RGB)"]
    end

    subgraph S2["2. AI Detection"]
        direction TB
        PRE --> YOLO["YOLOv8n Multi-Task<br>(best.pt)"]
        YOLO --> DETS["7 Canonical Classes"]
    end

    subgraph S3["3. Tracking & Association"]
        direction TB
        DETS --> BT["ByteTrack Algorithm<br>(Kalman Filter)"]
        BT --> ANAT["Anatomical Spatial<br>Zone Matcher"]
        ANAT --> TEMP["Temporal Confirmation<br>(N=3 / N=5 Frames)"]
    end

    subgraph S4["4. Decision Engine"]
        direction TB
        TEMP --> RISK["Explainable Risk<br>Engine (0-100)"]
        RISK --> INC["Incident Lifecycle<br>Governance"]
        INC --> EV["SHA-256 Evidence<br>Archival"]
    end

    subgraph S5["5. Distribution & UI"]
        direction TB
        INC --> WS["WebSocket Channel<br>(/ws/alerts)"]
        WS --> SOC["React 18 Operator HUD"]
        INC --> EXT["External Dispatcher<br>(Webhook / Email / Slack)"]
    end

    S1 --> S2 --> S3 --> S4 --> S5
```

### 4.1 Camera & Video Ingestion
The system supports multiple input formats managed by `backend/app/camera/worker.py` and `backend/app/camera/manager.py`:
- **Local USB Webcam:** Ingested via OpenCV device indexing (`0`, `1`). Tested and verified.
- **Recorded Video Files:** Supports `.mp4`, `.avi`, `.mkv` for offline audits and verification. Tested and verified.
- **RTSP / IP Cameras:** Ingests network video streams with credentials securely masked (`rtsp://admin:***@192.168.1.50:554/stream1`). Architecturally implemented with bounded exponential backoff reconnection. Physical industrial CCTV pilot is marked *Not Tested* due to local hardware unavailability.
- **Android / Mobile Network Stream:** Ingests IP webcam streams from mobile devices over local Wi-Fi. Tested and verified.

### 4.2 Frame Preprocessing
Incoming frames are scaled to $384 \times 384$ pixels matching the trained neural network resolution, normalized to $[0, 1]$, and converted to RGB tensor representations.

### 4.3 Object Detection
Frames pass through the production YOLOv8n checkpoint (`models/detection/ppe_fire_smoke_v2/weights/best.pt`). Checksum integrity is strictly verified on load via SHA-256 against `models/registry/model_registry.yaml`.

### 4.4 Worker Tracking (ByteTrack)
The system tracks individual workers using a two-stage Hungarian assignment algorithm coupled with an 8-state Kalman Filter (`KalmanBoxTracker`):
- Assigns stable, anonymous integer IDs (`Worker #1`, `Worker #2`).
- Recovers lost tracks across brief occlusions using low-confidence detection matching ($0.1 \le \text{conf} \le 0.5$).
- Does not collect or store biometric data or Personally Identifiable Information (PII).

### 4.5 Anatomical Spatial Association
Detected PPE items are mapped to individual worker bounding boxes based on relative human anatomical proportions:
- **Helmet:** Must lie in the upper $25\%$ of the person bounding box with horizontal centering.
- **Safety Vest:** Must overlap the central torso region ($15\%$ to $65\%$ vertical height).
- **Gloves:** Must reside in the lower lateral regions or wrist zones.
- **Footwear:** Must reside in the bottom $20\%$ of the bounding box.

### 4.6 Temporal Validation
Single-frame detections are treated as unconfirmed observations:
- **PPE State Confirmation:** Requires $3$ consecutive matching frames before transitioning a worker's PPE state from `UNKNOWN` to `PRESENT` or `ABSENT`.
- **Dropout Tolerance:** A worker who briefly looks away or walks behind a post retains their compliance state for up to $5$ frames without triggering a false alarm.

### 4.7 Fire & Smoke Hazard Analysis
Thermal and atmospheric combustion signatures are processed in parallel:
- Fire and smoke are tracked as spatial hazard objects with independent bounding boxes.
- Categorized into relationships: `ISOLATED_FIRE`, `ISOLATED_SMOKE`, `FIRE_WITH_SMOKE_PLUME`, `SMOKE_PRECEDING_FIRE`.
- Requires $5$ consecutive confirmation frames before escalating to `CONFIRMED`.

### 4.8 Risk Engine
Scores events on an explainable scale from $0$ to $100$, accounting for hazard category, duration of persistence, number of exposed workers, and facility zone risk multipliers.

### 4.9 Incident & Alert Engines
Groups events into persistent incidents. Applies deduplication, cooldown suppression, and automated severity escalation if an emergency persists beyond $30$ seconds.

### 4.10 Operator Dashboard
Broadcasting occurs via WebSockets directly into the React 18 Security Operations Center (SOC) dashboard, providing live visual telemetry, checklist HUDs, and human-in-the-loop action buttons.

---

## 5. PPE Compliance Governance

### Canonical Classes & The Absence Philosophy
The object detector is trained on 7 canonical classes:

| ID | Class Name | Category | Function |
|:---|:---|:---|:---|
| `0` | `person` | Worker | Primary tracking anchor |
| `1` | `helmet` | PPE Item | Hard hat head protection |
| `2` | `safety_vest` | PPE Item | High-visibility vest |
| `3` | `gloves` | PPE Item | Hand safety |
| `4` | `safety_footwear` | PPE Item | Safety boots / shoes |
| `5` | `fire` | Hazard | Open combustion / flames |
| `6` | `smoke` | Hazard | Plumes / airborne particulate |

The model does not use artificial negative classes like `no_helmet`. Detecting "nothing" on a head is inherently noisy in computer vision. Instead, RAKSHYA VISION verifies the presence of the required item within the anatomical sub-region. If absent across multiple confirmed frames, a violation is declared.

### Worker States
Workers are assigned one of four definitive states:
- **`SAFE`:** All required PPE items for the current zone are confirmed `PRESENT`.
- **`ATTENTION`:** Minor or secondary PPE items (e.g. gloves in low-risk zones) are pending or missing.
- **`VIOLATION`:** One or more mandatory PPE items (e.g. helmet or safety vest in high-risk zones) are confirmed `ABSENT` after temporal validation.
- **`UNKNOWN`:** The worker is occluded, partially outside the camera frame, or undergoing initial tracking acquisition.

```mermaid
flowchart TD
    P["Worker Detected (Person Class)"] --> ZONES["Partition Bounding Box into Anatomical Sub-Zones"]
    
    ZONES --> Z_HEAD["Head Zone (Top 0–25%)"]
    ZONES --> Z_TORSO["Torso Zone (15–65%)"]
    ZONES --> Z_HANDS["Hand Zones (Lateral / Wrists)"]
    ZONES --> Z_FEET["Foot Zone (Bottom 80–100%)"]

    Z_HEAD --> CHK_H{"Helmet Detected?"}
    Z_TORSO --> CHK_V{"Vest Detected?"}

    CHK_H -- "Yes" --> H_OK["Helmet: PRESENT"]
    CHK_H -- "No" --> OCC_H{"Occluded / Clipped?"}
    OCC_H -- "Yes" --> H_UNK["Helmet: UNKNOWN<br>(No Alert Triggered)"]
    OCC_H -- "No" --> H_CONF{"Absence >= 3 Frames?"}
    H_CONF -- "No" --> H_PEND["Pending Confirmation"]
    H_CONF -- "Yes" --> H_VIO["Helmet: VIOLATION (ABSENT)"]

    CHK_V -- "Yes" --> V_OK["Vest: PRESENT"]
    CHK_V -- "No" --> V_CONF{"Absence >= 3 Frames?"}
    V_CONF -- "No" --> V_PEND["Pending Confirmation"]
    V_CONF -- "Yes" --> V_VIO["Vest: VIOLATION (ABSENT)"]

    H_OK & V_OK --> STATE_SAFE["Worker State: SAFE"]
    H_UNK --> STATE_UNK["Worker State: UNKNOWN"]
    H_VIO --> STATE_VIOL["Worker State: VIOLATION"]
    V_VIO --> STATE_VIOL
```

> [!IMPORTANT]
> **Mandatory Safety Rule:** An `UNKNOWN` state **strictly never** triggers an alert or violation. Violations are only generated when temporal evidence proves confirmed absence.

---

## 6. Fire & Smoke Monitoring

Fire and smoke hazards are decoupled from worker compliance logic:

```mermaid
stateDiagram-v2
    [*] --> IDLE: Continuous Ingestion
    IDLE --> SUSPECTED: Flame or Smoke Detected (Conf >= 0.40)
    SUSPECTED --> IDLE: Transient Disappears (< 5 frames)
    SUSPECTED --> CONFIRMED: Detection Persists >= 5 Frames
    CONFIRMED --> CLEARED: Absence Persists >= 10 Frames
    CLEARED --> IDLE: Return to Normal Monitoring
```

### Operational Behavior:
- **`SUSPECTED` State:** When flames or smoke are first detected, the hazard enters `SUSPECTED`. No siren or external emergency dispatch is triggered yet, eliminating false alarms from camera sensor artifacts or transient reflections.
- **`CONFIRMED` State:** If detection persists for $5$ consecutive frames, the hazard transitions to `CONFIRMED`. An emergency incident is generated immediately, rated `HIGH` or `CRITICAL`.
- **`CLEARED` State:** If the hazard disappears for $10$ consecutive frames, the event is marked `CLEARED` and the incident is marked for resolution.

### Known Environmental Limitations:
- Very small, distant smoke plumes in low-resolution cameras ($< 15 \times 15$ pixels) may fall below confidence thresholds.
- Optical smoke detection can encounter visual confusion in environments with dense steam, dust storms, or welding vapor. RAKSHYA VISION complements physical ionization/optical smoke detectors; it does not replace certified fire alarms.

---

## 7. Explainable Risk Engine

The `RiskEngine` calculates a deterministic score from $0$ to $100$ according to configurable weights defined in `configs/risk_policy.yaml`:

$$\text{Risk Score} = \min\left(100, \; (\text{Base Severity} + \text{Persistence Factor} + \text{Worker Density Factor}) \times \text{Zone Multiplier}\right)$$

```mermaid
flowchart TD
    subgraph IN["Input Risk Factors"]
        B["Base Severity Weight<br>(Fire: +60, Smoke: +40, Helmet: +35, Vest: +25)"]
        P["Temporal Persistence<br>(+1 pt/sec up to +20)"]
        D["Worker Exposure Density<br>(+10 pts per additional worker)"]
        Z["Zone Risk Multiplier<br>(Loading Bay: 1.3x, Workshop: 1.0x, Break Room: 0.7x)"]
    end

    subgraph CALC["Risk Formula Computation"]
        SUM["Raw Score = Base Severity + Persistence + Density"]
        MULT["Weighted Score = Raw Score * Zone Multiplier"]
        CLAMP["Final Score = min(100, max(0, Weighted Score))"]
        SUM --> MULT --> CLAMP
    end

    subgraph TIERS["Risk Level Protocol"]
        CLAMP --> T1["0 – 29: LOW<br>(Audit Log Only)"]
        CLAMP --> T2["30 – 59: MEDIUM<br>(Dashboard Visual Banner)"]
        CLAMP --> T3["60 – 79: HIGH<br>(Visual + Audio Chime + Ack Required)"]
        CLAMP --> T4["80 – 100: CRITICAL<br>(Modal Takeover + Auto External Dispatch)"]
    end

    B & P & D --> SUM
    Z --> MULT
```

### Factor Breakdown:
- **Base Severity:**
  - Fire Detected: $+60$
  - Smoke Detected: $+40$
  - Missing Helmet: $+35$
  - Missing Safety Vest: $+25$
  - Missing Footwear / Gloves: $+15$
- **Persistence Factor:** Adds $+1$ point per elapsed second of unmitigated hazard (capped at $+20$).
- **Worker Density:** Adds $+10$ points per additional worker exposed in the hazard boundary.
- **Zone Risk Multiplier:**
  - `LOADING_BAY` / `ELECTRICAL_ROOM` (High Risk): $\times 1.3$
  - `GENERAL_WORKSHOP` (Standard): $\times 1.0$
  - `BREAK_ROOM` (Low Risk): $\times 0.7$

### Risk Tiers:
| Score Range | Risk Level | Action Protocol |
|:---|:---|:---|
| `0 – 29` | `LOW` | Logged for compliance metrics; no intrusive sirens. |
| `30 – 59` | `MEDIUM` | Visual alert banner on dashboard; standard cooldown. |
| `60 – 79` | `HIGH` | Immediate visual warning; audio chime; operator acknowledgement requested. |
| `80 – 100` | `CRITICAL` | High-priority modal takeover; persistent alert banner; automated external dispatch. |

---

## 8. Incident Lifecycle

Incidents represent persistent, multi-event safety situations over time.

```mermaid
stateDiagram-v2
    [*] --> OPEN: Confirmed Event / Hazard
    OPEN --> ACKNOWLEDGED: Operator Acknowledges Alert
    OPEN --> ESCALATED: Persistence > 30s without resolution
    ACKNOWLEDGED --> RESOLVED: Hazard Cleared / Worker Leaves
    OPEN --> RESOLVED: Automated Hazard Clearing
    OPEN --> DISMISSED: Operator Dismisses (False Positive)
    ACKNOWLEDGED --> DISMISSED: Operator Overrides
    RESOLVED --> [*]
    DISMISSED --> [*]
```

### Lifecycle Mechanics:
- **Creation:** A new `Incident` is generated when an event occurs with no open incident matching the same camera and event type.
- **Deduplication:** Subsequent observations for the same worker or hazard update the existing incident rather than creating duplicate database rows.
- **Cooldown Suppression:** Configurable suppression timers (e.g. 60s for missing helmet, 30s for fire) prevent operator notification fatigue.
- **Escalation:** If an unacknowledged incident remains active past `escalation_persistence_seconds` (default: 30s), its severity escalates (e.g. `HIGH` $\rightarrow$ `CRITICAL`).

---

## 9. Alert Engine & Multi-Channel Providers

The `AlertEngine` decouples internal telemetry from external notifications:

```mermaid
flowchart LR
    INC["Incident / Safety Event<br>(Confirmed Breach)"] --> DEDUP{"Deduplication &<br>Cooldown Check"}
    
    DEDUP -- "Within Cooldown" --> SUPPRESS["Suppress Duplicate<br>(Prevent Alert Fatigue)"]
    
    DEDUP -- "New / Escalated" --> FANOUT["Alert Dispatch Engine"]
    
    FANOUT --> DB[("SQLite WAL Audit Log<br>Table: alert_history")]
    FANOUT --> EV["Evidence Manager<br>(SHA-256 Hashed Snapshot)"]
    FANOUT --> WS["WebSocket Broadcaster<br>(/ws/alerts to React SOC)"]
    
    subgraph EXT["Configurable External Providers"]
        FANOUT --> WH["HTTP Webhook<br>(HMAC-SHA256 Signed)"]
        FANOUT --> SMTP["Email Dispatcher<br>(SMTP / STARTTLS)"]
        FANOUT --> SLACK["Slack Webhook<br>(#safety-alerts)"]
    end
```

### Provider Implementation Status:

| Provider | Status | Implementation Details |
|:---|:---|:---|
| **Internal Dashboard** | **Implemented & Verified** | Bi-directional WebSocket (`/ws/alerts`) with instant JSON dispatch. |
| **Database Audit Trail** | **Implemented & Verified** | Every alert action logged in `alert_history` table with timestamps and operator reasons. |
| **HTTP Webhook** | **Implemented — Configurable** | Sends JSON payloads with cryptographic `X-Rakshya-Signature` (HMAC-SHA256) and exponential retry. |
| **Email (SMTP)** | **Implemented — Configurable** | Sends MIME multipart notifications via SMTP with STARTTLS encryption. |
| **SMS Gateway** | **Implemented — Gateway Stub** | Structured SMS integration stub ready for Twilio/AWS SNS API credentials. |

> [!NOTE]
> External alert channels remain in `NOT_CONFIGURED` status until production SMTP credentials or Webhook URLs are provided in `.env`. The system never fabricates delivery receipts.

---

## 10. Human-Centric Operator Dashboard

The user interface is built with React 18, TypeScript, and Vite, running as a Security Operations Center (SOC) dark-theme dashboard.

### Core Dashboard Features:
1. **Overview View:** Real-time KPI summary (active alerts, critical hazards, compliant workers count, camera status).
2. **Cameras Matrix:** Live multi-camera grid showing FPS, capture source, resolution, and operational start/stop controls.
3. **Workers & PPE Inspector:** Displays anonymous worker cards with ByteTrack IDs and checklist HUD badges.
4. **Fire & Smoke Monitor:** Spatial threat cards detailing detected combustion coordinates, confidence, and containment zones.
5. **Alerts & Incidents Center:** Filterable audit table with immediate human-in-the-loop actions (`Acknowledge`, `Resolve`, `Dismiss`).
6. **Incident Evidence Modal:** Displays cryptographically verified snapshot captures with SHA-256 integrity badges and secure download links.
7. **System Analytics:** Distribution charts computed from live SQLite records without fake data.

---

## 11. Detection Classes

The model detects 7 canonical classes verified in the model registry:

| Class ID | Class Name | Function / Object | Confidence Threshold |
|:---:|:---|:---|:---:|
| `0` | `person` | Worker anchor bounding box | `0.40` |
| `1` | `helmet` | Hard hat / protective helmet | `0.30` |
| `2` | `safety_vest` | High-visibility reflective vest | `0.30` |
| `3` | `gloves` | Protective handwear | `0.25` |
| `4` | `safety_footwear` | Steel-toe / industrial boots | `0.25` |
| `5` | `fire` | Open flames / combustion | `0.35` |
| `6` | `smoke` | Atmospheric smoke plumes | `0.35` |

---

## 12. Technology Stack

| Layer | Technology | Purpose |
|:---|:---|:---|
| **Core Language** | Python 3.13 | Backend runtime, computer vision pipeline, API |
| **Computer Vision** | OpenCV (`opencv-python` 4.11) | Video decoding, frame preprocessing, annotations |
| **Deep Learning** | PyTorch 2.6.0 + Ultralytics YOLOv8 | Convolutional object detection model inference |
| **Worker Tracking** | Custom ByteTrack (NumPy + SciPy) | Multi-object tracking with 8-state Kalman Filter |
| **Web Framework** | FastAPI 0.115 + Starlette | Asynchronous REST API, WebSocket server |
| **Data Validation** | Pydantic v2 | Strict schema validation, configuration typing |
| **Database ORM** | SQLAlchemy 2.0 | Relational database mapping and migrations |
| **Database Engine** | SQLite 3 (WAL Mode) | Thread-safe edge persistence with 5s busy timeout |
| **Authentication** | PyJWT + Passlib (PBKDF2-HMAC-SHA256) | Token authentication with 600,000 iterations |
| **Observability** | Prometheus 0.0.4 + psutil | Metrics exposition and system telemetry |
| **Frontend Framework** | React 18.3 + TypeScript 5.7 | Component architecture, type safety |
| **Build Tooling** | Vite 6.4 | Modern ESM bundler and development server |
| **UI Components** | Lucide React | Clean icon set |
| **Testing Framework** | Pytest 9.1 + HTTPX | Automated test runner, client simulation |

---

## 13. Repository Structure

```
RAKSHYA-VISION/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── compliance/       # ByteTrack, anatomical association, temporal state machine
│   │   │   ├── detection/        # YOLO detector, ModelLoader, video processor
│   │   │   ├── hazards/          # Fire & smoke tracker, spatial analysis, temporal confirmation
│   │   │   └── risk/             # Pydantic schemas for events, risks, and alerts
│   │   ├── api/
│   │   │   ├── alerts.py         # Alert lifecycle endpoints
│   │   │   ├── auth.py           # Authentication & RBAC endpoints
│   │   │   ├── cameras.py        # Camera worker controls & snapshot API
│   │   │   ├── compliance.py     # Worker compliance analysis endpoints
│   │   │   ├── detection.py      # Raw detection endpoints
│   │   │   ├── evidence.py       # Evidence archival & download API
│   │   │   ├── hazards.py        # Hazard analysis endpoints
│   │   │   ├── monitoring.py     # Liveness, readiness, and Prometheus metrics
│   │   │   └── websocket.py      # Live WebSocket event broadcaster
│   │   ├── camera/               # Multi-Camera Manager & thread-isolated workers
│   │   ├── database/             # SQLite session, engine, WAL configuration
│   │   ├── models/               # SQLAlchemy ORM models (User, Incident, Alert, Evidence, etc.)
│   │   ├── security/             # Password hashing, JWT token creation, RBAC guards
│   │   ├── services/             # AlertEngine, RiskEngine, EvidenceManager, MetricsCollector
│   │   ├── config.py             # Centralized typed settings & secret protection
│   │   └── main.py               # FastAPI application entrypoint & lifespan
│   ├── tests/                    # 160 automated pytest unit and integration tests
│   └── requirements.txt          # Python dependencies
├── configs/
│   ├── alert_policy.yaml         # Cooldown and escalation rules
│   ├── cameras.yaml              # Multi-camera sources and resolution configs
│   ├── detection.yaml            # YOLO confidence and NMS thresholds
│   ├── production.yaml           # Centralized production configuration
│   └── risk_policy.yaml          # Risk factor scoring and zone multipliers
├── datasets/
│   ├── manifests/                # Checksums, class mappings, version manifests
│   ├── processed/                # Unified train/val/test YOLO dataset (22,453 images)
│   ├── README.md                 # Dataset usage instructions
│   └── SOURCES.md                # Official source registry and licensing
├── docs/                         # Technical documentation & engineering references
│   ├── architecture/             # System design, processing pipeline, data contracts, database
│   ├── ai/                       # Detection model, model registry, PPE compliance, tracking, hazards
│   ├── operations/               # Multi-camera management, alerts, incidents, evidence, monitoring
│   ├── deployment/               # Installation, configuration, production setup, troubleshooting
│   ├── security/                 # Authentication, RBAC, security model & threat mitigations
│   ├── testing/                  # Testing strategy, integration report, benchmarks, known issues
│   ├── datasets/                 # Dataset strategy & source provenance
│   ├── reports/                  # Production readiness scorecard & known limitations
│   └── README.md                 # Master documentation index
├── frontend/
│   ├── src/
│   │   ├── components/           # SOC UI components (Alerts, Cameras, Modals)
│   │   ├── pages/                # Views (Overview, Cameras, Workers, Hazards, Alerts, Analytics)
│   │   ├── services/             # REST API and WebSocket client services
│   │   ├── types/                # TypeScript schemas matching backend models
│   │   └── App.tsx               # Root React application
│   ├── package.json              # Frontend dependencies
│   └── vite.config.ts            # Vite configuration
├── models/
│   ├── detection/                # Model checkpoints (best.pt weights)
│   └── registry/                 # model_registry.yaml with SHA-256 hashes
├── outputs/
│   ├── evidence/                 # Visual evidence archive (YYYY/MM/DD/{camera}/)
│   └── logs/                     # Rotating production log files
├── runs/                         # Model training evaluation artifacts
├── scripts/
│   ├── cleanup_retention.py      # Automated database and evidence retention script
│   └── testing/                  # run_integration_tests.py (39 E2E scenarios)
├── .env.example                  # Safe configuration template
├── .gitignore                    # Version control exclusions
├── PROJECT_STATUS.md             # Current system status & verification evidence
└── README.md                     # Master project documentation
```

---

## 14. Technical Documentation Directory

Complete engineering documentation is organized logically in the [`docs/`](./docs/README.md) directory:

| Section | Key Documents |
|---|---|
| **Architecture** | [System Architecture](docs/architecture/system-architecture.md) • [Processing Pipeline](docs/architecture/processing-pipeline.md) • [Data Flow](docs/architecture/data-flow.md) • [Database Architecture](docs/architecture/database.md) |
| **AI & Vision** | [Detection Model](docs/ai/detection-model.md) • [Model Registry](docs/ai/model-registry.md) • [PPE Compliance](docs/ai/ppe-compliance.md) • [Worker Tracking](docs/ai/worker-tracking.md) • [Hazards](docs/ai/fire-smoke-detection.md) • [Risk Engine](docs/ai/risk-engine.md) |
| **Operations** | [Camera Management](docs/operations/camera-management.md) • [Camera Dashboard](docs/operations/camera-dashboard.md) • [Alerts](docs/operations/alerts.md) • [Incidents](docs/operations/incident-management.md) • [Evidence](docs/operations/evidence-management.md) • [Monitoring](docs/operations/monitoring.md) |
| **Deployment** | [Installation](docs/deployment/installation.md) • [Configuration](docs/deployment/configuration.md) • [Production Deployment](docs/deployment/production-deployment.md) • [Troubleshooting](docs/deployment/troubleshooting.md) |
| **Security** | [Authentication](docs/security/authentication.md) • [Authorization & RBAC](docs/security/authorization.md) • [Security Model](docs/security/security-model.md) |
| **Testing** | [Testing Strategy](docs/testing/testing-strategy.md) • [Integration Report](docs/testing/integration-testing.md) • [Benchmarks](docs/testing/performance.md) • [Known Issues](docs/testing/known-issues.md) |
| **Data & Reports** | [Dataset Strategy](docs/datasets/dataset-strategy.md) • [Dataset Sources](docs/datasets/sources.md) • [Production Readiness](docs/reports/production-readiness.md) • [Limitations](docs/reports/known-limitations.md) |

---

## 15. Model & Model Registry

The active production model is managed through an explicit registry:

- **Checkpoint Path:** `models/detection/ppe_fire_smoke_v2/weights/best.pt`
- **Model Architecture:** YOLOv8n (nano)
- **Model Framework:** Ultralytics YOLO / PyTorch
- **Input Resolution:** $384 \times 384$ pixels
- **SHA-256 Checksum:** `490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3`
- **Model Status:** `production` in `models/registry/model_registry.yaml`

### Checksum Verification Workflow:
The `ModelLoader` (`backend/app/ai/detection/model_loader.py`) enforces strict cryptographic validation:

```
ModelLoader.load_model()
    │
    ├── 1. Reads models/registry/model_registry.yaml
    ├── 2. Identifies active model marked status: production
    ├── 3. Computes live SHA-256 digest of weights file on disk
    ├── 4. Compares computed hash against registry value
    │
    ├── Match? ──> Loads neural network into memory
    └── Mismatch? ──> Halts loading immediately with RuntimeError:
                      "MODEL CHECKSUM VERIFICATION FAILED"
```

---

## 15. Datasets — Source & Traceability

RAKSHYA VISION was trained and validated on four open datasets compiled into a unified training split of **22,453 images** and **51,195 verified annotations**:

### 1. PPE Detection & Compliance
- **Source:** Roboflow Universe
- **Official URL:** [https://universe.roboflow.com/izanagi/ppe-detection-and-compliance](https://universe.roboflow.com/izanagi/ppe-detection-and-compliance)
- **License:** CC BY 4.0
- **Usage:** Primary multi-class PPE dataset providing diverse coverage of boots, gloves, vests, helmets, and full-body worker postures.

### 2. Construction PPE
- **Source:** Roboflow Universe
- **Official URL:** [https://universe.roboflow.com/skcet-g4h72/construction-ppe-rdhzo](https://universe.roboflow.com/skcet-g4h72/construction-ppe-rdhzo)
- **License:** CC BY 4.0
- **Usage:** Supplementary dataset providing real-world construction site backgrounds, lighting angles, and hard hat variations.

### 3. Hard Hat Workers
- **Source:** Roboflow Public / Harvard Dataverse
- **Official URL:** [https://public.roboflow.com/object-detection/hard-hat-workers](https://public.roboflow.com/object-detection/hard-hat-workers)
- **License:** CC0: Public Domain
- **Usage:** Core dataset for head-to-helmet spatial association and dense worker crowd modeling.

### 4. D-Fire (Fire & Smoke)
- **Source:** GAIA Solutions / Roboflow Universe
- **Official URL:** [https://github.com/gaia-solutions-on-demand/DFireDataset](https://github.com/gaia-solutions-on-demand/DFireDataset)
- **License:** CC BY 4.0 / GPL-3.0
- **Usage:** Dedicated combustion dataset providing varied fire flame intensities and industrial smoke plume patterns.

---

## 16. Dataset Source Mapping

| Dataset Name | Type | Images | Purpose in Project | Storage Location | Verified License |
|:---|:---|:---:|:---|:---|:---|
| **PPE Detection & Compliance** | Dataset | 9,663 | Primary multi-class PPE training | `datasets/raw/ppe_detection/` | CC BY 4.0 |
| **Construction PPE** | Dataset | 1,124 | Site backgrounds & vest diversity | `datasets/raw/construction_ppe/` | CC BY 4.0 |
| **Hard Hat Workers** | Dataset | 7,035 | Worker & helmet relationship modeling | `datasets/raw/hard_hat_workers/` | CC0 (Public Domain) |
| **D-Fire Dataset** | Dataset | 4,631 | Fire & smoke hazard training | `datasets/raw/d_fire/` | CC BY 4.0 / GPL-3.0 |
| **Unified Processed Split** | Unified Split | 22,453 | Train (15,717), Val (4,490), Test (2,246) | `datasets/processed/` | Combined Under Terms |

---

## 17. External Technology Sources

Every core library and framework used in RAKSHYA VISION is grounded in an official repository:

- **Ultralytics YOLOv8:** [https://docs.ultralytics.com/](https://docs.ultralytics.com/)
- **OpenCV Computer Vision:** [https://opencv.org/](https://opencv.org/)
- **PyTorch Machine Learning:** [https://pytorch.org/](https://pytorch.org/)
- **FastAPI Framework:** [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
- **React 18:** [https://react.dev/](https://react.dev/)
- **TypeScript:** [https://www.typescriptlang.org/](https://www.typescriptlang.org/)
- **Vite:** [https://vite.dev/](https://vite.dev/)
- **SQLAlchemy:** [https://www.sqlalchemy.org/](https://www.sqlalchemy.org/)
- **SQLite:** [https://www.sqlite.org/](https://www.sqlite.org/)
- **ByteTrack Research:** [https://github.com/ifzhang/ByteTrack](https://github.com/ifzhang/ByteTrack)

---

## 18. Problem Statement Source

- **Competition:** BPUT Hackathon 2026
- **Track:** Artificial Intelligence & Computer Vision
- **Problem Statement Code:** PS06
- **Title:** Prototype AI system that detects safety gear compliance
- **Organizing Entities:** Software Technology Parks of India (STPI) & EmTek
- **Source Context:** Based on the official BPUT Hackathon 2026 problem statement guidelines supplied to participating engineering teams.

---

## 19. Source → Project Traceability

| External Source | Category | What It Provides | How RAKSHYA VISION Uses It | Repository Location |
|:---|:---|:---|:---|:---|
| **Roboflow Universe** | Dataset Source | Raw annotated bounding box datasets | Training data for canonical classes | `datasets/raw/` |
| **D-Fire (GAIA)** | Dataset Source | Fire and smoke bounding annotations | Training data for hazard detection | `datasets/raw/d_fire/` |
| **Ultralytics** | Neural Framework | YOLOv8 architecture & inference engine | Object detector backbone (`best.pt`) | `backend/app/ai/detection/` |
| **ByteTrack** | Tracking Algorithm | Kalman filter multi-object tracking | Worker identity persistence | `backend/app/ai/compliance/tracker.py` |
| **FastAPI** | Web Framework | ASGI async HTTP & WebSocket server | Real-time REST API & live alerting | `backend/app/api/` |
| **React / Vite** | Frontend Engine | Reactive Virtual DOM & ESM bundler | Human-in-the-loop SOC dashboard | `frontend/src/` |

---

## 20. Licenses & Attribution

| Resource | Origin | License | Attribution Requirement | Project Compliance |
|:---|:---|:---|:---|:---|
| **RAKSHYA VISION** | Project Team | MIT License | Standard MIT notice | Included in repository |
| **PPE Detection Dataset** | Izanagi (Roboflow) | CC BY 4.0 | Attribution required | Cited in `datasets/SOURCES.md` |
| **Construction PPE** | SKCET (Roboflow) | CC BY 4.0 | Attribution required | Cited in `datasets/SOURCES.md` |
| **Hard Hat Workers** | Roboflow / Harvard | CC0 1.0 | Public Domain | Preserved in dataset registry |
| **D-Fire Dataset** | GAIA / Pedro Vinicius | CC BY 4.0 | Attribution required | Cited in `datasets/SOURCES.md` |
| **Ultralytics YOLO** | Ultralytics Inc. | AGPL-3.0 / Enterprise | License compliance required | Maintained under open-source evaluation terms |
| **OpenCV** | OpenCV Team | Apache 2.0 | Apache notice | Maintained |
| **FastAPI** | Sebastián Ramírez | MIT License | Standard notice | Maintained |
| **React** | Meta Platforms, Inc. | MIT License | Standard notice | Maintained |

---

## 21. Performance Benchmarks

Performance was benchmarked across repeated end-to-end cycles (`outputs/integration/performance_report.json`) on the development host:

### Benchmark Environment:
- **Processor:** Intel Core i5-13420H (8 Cores / 12 Threads)
- **Host Memory:** 15.59 GB RAM
- **Execution Mode:** CPU-Only PyTorch (`device: cpu`)
- **Neural Model:** YOLOv8n ($384 \times 384$ input)

### Measured Results:
| Benchmark Dimension | Measured Result | Latency Budget | Status |
|:---|:---:|:---:|:---:|
| **Mean Pipeline Latency (End-to-End)** | **41.55 ms** | $< 100.0\text{ ms}$ | **PASS** |
| **Median Pipeline Latency** | **40.34 ms** | $< 100.0\text{ ms}$ | **PASS** |
| **Effective Frame Rate (CPU)** | **24.1 FPS** | $\ge 15.0\text{ FPS}$ | **PASS** |
| **Subsystem: YOLOv8n Detection** | 41.47 ms | $< 80.0\text{ ms}$ | **PASS** |
| **Subsystem: ByteTrack Tracking** | 0.01 ms | $< 5.0\text{ ms}$ | **PASS** |
| **Subsystem: Anatomical Association** | $< 0.01\text{ ms}$ | $< 5.0\text{ ms}$ | **PASS** |
| **Process Resident Memory (RSS)** | 423 MB $\rightarrow$ 432 MB | $< 1000.0\text{ MB}$ | **PASS** (Zero Leaks) |

> [!NOTE]
> Development host benchmarks reflect single-camera CPU performance. Multi-camera deployments at scale require edge accelerators (e.g. NVIDIA Jetson, Intel OpenVINO, or dedicated GPU instances).

---

## 22. Testing & Verification

The repository contains an automated testing suite covering all architectural layers:

```
pytest backend/tests -v
===================== 154 passed, 3 warnings in 41.33s =====================
```

### Coverage by Subsystem:
1. **Model Registry & SHA-256 Checksum (`test_model_registry_phase10.py`):** 7/7 tests passed.
2. **Production Config & Secrets (`test_production_config_phase10.py`):** 9/9 tests passed.
3. **Database WAL & Data Retention (`test_database_phase10.py`):** 6/6 tests passed.
4. **Multi-Camera Manager (`test_camera_manager_phase10.py`):** 7/7 tests passed.
5. **Camera API & Control (`test_camera_api_phase10.py`):** 7/7 tests passed.
6. **Authentication & RBAC (`test_auth_rbac_phase10.py`):** 8/8 tests passed.
7. **External Alert Providers (`test_alert_providers_phase10.py`):** 6/6 tests passed.
8. **Incident Evidence Archival (`test_evidence_phase10.py`):** 8/8 tests passed.
9. **Observability & Metrics (`test_observability_phase10.py`):** 8/8 tests passed.
10. **Object Detection Pipeline (`test_detection.py`):** 19/19 tests passed.
11. **Worker Compliance & Association (`test_compliance.py`):** 14/14 tests passed.
12. **Fire & Smoke Hazard Tracking (`test_hazards.py`):** 16/16 tests passed.
13. **Risk & Smart Alerts (`test_risk_alerts.py`):** 19/19 tests passed.
14. **WebSocket Streaming (`test_websocket.py`):** 3/3 tests passed.
15. **Application Health & Routing (`test_main.py`):** 4/4 tests passed.
16. **Full Integration Suite (`test_integration_phase9.py`):** 6 tests passed (covering 39 scenarios).

### Integration Test Runner:
```
python scripts/testing/run_integration_tests.py
Total Tests: 39 | Passed: 39 | Failed: 0 (100% Pass Rate)
```

---

## 23. Production Status Matrix

| Subsystem / Capability | Operational Status | Evidence in Codebase |
|:---|:---:|:---|
| **YOLOv8 Object Detection** | **Implemented & Verified** | `backend/app/ai/detection/detector.py` |
| **Model Registry & SHA-256 Checksum** | **Implemented & Verified** | `models/registry/model_registry.yaml`, `model_loader.py` |
| **ByteTrack Worker Tracking** | **Implemented & Verified** | `backend/app/ai/compliance/tracker.py` |
| **Anatomical PPE Association** | **Implemented & Verified** | `backend/app/ai/compliance/association.py` |
| **Temporal Compliance State Machine** | **Implemented & Verified** | `backend/app/ai/compliance/temporal.py` |
| **Fire & Smoke Hazard Tracking** | **Implemented & Verified** | `backend/app/ai/hazards/tracker.py` |
| **Explainable Risk Engine (0-100)** | **Implemented & Verified** | `backend/app/services/risk_engine.py` |
| **Smart Alert Engine & Deduplication** | **Implemented & Verified** | `backend/app/services/alert_engine.py` |
| **Database WAL Mode & Foreign Keys** | **Implemented & Verified** | `backend/app/database/session.py` |
| **Multi-Camera Manager Pool** | **Implemented & Verified** | `backend/app/camera/manager.py`, `worker.py` |
| **Camera Control & Snapshot API** | **Implemented & Verified** | `backend/app/api/cameras.py` |
| **Authentication & RBAC (PBKDF2/JWT)** | **Implemented & Verified** | `backend/app/security/auth.py`, `api/auth.py` |
| **External Alert Providers (Webhook/Email)** | **Implemented & Verified** | `backend/app/services/alert_providers/` |
| **Incident Evidence Archival & Checksum** | **Implemented & Verified** | `backend/app/services/evidence_manager.py` |
| **Observability (/health, /metrics)** | **Implemented & Verified** | `backend/app/api/monitoring.py`, `services/metrics.py` |
| **React 18 SOC Dashboard** | **Implemented & Verified** | `frontend/src/` (`npm run build` succeeds in 3.5s) |
| **Physical Industrial CCTV Pilot** | **Not Tested** | Hardware unavailable in test environment |
| **Long-Duration Stress Test (> 72h)** | **Not Tested** | Awaiting pilot edge deployment |
| **Edge Hardware Packaging (Docker/K8s)** | **Planned** | Container manifests scheduled for Phase 11 |

---

## 24. Real-World Deployment Architecture

```mermaid
flowchart TD
    subgraph FIELD["Industrial Workplace / Facility"]
        C1["Camera 01: Entrance Gate<br>(RTSP / H.264)"]
        C2["Camera 02: Workshop Floor<br>(RTSP / H.264)"]
        C3["Camera 03: Loading Bay<br>(RTSP / H.264)"]
        C4["Camera 04: Hazardous Storage<br>(RTSP / H.264)"]
    end

    subgraph EDGE["Edge Compute Server / On-Premise Gateway"]
        MCM["Multi-Camera Stream Manager"]
        YOLO["YOLOv8n Multi-Task AI Engine (384x384)"]
        TRACK["ByteTrack & Anatomical Compliance Engine"]
        RISK["Risk Scoring & Incident Lifecycle Engine"]
        DB[("SQLite WAL Database<br>rakshya_vision.db")]
        EVID["Evidence Archival<br>(outputs/evidence/ + SHA-256)"]
        FASTAPI["FastAPI App Server<br>(Port 8000)"]
        PROM["Prometheus Metrics<br>(/metrics Endpoint)"]

        MCM --> YOLO --> TRACK --> RISK
        RISK --> DB
        RISK --> EVID
        RISK --> FASTAPI
        FASTAPI --> PROM
    end

    subgraph SOC["Safety Operations Center (SOC)"]
        DASH["React 18 / Vite Web Dashboard<br>(Live Annotated Streams, Alert HUD, Risk Gauges)"]
    end

    subgraph EXTERNAL["Enterprise Integrations & Dispatch"]
        WH["HTTP Webhook Endpoint<br>(HMAC-SHA256 Signed)"]
        MAIL["Safety Management (SMTP Email)"]
        SLACK["Incident Channel (Slack App)"]
    end

    C1 & C2 & C3 & C4 -->|RTSP Network Feeds| MCM
    FASTAPI -->|WebSocket /ws/alerts & REST /api| DASH
    FASTAPI -->|Signed Webhook| WH
    FASTAPI -->|STARTTLS Email| MAIL
    FASTAPI -->|Incoming Webhook| SLACK
```

> [!NOTE]
> Physical industrial CCTV deployment is marked as **Not Tested** because development was conducted using recorded test video, local webcams, synthetic streams, and mobile network streams.

---

## 25. Configuration Guide

System behavior is governed by centralized, typed YAML configurations:

### Configuration Files:
- **`configs/production.yaml`:** Central production configuration (server settings, database timeouts, evidence retention windows, logging parameters, security flags).
- **`configs/cameras.yaml`:** Camera configurations (camera ID, name, RTSP/USB source, target FPS, assigned zone).
- **`configs/risk_policy.yaml`:** Risk scoring weights, persistence penalties, and zone risk multipliers.
- **`configs/alert_policy.yaml`:** Deduplication cooldown windows and escalation persistence thresholds.
- **`models/registry/model_registry.yaml`:** Active model catalog and immutable SHA-256 hashes.

### Secret Management (`.env`):
Secrets and API credentials are kept strictly isolated from version control. A sanitized template is provided in `.env.example`:

```bash
# Application Environment
APP_ENV=production
SECRET_KEY=generate_with_openssl_rand_hex_32
JWT_SECRET_KEY=generate_with_openssl_rand_hex_32

# Security & RBAC
AUTH_ENABLED=true
JWT_EXPIRATION_MINUTES=480

# External Alert Providers (Leave blank if unconfigured)
ALERT_WEBHOOK_ENABLED=false
WEBHOOK_URL=
WEBHOOK_SECRET=

ALERT_EMAIL_ENABLED=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
EMAIL_FROM_ADDRESS=
EMAIL_RECIPIENTS=
```

---

## 26. Installation & Quick Start

### Prerequisites
- **Operating System:** Windows 10/11, Ubuntu 22.04+, or macOS
- **Python:** Python 3.10 to 3.13 (64-bit)
- **Node.js:** Node.js v18+ and npm

---

### Step 1: Clone Repository
```bash
git clone https://github.com/SMRU08/RAKSHYA-VISION.git
cd RAKSHYA-VISION
```

---

### Step 2: Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate Python virtual environment
python -m venv .venv

# Windows activation:
.venv\Scripts\Activate.ps1
# Linux/macOS activation:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 3: Configure Environment
```bash
# Return to root and create .env file from template
cd ..
cp .env.example .env
```

---

### Step 4: Run Backend Server
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- **API Root:** [http://localhost:8000/](http://localhost:8000/)
- **Liveness Probe:** [http://localhost:8000/health/live](http://localhost:8000/health/live)
- **Readiness Probe:** [http://localhost:8000/health/ready](http://localhost:8000/health/ready)
- **Prometheus Metrics:** [http://localhost:8000/metrics](http://localhost:8000/metrics)
- **OpenAPI Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Step 5: Frontend Setup & Startup
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
- **Dashboard Interface:** [http://localhost:5173](http://localhost:5173)

---

### Step 6: Verify System Health
Run automated tests to confirm system integrity:
```bash
# Backend pytest suite (154 tests)
pytest backend/tests -v

# Phase 9 integration test runner (39 scenarios)
python scripts/testing/run_integration_tests.py

# Frontend production build
cd frontend
npm run build
```

---

## 27. API & WebSocket Reference

### System Health & Monitoring
- `GET /health/live` — Lightweight container liveness probe (`HTTP 200`).
- `GET /health/ready` — Deep readiness probe validating DB, AI model, and storage (`HTTP 200` or `HTTP 503`).
- `GET /health` — Legacy health endpoint for backward compatibility.
- `GET /health/database` — SQLite WAL mode, PRAGMA, and table connection health.
- `GET /metrics` — Prometheus 0.0.4 metrics exposition.
- `GET /api/monitoring/metrics` — JSON operational metrics summary.
- `GET /api/monitoring/health/deep` — Detailed diagnostics report.

### Camera Management
- `GET /api/cameras` — Real-time operational statuses and FPS metrics.
- `GET /api/cameras/{camera_id}` — Single camera status.
- `POST /api/cameras/{camera_id}/start` — Starts capture worker thread.
- `POST /api/cameras/{camera_id}/stop` — Gracefully stops capture worker thread.
- `GET /api/cameras/{camera_id}/snapshot` — Streams live JPEG frame inspection.

### Safety Incidents & Alerts
- `GET /api/risk/summary` — Active incident, alert, and hazard counts.
- `GET /api/alerts` — Lists alerts with severity and status filters.
- `GET /api/alerts/{alert_id}` — Alert detail and audit timeline.
- `POST /api/alerts/{alert_id}/acknowledge` — Operator acknowledgement.
- `POST /api/alerts/{alert_id}/resolve` — Operator incident resolution.
- `POST /api/alerts/{alert_id}/dismiss` — Operator alert dismissal.
- `GET /api/incidents` — Lists safety incidents.
- `GET /api/incidents/{incident_id}` — Incident details.
- `GET /api/alerts/providers/status` — Status of external alert notification channels.

### Evidence Archival
- `GET /api/incidents/{incident_id}/evidence` — Lists archived evidence for an incident.
- `GET /api/evidence/{evidence_id}` — Evidence metadata and live SHA-256 integrity check.
- `GET /api/evidence/{evidence_id}/download` — Secure image download with path traversal defense.
- `GET /api/evidence/storage/status` — Evidence disk usage and quota limits.

### Authentication & Audit
- `POST /api/auth/login` — Issues JWT bearer token.
- `GET /api/auth/me` — Current authenticated user profile.
- `GET /api/auth/users` — Admin user management.
- `GET /api/auth/audit-logs` — Immutable audit log of administrative actions.

### Real-Time WebSockets
- `WS /ws/alerts` — Live push stream for `AlertCreated`, `AlertUpdated`, `AlertEscalated`, and `IncidentCreated` events. Supports bi-directional ping/pong heartbeats.

---

## 28. Security & Privacy

1. **Authentication & RBAC:** Passwords hashed using PBKDF2-HMAC-SHA256 with 600,000 iterations. JWT tokens expire after 8 hours. Roles include `ADMIN`, `OPERATOR`, and `VIEWER`.
2. **Credential Redaction:** Camera RTSP passwords and database secrets are masked in logs and API outputs (`mask_camera_source`).
3. **Path Traversal Defenses:** File endpoints canonicalize relative paths against base directories. Requests attempting directory traversal (e.g. `../../`) raise `HTTP 403 Forbidden`.
4. **Tamper-Evident Storage:** Visual evidence files are cryptographically hashed using SHA-256 upon write. Verification re-calculates hashes to expose tampering.
5. **Privacy by Design:** Worker tracking uses anonymous integer IDs (`Track #101`). No facial recognition, biometric identification, or PII is recorded.
6. **Data Retention & Pruning:** Automated maintenance (`scripts/cleanup_retention.py`) purges expired records and unlinks evidence files according to retention policies.

---

## 29. Known Limitations

- **Small & Distant Combustion:** Fire or smoke signatures smaller than $15 \times 15$ pixels in wide-angle views may remain below the detection confidence threshold.
- **Optical Smoke Confusion:** Visual smoke detection may be prone to false alerts in areas with heavy steam or dense industrial dust clouds.
- **Extreme Footwear Occlusion:** Safety footwear detection can be challenged when workers stand behind pallets or materials.
- **CPU Throughput Bounds:** CPU inference runs at ~24 FPS for single streams. Multi-camera concurrent inference requires edge hardware acceleration.
- **Physical CCTV Pilot Status:** Physical industrial CCTV hardware has not yet been piloted in a live factory environment.

---

## 30. Roadmap

### Current Capabilities

RAKSHYA VISION currently provides:

- **AI-Based PPE Detection:** Real-time multi-task object detection across 7 canonical classes (`person`, `helmet`, `safety_vest`, `gloves`, `safety_footwear`, `fire`, `smoke`) using a single-stage YOLOv8 architecture.
- **Worker Tracking:** Multi-person identity tracking using ByteTrack with Kalman filtering and Hungarian association across continuous frames.
- **PPE Compliance Analysis:** Deterministic anatomical bounding box association mapping detected protective equipment to corresponding worker body zones (head, torso, hands, feet) without relying on noisy absence classes.
- **Fire & Smoke Hazard Monitoring:** Dual-channel spatial detection for open flame and atmospheric smoke emissions.
- **Temporal Event Confirmation:** State machine stabilization requiring consecutive frame confirmations ($N_{\text{confirm}} = 3$ for PPE violations, $N_{\text{confirm}} = 5$ for environmental hazards) to prevent transient false alarms.
- **Explainable Risk Assessment:** Transparent $0–100$ scoring calculated from severity weights, spatial proximity, and worker exposure duration.
- **Incident Lifecycle Management:** Automatic transition governance for safety events (`NEW` $\to$ `ACKNOWLEDGED` $\to$ `RESOLVED`) with complete audit trails.
- **Real-Time Operator Dashboard:** Web-based control room interface delivering live annotated video overlays, dynamic telemetry, and incident queues over WebSockets.
- **Multi-Camera Management:** Dynamic multi-stream orchestration supporting simultaneous IP/RTSP streams, USB webcams, and recorded video files with independent thread workers.
- **Authenticated Access & RBAC:** Role-based access control (`admin`, `operator`, `auditor`) with PBKDF2-HMAC-SHA256 password hashing and JWT token authentication.
- **Incident Evidence Archival:** Automated capture of JPEG frame snapshots and structured JSON telemetry tagged with cryptographic SHA-256 checksums for auditability.
- **Configurable External Alert Providers:** Dispatch engine supporting outgoing webhooks, SMTP email alerts, and Slack notifications with rate limiting and retry handling.
- **System Health & Operational Monitoring:** Prometheus `/metrics` exposition alongside Kubernetes-compatible `/health/live` and `/health/ready` probe endpoints.

### Near-Term Improvements

The next engineering priorities for operational readiness include:

- **GPU and Edge Acceleration:** Benchmarking and runtime optimization for NVIDIA Jetson and discrete CUDA environments to maximize multi-stream frame rates.
- **Small-Object & Distant PPE Optimization:** Further tuning of detector anchors and input resolution to enhance glove and footwear detection at extended camera distances.
- **Extended Real-World Validation:** Validation against diverse industrial RTSP camera hardware, varied focal lengths, and complex lighting environments.
- **Longer-Duration Reliability Testing:** Extended continuous multi-stream soak testing to evaluate memory stability and SQLite WAL performance under sustained load.
- **Broader Alert Provider Validation:** End-to-end delivery testing across enterprise incident response systems (Microsoft Teams, PagerDuty, enterprise SMS gateways).
- **Deployment Packaging:** Production containerization manifests including multi-stage Dockerfiles and Docker Compose profiles for simplified deployment.
- **Operational Hardening:** Dynamic camera reconnect handling with automated exponential backoff for intermittent network drops.

### Future Development

Potential future work includes:

- **Hardware-Specific Engine Optimization:** Exporting trained weights to TensorRT engines and ONNX Runtime with INT8 quantization for ultra-low-power edge nodes.
- **Large-Scale Multi-Camera Orchestration:** Distributed worker pipeline using Celery/Redis or Kafka for centralized monitoring across dozens of concurrent feeds.
- **Expanded PPE Classification:** Support for additional specialized safety equipment such as face shields, fall arrest harnesses, and ear protection.
- **Domain-Specific Dataset Expansion:** Gathering and annotating low-light, adverse weather, and heavy dust workplace imagery to boost domain generalization.
- **Advanced Predictive Safety Analytics:** Heatmap analytics for spatial violation congestion and worker dwell time trends across facility zones.
- **Enterprise System Integrations:** Bi-directional webhooks with existing Environmental Health & Safety (EHS) and industrial ERP platforms.

---

## 31. Authors & Acknowledgments

- **Lead Engineer & Maintainer:** Smruti Ranjan Nayak ([@SMRU08](https://github.com/SMRU08))
- **Project:** RAKSHYA VISION
- **Competition:** BPUT Hackathon 2026
- **Problem Statement:** PS06 — AI Vision-Based Safety Gear Compliance
- **Organized By:** Software Technology Parks of India (STPI) & EmTek
- **License:** MIT License — see [LICENSE](LICENSE) for details.
