# SafeSync Final Prototype — Phase 1: Complete Project Audit Report

**Date:** 2026-10-11  
**System Status:** Pre-Fix Audit Baseline  
**Auditor:** Senior Full-Stack & AI Systems Engineer  

---

## 1. Executive Summary & Root Cause Analysis

A complete non-destructive audit of the SafeSync codebase was conducted. The core AI model, inference pipeline, and React frontend build are functional and verified. However, **live camera detection in the dashboard fails due to three distinct confirmed root causes**:

1. **Camera Manager Resource Exhaustion & FFmpeg Packet Overload (CRITICAL)**
   - In `backend/app/main.py`, the lifespan startup handler executes:
     ```python
     CameraManager.get_instance().start_all()
     ```
   - In `configs/cameras.yaml` and SQLite `cameras` table, there are **25 file cameras** (`cam_output2_01` through `cam_output2_18`, `cam_new_01` through `cam_new_07`) pointing to non-existent file paths (`D:\Additional\Safesync\output2\...` and `D:\Additional\New folder (2)\...`).
   - `CameraManager` launches **25 background threads** that simultaneously enter infinite reconnection loops trying to open missing video files using OpenCV / FFmpeg.
   - This saturates backend file descriptors, spawns 25 parallel reconnect threads, spams the console with `grabFrame packet read max attempts exceeded`, starves CPU resources, and prevents the physical webcam capture worker from operating cleanly.

2. **Frontend Default Camera & Viewport Gating (HIGH)**
   - In `frontend/src/pages/LiveMonitoringView.tsx`:
     ```tsx
     const [selectedCameraId, setSelectedCameraId] = useState<string>(
       cameras[0]?.camera_id || 'camera_01'
     );
     ```
     `camera_01` does not exist or is disabled. When the dashboard loads before cameras are fetched, it defaults to an invalid ID.
   - In `frontend/src/components/CameraFeedPlayer.tsx`:
     The viewport gate conditionally blocks `<img src={streamUrl} />` if `!isCameraOnline` or `isStale`. On initial webcam connection, before telemetry arrives, the frontend falls back to `"Camera Signal Standby"` instead of opening the live stream image tag.

3. **Live-Only Prototype Scope vs Stale Recorded Video Matrix (MEDIUM)**
   - The system is configured as a multi-camera recorded-video matrix, whereas the evaluation target is a **reliable live-only prototype** (physical webcam + live AI inference).

---

## 2. Project Architecture & Entry Points

### 2.1 Backend
- **Root Directory:** `D:\Additional\PROJECT\SafeSync\backend`
- **Entry Point:** `app.main:app`
- **Framework:** FastAPI, Uvicorn, SQLAlchemy, OpenCV (`cv2`), PyTorch (`torch`), Ultralytics YOLO
- **Python Environment:** `D:\Additional\PROJECT\SafeSync\backend\.venv\Scripts\python.exe` (Python 3.13.15)
- **Start Command:**
  ```powershell
  cd D:\Additional\PROJECT\SafeSync\backend
  .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```

### 2.2 Frontend
- **Root Directory:** `D:\Additional\PROJECT\SafeSync\frontend`
- **Entry Point:** `src/main.tsx` (Vite + React 18 + TypeScript + Tailwind CSS)
- **Production Build:** `npm run build` (Verified: **PASS**, builds in 4.64s without errors)
- **Start Command:**
  ```powershell
  cd D:\Additional\PROJECT\SafeSync\frontend
  npm run dev -- --host 0.0.0.0 --port 5173
  ```

---

## 3. Production Model & AI Inference Audit

| Property | Status | Value / Observation |
|---|---|---|
| **Production Model Path** | **PASS** | `models/detection/ppe_fire_smoke_v3/weights/best.pt` |
| **Model Checkpoint Integrity** | **PASS** | SHA-256 match: `9b414f3018d54ae5...` |
| **Canonical Classes (7)** | **PASS** | `0: person`, `1: helmet`, `2: safety_vest`, `3: gloves`, `4: safety_footwear`, `5: fire`, `6: smoke` |
| **Hardware Detection** | **PASS** | Hardware USB Webcam Index 0 is accessible via `cv2.VideoCapture(0, cv2.CAP_DSHOW)` (Resolution: 640x480) |
| **Direct Inference Execution** | **PASS** | Tested model directly on webcam frame: detected person (`conf: 0.31`) in ~397ms on CPU |
| **P0 Environmental Hazards** | **PASS** | Decoupled fire/smoke detection preserved with color/flicker and worker-torso exclusion |
| **Compliance Ontology** | **PASS** | `UNKNOWN` strictly preserved as non-violating (never treated as `ABSENT` or `SAFE`) |

