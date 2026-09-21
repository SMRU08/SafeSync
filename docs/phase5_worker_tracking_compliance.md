# Phase 5 Technical Report — Worker Tracking, Spatial PPE Association & Temporal Compliance

**Project:** RAKSHYA VISION — AI Vision-Based Safety Monitoring  
**Phase:** 5 (Worker Tracking + PPE Association + Compliance)  
**Status:** COMPLETED & VERIFIED  
**Date:** September 2026  

---

## 1. Executive Summary & Objective

In Phase 5, the RAKSHYA VISION pipeline was evolved from raw bounding-box object detections into an actionable, person-centric safety compliance system. Raw frame detections (`person`, `helmet`, `safety_vest`, `gloves`, `safety_footwear`, `fire`, `smoke`) are now tracked as persistent anonymous individuals across frames, associated with their respective PPE items via spatial relative geometry and bipartite matching, evaluated through a temporal evidence state machine, and rendered via an informative real-time checklist HUD.

### Strict Scope Compliance:
* **Anonymous Tracking Only:** No facial recognition or biometric identification is performed. Workers are identified solely by anonymous IDs (`Worker #1`, `Worker #2`, etc.).
* **Fire/Smoke Clean Pass-Through:** Environmental hazards (`fire`, `smoke`) are passed through directly as independent scene hazard signals and are never treated as worker PPE violations.
* **No Single-Frame False Violations:** Missed detections are subject to configurable temporal tolerance (`missing_detection_tolerance = 5`), preventing transient flicker or occlusions from causing spurious alarms.
* **Occlusion & Boundary Handling:** Occluded body zones or truncated boxes near camera borders transition to `UNKNOWN` state rather than penalizing workers with false `ABSENT` violations.

---

## 2. System Architecture

```
Camera / Video Stream
         │
         ▼
[1] YOLO Detection Engine (V2 Model: 7 Canonical Classes)
         │
         ├─── Environmental Hazards (Fire, Smoke) ────► Passed through cleanly
         │
         ├─── Person Detections [x1, y1, x2, y2, score]
         │        │
         │        ▼
         │   [2] ByteTrack Multi-Object Tracker (Kalman Filter + 2-Stage Matching)
         │        │
         │        ▼
         │   Persistent Worker Tracks (Track IDs: 1, 2, ...)
         │        │
         └─── PPE Detections (Helmet, Vest, Gloves, Footwear)
                  │
                  ▼
         [3] Spatial PPE Association Engine (Anatomy-Aware ROIs + Bipartite Hungarian)
                  │
                  ▼
         [4] Temporal Compliance State Machine (3-frame Confirm / 5-frame Tol / UNKNOWN)
                  │
                  ▼
         [5] Compliance Checklist HUD Visualizer + Metrics & API
```

---

## 3. Detailed Component Architecture

### 3.1 Multi-Object Worker Tracking (ByteTrack)
* **Implementation:** `backend/app/ai/compliance/tracker.py`
* **Algorithm:** ByteTrack with 8-dimensional Kalman Filter state vector:
  $$\mathbf{x} = [x_c, y_c, s, r, \dot{x}_c, \dot{y}_c, \dot{s}, \dot{r}]^T$$
  where $(x_c, y_c)$ is the bounding box center, $s = w \cdot h$ is the scale/area, and $r = w / h$ is the aspect ratio.
* **Two-Stage Association Strategy:**
  1. *First Stage:* Associates high-confidence detections ($\text{score} \ge 0.25$) with existing active/lost tracks using IoU distance and the Hungarian algorithm (`scipy.optimize.linear_sum_assignment`).
  2. *Second Stage:* Associates remaining unmatched active tracks with low-confidence detections ($0.10 \le \text{score} < 0.25$), recovering workers undergoing momentary motion blur or partial occlusion.
* **Lifecycle Management:** Tracks transition through `New -> Tracked -> Lost -> Removed`. Lost tracks are retained in memory for `track_buffer = 30` frames before eviction.
* **Tracking Stability Metrics:** Automatically tracks `total_unique_tracks`, `id_switches`, `lost_count`, `recovered_count`, and `track_durations`.

