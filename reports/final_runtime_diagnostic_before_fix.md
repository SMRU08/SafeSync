# SafeSync — Final Runtime Diagnostic Report (Before Fix)

**Date:** 2026-10-08  
**Author:** SafeSync Senior Production Engineer  
**Objective:** Document runtime diagnostic state before implementing runtime fixes  

---

## 1. Git & Repository Checkpoint State

- **Current Branch:** `master`
- **Current Head Commit:** `eb6009d` (`eval: validate safesync v7 run 3 controlled shadow mode pipeline`)
- **Working Tree State:** Clean (no modified tracked files)
- **Untracked Artifacts:**
  - `FINAL_SUBMISSION_READINESS.md`
  - `scripts/testing/verify_submission_readiness.py`
- **Diff Stat:** 0 tracked changes (`git diff --stat` is empty)

---

## 2. Production Model Security & Lock Status

All model weights verified on disk via SHA-256 before runtime audit:

| Role | Model Path | Expected SHA-256 | Actual Disk SHA-256 | Status |
| :--- | :--- | :--- | :--- | :--- |
| **PRODUCTION (V3)** | `models/detection/ppe_fire_smoke_v3/weights/best.pt` | `9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe` | `9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe` | **MATCH (LOCKED)** |
| **SHADOW (V6)** | `models/detection/safesync_v6_hardnegative/weights/best.pt` | `c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc` | `c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc` | **MATCH (LOCKED)** |
| **EXPERIMENTAL (V7 R3)** | `models/detection/safesync_v7_small_object/runs/run3/weights/best.pt` | `d725767535e9bd56586620378b4411a443b7fd17653625f2d8a2886b63aaf218` | `d725767535e9bd56586620378b4411a443b7fd17653625f2d8a2886b63aaf218` | **MATCH (LOCKED)** |

**Lock Assertion:** No retraining, no weight changes, and no promotion of experimental models.

---

## 3. Observed Runtime Symptoms

When launching the frontend, the UI displayed:
- **API:** OFFLINE
- **AI Engine:** UNAVAILABLE / STANDBY
- **DB:** OFFLINE
- **WebSocket:** DISCONNECTED / CONNECTING
- **Camera:** OFFLINE (`Camera CAMERA_01 Offline: Cannot reach source (endpoint offline)`)

---

## 4. Root Cause Breakdown

### Issue 1: Orphaned Process & Port 8000 Socket Freeze
- **Finding:** A previous background Uvicorn reloader process (PID 4092) and worker (PID 16196) were running in a frozen/hung state holding port 8000.
- **Evidence:** Over 60 TCP sockets were trapped in `CloseWait` on port 8000. `Invoke-RestMethod` to `http://localhost:8000/api/health` and `http://localhost:8000/health/live` timed out indefinitely.
- **Resolution:** Safely terminated orphaned PIDs 4092 and 16196 to free port 8000.

### Issue 2: Root-Level Startup Import Resolution (ModuleNotFoundError)
- **Finding:** Running `python -m uvicorn backend.app.main:app --reload` from the project root fails with:
  ```text
  File "D:\Additional\PROJECT\SafeSync\backend\app\main.py", line 5, in <module>
    from app.config import settings
  ModuleNotFoundError: No module named 'app'
  ```
- **Cause:** When starting from project root, Python sets `sys.path[0]` to the project root. Since `app` is located inside the `backend/` directory, Python cannot resolve `from app.config` without `backend` on Python's path or without Uvicorn's `--app-dir backend` flag.
- **Classification:** **IMPORT ERROR / ENVIRONMENT RESOLUTION**.

### Issue 3: Camera Device Index Hardware Conflict (DirectShow Crash)
- **Finding:** `CameraManager.start_all()` loads cameras from both `configs/cameras.yaml` AND `safesync.db`.
  - In `configs/cameras.yaml`: `camera_01` was configured with `source: "0"` (`usb`), `enabled: true`.
  - In `safesync.db`: `camera_sahil` was registered with `source: "0"` (`usb`), `enabled: 1`.
- **Cause:** Both workers started simultaneously and called `cv2.VideoCapture(0, cv2.CAP_DSHOW)` on the same physical USB device. Windows DirectShow crashed with:
  ```text
  [ WARN:0@10.873] global cap.cpp:456 cv::VideoCapture::open VIDEOIO(DSHOW): raised unknown C++ exception!
  ```
  This left physical webcam 0 locked and marked OFFLINE.
- **Verification:** Independent test with single-thread OpenCV confirmed device 0 works perfectly (`Webcam 0 opened: True, Frame: (480, 640, 3)`).
- **Classification:** **CAMERA INITIALIZATION & CONFIGURATION ERROR**.

### Issue 4: Stale Database Test Cameras & Offline IP Stream
- **Finding:** `safesync.db` contained 7 test cameras (`api_test_synth`, `cam_live_test`, `mgr_cam_1`, etc.), some marked `enabled: 1`.
- **Finding:** `camera_02` in `configs/cameras.yaml` is set to an unreachable remote IP webcam (`http://192.168.137.166:8080/video`), which repeatedly warned on startup and delayed camera manager operations.

---

## 5. Planned Fix Actions

1. Ensure standard project package resolution for `backend` so `uvicorn` starts cleanly whether run from root (`--app-dir backend`) or via `backend.app.main:app`.
2. Sanitize database camera entries:
   - Purge duplicate `camera_sahil` USB conflict.
   - Disable or clean leftover test entries using `CameraManager.validate_and_cleanup_cameras(remove_broken=True)`.
3. Set `camera_02` (offline mobile IP) to `enabled: false` in `configs/cameras.yaml` so only physical `camera_01` (webcam 0) auto-starts for the single-camera baseline.
4. Verify backend health endpoints (`/api/health`, `/health/live`, `/health/ready`).
5. Verify WebSocket `/ws/events` and frontend connectivity.
