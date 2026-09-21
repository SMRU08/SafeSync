# Phase 6 Technical Report — Fire & Smoke Hazard Analysis

**Project:** RAKSHYA VISION — AI Vision-Based Safety Monitoring  
**Phase:** 6 (Fire & Smoke Hazard Analysis)  
**Status:** COMPLETED & VERIFIED  
**Date:** September 2026  

---

## 1. Executive Summary & Architecture

Phase 6 implements a dedicated, robust, and non-destructive **Fire and Smoke Hazard Analysis Layer** built directly on top of the validated YOLOv8n V2 detection and video analytics pipelines.

### Key Operational Characteristics:
- **Strict Decoupling from PPE Compliance:** Environmental hazards (`fire`, `smoke`) are processed via an isolated pipeline. A fire or smoke detection **never** generates a PPE violation or alters a worker's personal compliance state.
- **Persistent Multi-Object Hazard Tracking:** Detections are grouped and assigned anonymous tracking identifiers (`HAZARD-0001`, `HAZARD-0002`). Fire and smoke are tracked as separate physical event streams.
- **Temporal Evidence Accumulation:** Single-frame flicker triggers `SUSPECTED`, not `CONFIRMED`. Persistent hazards require $N_{\text{confirm}} = 5$ frames to confirm and tolerate up to $N_{\text{gap}} = 5$ missing frames before clearing.
- **Zone and Camera Intelligence:** Observations are associated with cameras and geographical or logical facility zones (`configs/cameras.yaml`) with optional polygon ROI containment.
- **Strict Scope Boundaries:** No risk severity scoring (`CRITICAL`, `HIGH`, etc.), no automated notifications (SMS, email, WhatsApp), and no emergency alert dispatches were implemented; these are deferred to Phase 7.

```
Camera / Video Stream
         │
         ▼
[1] YOLOv8n Object Detector (V2 Checkpoint: 7 Canonical Classes)
         │
         ├─── Worker & PPE Classes (0..4) ──► Phase 5 Compliance Pipeline
         │
         └─── Environmental Hazard Classes (5: fire, 6: smoke)
                  │
                  ▼
         [2] Confidence Filtering (fire_conf: 0.25, smoke_conf: 0.25)
                  │
                  ▼
         [3] Camera & Zone Resolution (Point-in-Polygon ROI Check)
                  │
                  ▼
         [4] Spatial Hazard Tracker (IoU + Centroid Distance Matching)
                  │
                  ▼
         [5] Temporal State Machine (NO_HAZARD -> SUSPECTED -> CONFIRMED -> CLEARED)
                  │
                  ▼
         [6] Database Persistence (HazardEvent, HazardObservation)
                  │
                  ▼
         [7] Visualizer HUD & FastAPI REST Endpoints (/api/hazards)
```

---

## 2. Fire & Smoke Detection Metrics (Model Limitations)

The system utilizes the verified Phase 3.1 checkpoint:
- **Checkpoint Path:** `models/detection/ppe_fire_smoke_v2/weights/best.pt`
- **File Checksum (SHA-256):** `490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3`
- **Measured Test Split Evaluation (Held-out 2,246 test images, conf=0.25):**
  - **`fire` (Class 5):** Precision: **41.99%** | Recall: **30.62%** | mAP@50: **20.15%**
  - **`smoke` (Class 6):** Precision: **57.74%** | Recall: **30.48%** | mAP@50: **22.62%**

> [!IMPORTANT]
> The computer vision model has an average recall of ~30.5% on distant or diffuse hazards. The system **does NOT guarantee 100% detection of all fires or smoke** and is designed as an assistive software layer to supplement certified physical life-safety systems.

---

## 3. Temporal Validation & State Machine

