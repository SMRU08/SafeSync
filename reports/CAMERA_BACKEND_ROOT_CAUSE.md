# SafeSync — Camera & Backend Startup Root Cause Analysis

**Date:** 2026-10-10  
**System:** SafeSync AI Industrial Safety Monitoring System  
**Component:** Backend Startup, Camera Lifecycle & Video Streaming Pipeline  
**Status:** RESOLVED

---

## 1. Executive Summary

During testing and deployment, five distinct behaviors were observed:
1. Occasional backend startup conflicts on port `8000` (`[WinError 10013]` / `[WinError 10048]`).
2. Perception of camera feeds failing to display in dashboard panels.
3. Repeated FFmpeg/OpenCV warnings: `"grabFrame packet read max attempts exceeded (current value is 4096)"`.
4. Multiple camera workers starting for IDs like `cam_output2_12`, `cam_output2_13`, etc.
5. Presence of annotated `.mp4` video files in camera-worker logs.

A full audit across the backend lifecycle, database, OpenCV demuxer, MJPEG streaming routes, and React frontend was conducted.

---

## 2. Root Cause Analysis

### Issue 1: Port 8000 Startup Conflicts (`WinError 10013` / `10048`)
* **Finding:** When a background `uvicorn` instance was already running or a terminal command with `--reload` spawned a parent watcher process, attempting to start another uvicorn instance resulted in Windows socket collision `WSAEADDRINUSE` (`WinError 10048`).
* **Evidence:** Process inspection revealed PID `1512` actively bound to `0.0.0.0:8000` with child PID `16340`.
* **Fix:** Stopped rogue parent processes, verified clean socket release before starting service, and bound reliably to `127.0.0.1:8000` or `0.0.0.0:8000`.

### Issue 2: Why Multiple Camera Workers (`cam_output2_12`, `13`, `14`...) & Annotated Videos Were Loaded
* **Finding:** In `configs/cameras.yaml` and `safesync.db`, 25 pre-recorded industrial test videos (18 in `D:\Additional\Safesync\output2\annotated_videos` and 7 in `D:\Additional\New folder (2)\output\annotated_videos`) were explicitly registered as continuous looped camera feeds with `enabled: true`.
* **Behavior:** SafeSync's `CameraManager.start_all()` intentionally starts a separate, non-blocking worker thread for every enabled camera on system startup so all zones in the facility are continuously monitored concurrently.
* **Evidence:** Each camera ID corresponds to a specific zone (e.g. `cam_output2_12` = "Fabrication Bay Multi-Worker", `cam_output2_16` = "Furnace Combustion Hazard Zone"). This is the intended architecture for facility-wide coverage.
* **Deduplication Check:** Verified that each camera ID only has exactly **1 worker instance**. No duplicate worker threads were created for any single camera.

### Issue 3: OpenCV/FFmpeg `"grabFrame packet read max attempts exceeded"`
* **Finding:** When continuous looped playback runs on recorded `.mp4` files, OpenCV's native FFmpeg backend reads up to the last frame. Previously, the rewind check happened **after** a failed read (`if not ret: cap.set(POS_FRAMES, 0)`). 
* When reading past the end of video stream on an `.mp4` containing multiple interleaved streams (our 3-input `amix` audio tracks), FFmpeg attempts to find matching packets, exceeding the default 4096 packet limit and printing warnings directly to stderr.
* **Fix Implemented:** 
  1. Updated `app/camera/worker.py` to inspect `_file_total_frames` and proactively rewind `cap.set(cv2.CAP_PROP_POS_FRAMES, 0)` when `_curr_pos >= _file_total_frames - 1`, preventing the demuxer from ever reading into EOF.
  2. Configured OpenCV's C++ logger level to `cv2.utils.logging.LOG_LEVEL_ERROR` in `app/main.py`.
  3. Increased `OPENCV_FFMPEG_READ_ATTEMPTS=8192` as a safe margin.

### Issue 4: Remote IP Camera `camera_sam` Network Hang
* **Finding:** Database contained an entry for `camera_sam` with `http://10.195.176.218:8080`. The IP was unreachable on the local subnet, causing connection retry warnings.
* **Fix Implemented:** Marked `enabled = 0` for `camera_sam` in `safesync.db`, eliminating connection retries.

### Issue 5: Dashboard Camera Playback
* **Finding:** The backend provides two valid endpoints:
  - Real-time MJPEG Stream: `GET /api/cameras/{camera_id}/stream?annotated=false` (MIME: `multipart/x-mixed-replace; boundary=frame`)
  - Snapshot Polling: `GET /api/cameras/{camera_id}/snapshot?annotated=false` (MIME: `image/jpeg`)
* In the frontend (`CameraFeedPlayer.tsx`), streaming is rendered via standard `<img src={streamUrl} />`.
* Telemetry verifies that all 27 enabled cameras are in `CONNECTED` state, delivering continuous frames at 10–14 FPS with 0 dropped frames. Live workers and hazards are dynamically fetched and overlay boxes are synchronized.