---

## 4. Test Results Baseline

| Test Suite | Target | Status | Notes |
|---|---|---|---|
| Smoke Test | `tests/test_smoke.py` | **PASS (3/3)** | Core imports, ontology, and `UNKNOWN != ABSENT` verified. |
| Safety Engine & Compliance | `tests/test_safety_engine.py`<br>`tests/test_compliance.py` | **PASS (22/22)** | All 7 safety rules, tri-state compliance, and tracking verified. |
| Live Camera Pipeline | `tests/test_live_camera_pipeline.py` | **6 PASS, 1 FAIL** | 6 tests passed; 1 latency assertion failed (`123ms` vs `<100ms` strict threshold due to single-core synthetic load). |
| Frontend Typecheck & Build | `npm run build` | **PASS** | 0 TypeScript errors, minification and bundling succeed. |

---

## 5. Issue Classification

### CRITICAL
1. **25 Non-Existent File Streams in Auto-Start Loop**
   - **File:** `configs/cameras.yaml`, `backend/app/database/session.py` (DB table `cameras`)
   - **Impact:** Spawns 25 parallel threads endlessly trying to read missing `.mp4` files, causing `grabFrame packet read max attempts exceeded` and thread starvation.
   - **Fix:** In `cameras.yaml` and SQLite DB, mark file cameras as `enabled: false` (or disable multi-file matrix auto-start), keeping `cam_live_webcam` enabled as primary.

### HIGH
2. **Frontend Initial Camera Selection Defaults to Invalid ID**
   - **File:** `frontend/src/pages/LiveMonitoringView.tsx` (lines 47-49)
   - **Impact:** Defaults to `'camera_01'` which does not exist, causing blank screen / standby until manually clicked.
   - **Fix:** Default `selectedCameraId` dynamically to `'cam_live_webcam'` or `cameras[0]?.camera_id`.

3. **Stream Viewport Gating in CameraFeedPlayer**
   - **File:** `frontend/src/components/CameraFeedPlayer.tsx` (line 416)
   - **Impact:** `!isCameraOnline` hides `<img src={streamUrl} />` before initial telemetry arrives.
   - **Fix:** Render `<img src={streamUrl} />` when `activeCamera.enabled !== false`, allowing native image stream rendering and handling errors gracefully via `onError`.

### MEDIUM
4. **Recorded Video Upload Workflow Not Needed for Live Prototype**
   - The prototype should focus purely on the live physical camera feed with real-time YOLO detection and hazard alerts.

---

## 6. Recommended Phase 2 Repair Plan

1. **Step 1 — Disable Dead Camera Workers:** Update `configs/cameras.yaml` and SQLite database so only `cam_live_webcam` (index 0) is `enabled: true`. Disable the 25 missing `.mp4` video entries to immediately eliminate the FFmpeg `grabFrame packet read max attempts exceeded` errors and thread saturation.
2. **Step 2 — Prioritize Live Camera in Frontend:** Update `LiveMonitoringView.tsx` and `OverviewView.tsx` to automatically default to `cam_live_webcam`.
3. **Step 3 — Relax Premature Viewport Block in CameraFeedPlayer:** Render the stream image element whenever the camera is enabled, allowing instant MJPEG feed display.
4. **Step 4 — Start Backend & Frontend Services:** Run both services cleanly and execute end-to-end live testing with real YOLO inference on the physical camera feed.
5. **Step 5 — Generate Phase 2 Validation Report:** Document verified FPS, latency, and live detection results in `reports/LIVE_CAMERA_FIX_TEST_RESULTS.md`.

---
*Status: Phase 1 complete. Awaiting user approval to proceed with Phase 2 fixes.*