### 3.1 State Transitions
```
   [ Detection Arrives ]
             │
             ▼
        SUSPECTED  ◄─────────────┐ (Re-detected)
             │                   │
  (>= 5 frames & ratio >= 0.60)  │
             │                   │
             ▼                   │
         CONFIRMED               │
             │                   │
    (>= 10 missed frames)        │
             │                   │
             ▼                   │
          CLEARED ───────────────┘
             │
       (Unobserved)
             │
             ▼
         NO_HAZARD
```

### 3.2 Transition Policy & Thresholds
Defined in `configs/hazard.yaml`:
* `confirmation_frames = 5`: Detections must accumulate over at least 5 frames to graduate from `SUSPECTED` to `CONFIRMED`.
* `minimum_observation_ratio = 0.60`: The persistence ratio ($\frac{\text{detected frames}}{\text{observed frames}}$) must be at least 60%.
* `max_gap_frames = 5`: Brief false detections that disappear for 5 frames decay from `SUSPECTED` directly to `CLEARED` $\rightarrow$ `NO_HAZARD`.
* `clear_frames = 10`: Confirmed hazards tolerate brief smoke dissipation or flame flicker for up to 9 frames; at 10 consecutive missed frames, the state transitions to `CLEARED`.

### 3.3 Multi-Modal Scene Relationships
The engine categorizes scene hazard conditions into:
* `FIRE_ONLY`: Active fire tracks detected, no active smoke.
* `SMOKE_ONLY`: Active smoke tracks detected, no active fire.
* `FIRE_AND_SMOKE`: Concurrent active fire and smoke tracks.
* `NO_HAZARD`: No active fire or smoke events.

---

## 4. Spatial Hazard Tracking

Implemented in `backend/app/ai/hazards/tracker.py`:
- **Matching Distance:** Combines bounding-box IoU ($\ge 0.20$) and normalized centroid Euclidean distance ($\le 0.25 \times \text{frame diagonal}$) using the Hungarian algorithm (`scipy.optimize.linear_sum_assignment`).
- **Independent Streams:** Fire and smoke detections are segregated prior to association, preventing fire tracks from absorbing smoke detections.
- **Anonymous Event Naming:** Tracks are assigned IDs sequentially: `HAZARD-0001`, `HAZARD-0002`.

---

## 5. Zone & Camera Metadata Handling

Configured in `configs/cameras.yaml` and resolved in `backend/app/ai/hazards/zones.py`:
- Maps camera IDs (`camera_01`, `camera_02`, `camera_03`, `camera_04`) to facility zones (`production_floor`, `storage_area`, `electrical_room`, `loading_dock`).
- Supports optional polygon ROI checks (Point-in-Polygon ray-casting). For example, in `camera_03`, hazards with centers outside the transformer enclosure polygon $[0.1, 0.1] \dots [0.9, 0.9]$ fall back to `UNKNOWN`.
- Unregistered cameras default to `UNKNOWN`.

---

## 6. Database Persistence Schema

Implemented in `backend/app/models/hazard.py`:
* **`HazardEvent`:** Stores aggregated event summaries:
  `event_id`, `hazard_type`, `state`, `camera_id`, `zone_id`, `first_seen`, `last_seen`, `duration_seconds`, `detection_count`, `average_confidence`, `max_confidence`.
* **`HazardObservation`:** Stores frame-by-frame bounding boxes and confidence records linked to the parent `HazardEvent`.

---

## 7. FastAPI Endpoints

Exposed via `backend/app/api/hazards.py`:
* `GET /api/hazards/config`: Returns active thresholds, tracking parameters, and zone mappings.
* `POST /api/hazards/analyze`: Uploads a frame, executes YOLO inference, spatial tracking, temporal state evaluation, database persistence, and returns `HazardAnalysisResponse`.
* `GET /api/hazards`: Lists active or historical hazard events with optional filtering (`state`, `hazard_type`, `limit`).
* `GET /api/hazards/{event_id}`: Retrieves comprehensive details and observation histories for an event.

---

## 8. Empirical Verification Results