### 3.2 Anatomy-Aware Spatial PPE Association
* **Implementation:** `backend/app/ai/compliance/association.py`
* **Relative Body Zones:** Standard human anatomical proportions are mapped to worker bounding boxes:
  | PPE Item | Relative Height Interval $[y_{\min}, y_{\max}]$ | Lateral Margin | Containment Threshold |
  | :--- | :--- | :--- | :--- |
  | **Helmet** | Head region: $[-0.05, 0.30] \times H$ | $\pm 0.25 \times W$ | $\ge 20\%$ |
  | **Safety Vest** | Torso region: $[0.15, 0.70] \times H$ | $\pm 0.20 \times W$ | $\ge 30\%$ |
  | **Gloves** | Lower arm / hand: $[0.35, 0.90] \times H$ | $\pm 0.35 \times W$ | $\ge 15\%$ |
  | **Safety Footwear** | Lower leg / feet: $[0.70, 1.05] \times H$ | $\pm 0.25 \times W$ | $\ge 15\%$ |
* **Bipartite Matching:** To prevent duplicate PPE assignment (e.g. one helmet assigned to two adjacent workers), cost matrices based on spatial Euclidean center distance and vertical alignment are resolved using Hungarian matching. Each PPE detection is assigned to at most one worker.
* **Unassociated PPE:** PPE items detected outside any worker's anatomical ROI are collected and reported separately as free-floating items (e.g., equipment placed on benches).

### 3.3 Temporal Compliance State Machine
* **Implementation:** `backend/app/ai/compliance/temporal.py`
* **State Taxonomy:**
  - `PRESENT` (Confirmed active protection)
  - `ABSENT` (Confirmed missing protection / violation)
  - `UNKNOWN` (Uncertain due to occlusion, image boundary truncation, or insufficient history)
* **Transition Logic:**
  - Confirmation requires $N_{\text{confirm}} = 3$ consecutive or accumulated detections.
  - Absence requires $N_{\text{tol}} = 5$ consecutive frames of non-detection.
  - If a worker's head is clipped by the top frame boundary ($y_1 \le 10\text{px}$) or occluded by another worker (overlap $> 25\%$), helmet status defaults to `UNKNOWN` rather than reporting a false `ABSENT`.
* **Overall Worker Status:**
  - `NON_COMPLIANT`: If any required PPE item (e.g., helmet or vest) is confirmed `ABSENT`.
  - `COMPLIANT`: If all required PPE items are confirmed `PRESENT`.
  - `UNKNOWN`: If any required PPE item is in an `UNKNOWN` state and no item is confirmed `ABSENT`.

### 3.4 Checklist HUD Visualizer
* **Implementation:** `backend/app/ai/compliance/visualizer.py`
* **Display Elements:**
  - Worker bounding box color-coded by compliance:
    - **Green (`#00FF7F`):** `COMPLIANT`
    - **Crimson (`#1414E6`):** `NON_COMPLIANT`
    - **Amber (`#00D7FF`):** `UNKNOWN`
  - Compact HUD Card positioned directly above each worker:
    - Track Identifier: `Worker #1`
    - Item Badges: `H:[+]` (present), `V:[-]` (missing), `G:[?]` (unknown), `F:[?]` (unknown)
    - Status Banner: `[COMPLIANT]`, `[NON-COMPLIANT]`, or `[UNKNOWN]`
  - Environmental Hazard Overlays: Fire and smoke boxes rendered in distinct warning colors without compliance interference.

---

## 4. Verification and Validation Results

### 4.1 Controlled Scenario Tests (10/10 Passed)
Executed via `scripts/compliance/test_association_scenarios.py` with artifacts saved to `outputs/compliance/scenario_test_results.json`:

| Scenario ID | Test Case Description | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **S1** | Worker with helmet | Confirmed `PRESENT` after 3 frames | Confirmed `PRESENT` at frame 3 | **PASSED** |
| **S2** | Worker without helmet | Transition to `ABSENT` after 5 frames | `ABSENT` at frame 5, `NON_COMPLIANT` | **PASSED** |
| **S3** | Worker with safety vest | Associated in torso zone, confirmed `PRESENT` | Confirmed `PRESENT` at frame 3 | **PASSED** |
| **S4** | Worker without safety vest | Confirmed `ABSENT` after tolerance | `ABSENT` at frame 5, `NON_COMPLIANT` | **PASSED** |
| **S5** | Worker with gloves | Associated in lateral arm zone, `PRESENT` | Confirmed `PRESENT` at frame 3 | **PASSED** |
| **S6** | Worker without gloves | Transitioned to `ABSENT` after tolerance | Confirmed `ABSENT` at frame 5 | **PASSED** |
| **S7** | Worker with safety footwear | Associated in bottom ROI, `PRESENT` | Confirmed `PRESENT` at frame 3 | **PASSED** |
| **S8** | Worker without safety footwear | Transitioned to `ABSENT` after tolerance | Confirmed `ABSENT` at frame 5 | **PASSED** |
| **S9** | Multiple workers + single helmet | Bipartite assignment, no duplication | Assigned exclusively to closest worker | **PASSED** |
| **S10** | Boundary clipped worker (head) | Evaluated as `UNKNOWN`, avoids false alarm | Helmet status `UNKNOWN`, status `UNKNOWN` | **PASSED** |

### 4.2 Automated Test Suite (37/37 Passed)
All pytest unit and API tests execute cleanly:
* `backend/tests/test_compliance.py`: 14 tests covering tracker initialization, track persistence, upper/torso/foot spatial association, Hungarian assignment, temporal confirmation, tolerance decay, boundary occlusion handling, and API endpoints.
* `backend/tests/test_detection.py`: 19 tests covering Phase 4 detection pipeline, bounding box math, model loading, device selection, and video processors.
* `backend/tests/test_main.py`: 4 tests covering application routing, health checks, and error responses.

### 4.3 Real Video Pipeline Metrics
Executed on `datasets/test_safety_video.mp4` via `scripts/compliance/run_compliance_video.py`:
* **Input Resolution:** 640x480
* **Total Frames:** 75
* **Processing Speed:** 9.20 FPS (CPU)
* **Mean Frame Latency:** 105.76 ms
* **Latency Breakdown:**
  - Model Detection: ~85.4 ms
  - ByteTrack Tracking: ~1.2 ms
  - Spatial Association: ~0.8 ms
  - Temporal State Machine: ~0.6 ms
  - Visualizer HUD Rendering: ~3.8 ms
* **Tracking Metrics:**
  - Unique Tracks: 2
  - Average Track Duration: 30.0 frames
  - Lost Track Events: 2
  - Recovered Track Events: 1
  - ID Switches: 0
* **Outputs Generated:**
  - `outputs/compliance/videos/test_safety_video_compliance.mp4`
  - `outputs/tracking/tracking_metrics.json`

---

## 5. Configuration Reference

File: `configs/compliance.yaml`
```yaml
tracking:
  tracker: "bytetrack"
  track_high_thresh: 0.25
  track_low_thresh: 0.10
  new_track_thresh: 0.25
  track_buffer: 30
  match_thresh: 0.80
  min_box_area: 100

association:
  helmet:
    vertical_roi_top: -0.05
    vertical_roi_bottom: 0.30
    max_lateral_offset: 0.25
    min_containment_ratio: 0.20
  safety_vest:
    vertical_roi_top: 0.15
    vertical_roi_bottom: 0.70
    max_lateral_offset: 0.20
    min_containment_ratio: 0.30
  gloves:
    vertical_roi_top: 0.35
    vertical_roi_bottom: 0.90
    max_lateral_offset: 0.35
    min_containment_ratio: 0.15
  safety_footwear:
    vertical_roi_top: 0.70
    vertical_roi_bottom: 1.05
    max_lateral_offset: 0.25
    min_containment_ratio: 0.15

temporal:
  confirmation_frames: 3
  missing_detection_tolerance: 5
  history_window_frames: 30
  prune_lost_after_frames: 60

required_ppe:
  helmet: true
  safety_vest: true
  gloves: false
  safety_footwear: false
```

---

## 6. Known Limitations & Recommendations for Phase 6

1. **Camera Angle Sensitivity:** Highly elevated bird's-eye camera angles compress the vertical relative body zones (foreshortening). When deploying on steep top-down cameras, vertical ROI boundaries should be recalibrated.
2. **Heavy Crowds:** In very dense crowd scenes where workers overlap heavily, bounding box IoU association may yield `UNKNOWN` states due to occlusion rules. 
3. **Phase 6 Readiness:** The temporal compliance engine outputs confirmed violations (`ABSENT` on required PPE) that are ready to feed into Phase 6's Alert Engine (zone violation, persistence-based alerting, deduplication, cooldowns, and notification dispatch).