### 8.1 Controlled Scenario Tests (12/12 Passed)
Executed via `scripts/hazards/test_hazard_scenarios.py` with results stored in `outputs/hazards/scenario_test_results.json`:

| Scenario | Test Case Description | Evaluation Result | Status |
| :--- | :--- | :--- | :--- |
| **S1** | No fire / no smoke | `NO_HAZARD` scene state and relationship | **PASSED** |
| **S2** | Single-frame fire detection | Transitioned to `SUSPECTED` (not confirmed) | **PASSED** |
| **S3** | Persistent fire (5 frames) | Transitioned to `CONFIRMED` | **PASSED** |
| **S4** | Single-frame smoke detection | Evaluated as `SUSPECTED` | **PASSED** |
| **S5** | Persistent smoke (5 frames) | Transitioned to `CONFIRMED` | **PASSED** |
| **S6** | Fire disappearing temporarily | Retained as `CONFIRMED` across 3 missed frames | **PASSED** |
| **S7** | Smoke disappearing temporarily | Retained as `CONFIRMED` across 4 missed frames | **PASSED** |
| **S8** | Fire + smoke together | 2 independent tracks, `FIRE_AND_SMOKE` | **PASSED** |
| **S9** | False / brief detection decay | Transitioned `SUSPECTED` $\rightarrow$ `CLEARED` $\rightarrow$ `NO_HAZARD` | **PASSED** |
| **S10** | Multiple hazard locations | Distinct IDs assigned: `HAZARD-0001`, `HAZARD-0002` | **PASSED** |
| **S11** | Multiple cameras | camera_01 $\rightarrow$ `production_floor`, camera_02 $\rightarrow$ `storage_area` | **PASSED** |
| **S12** | Unknown zone | Out-of-bounds coordinate or unmapped cam $\rightarrow$ `UNKNOWN` | **PASSED** |

### 8.2 Full Automated Test Suite (53/53 Passed)
Executed via `pytest backend/tests -v`:
- `test_hazards.py`: **16 passed** (spatial tracker, temporal transitions, zone resolution, PPE separation, API endpoints).
- `test_compliance.py`: **14 passed** (Phase 5 tracking and compliance tests intact).
- `test_detection.py`: **19 passed** (Phase 4 detection tests intact).
- `test_main.py`: **4 passed** (system endpoints intact).
- **Total:** **53 passed in 9.26s (100% passing)**.

### 8.3 Video Processing & Performance Benchmark
Executed on multi-scene test video `datasets/test_hazard_video.mp4` via `scripts/hazards/run_hazard_video.py` and exported to `outputs/hazards/hazard_benchmark.json`:
- **Input Resolution:** 640x480 (75 frames)
- **Processing Throughput:** **8.78 FPS** on CPU
- **Mean Total Latency:** **111.07 ms**
  - YOLO Model Inference: **107.30 ms**
  - Spatial Hazard Tracking & State Machine: **0.30 ms**
  - HUD Drawing & Video Encoding: **3.47 ms**
- **Added Phase 6 Overhead:** Only **~0.30 ms** per frame.
- **Detected Events:**
  - Fire Events: 3
  - Smoke Events: 3
  - Confirmed Events: 6
  - Mean Confidence: 0.4978
- **Generated Outputs:**
  - Video: `outputs/hazards/videos/test_hazard_video_hazard.mp4`
  - Benchmark Report: `outputs/hazards/hazard_benchmark.json`

---

## 9. Known Limitations

1. **Model Recall (~30.5%):** The current YOLO model may miss small or low-contrast fire/smoke plumes in early combustion stages.
2. **Dense Dust / Steam:** As detailed in `docs/phase6_false_positive_analysis.md`, continuous boiler steam or exhaust can trigger false alarms without polygon exclusion masks.
3. **Phase 7 Readiness:** State transitions from this phase (`CONFIRMED`, `FIRE_AND_SMOKE`, duration metrics) are cleanly positioned to feed Phase 7's Risk Analysis and Notification Dispatch engine.
