# CAMERA_02 CONNECTION FAILURE: ROOT-CAUSE DIAGNOSTICS & PRODUCTION FIX

## 1. Executive Summary & Root Cause Determination

During real-world multi-camera testing, `camera_02` repeatedly failed to establish an active video stream and exhausted its reconnection retry loop with the following operational logs:
```
Camera camera_02 connection failed (attempt 1/5). Retrying in 1.00s...
Camera camera_02 connection failed (attempt 2/5). Retrying in 2.00s...
Camera camera_02 connection failed (attempt 3/5). Retrying in 4.00s...
Camera camera_02 connection failed (attempt 4/5). Retrying in 8.00s...
Camera camera_02 reached max retries (5). Stopping retry loop.
CameraWorker capture loop exited for camera_02
```

### Exact Root Cause
The root cause of the failure is a **physical and logical network layer endpoint unreachability (IP Subnet Mismatch)**:
1. **Network Subnet Mismatch**:
   - The configured source URL for `camera_02` was hardcoded to `http://192.168.137.166:8080/video`.
   - The IP subnet `192.168.137.0/24` is the default subnet used by the **Windows Mobile Hotspot** feature (ICS).
   - At the time of execution, the Windows host machine was connected to an external Wi-Fi network with IP address **`10.57.213.216`** (Default Gateway: `10.57.213.131`), and the Windows Mobile Hotspot adapter was disconnected.
   - Consequently, no network route existed from the host machine to `192.168.137.166`.
2. **Endpoint Unreachable (WSAETIMEDOUT / Error -138)**:
   - Any TCP connection attempts to `192.168.137.166:8080` timed out at the OS socket layer (`WinError 10060 / ETIMEDOUT`).
   - OpenCV's `cv2.VideoCapture` timed out after FFmpeg reported `error -138 (Connection timed out)`.
3. **Telemetry & Failure State Gap**:
   - Previously, when max retries were exhausted, the worker logged a message and left the state as `ERROR` or exited without updating explicit failure telemetry (`last_error`, `last_attempt`, `retry_count`) for the dashboard operator.
   - The frontend did not provide an intuitive way to test or reconfigure the mobile phone's dynamic IP address without database or YAML modifications.

---

## 2. Camera Source Configuration

The configured camera stream for `camera_02` was inspected across all persistence layers:

- **Source Configuration (`configs/cameras.yaml`)**:
  ```yaml
  - id: camera_02
    name: "Zone B - Mobile Stream"
    source: "http://192.168.137.166:8080/video"
    source_type: "http"
    enabled: true
    zone_id: "ZONE-B"
    location: "Material Staging Area"
    reconnect_policy:
      max_retries: 5
      initial_delay_seconds: 1.0
      max_delay_seconds: 30.0
  ```
- **SQLite Database Record (`safesync.db`, Table `cameras`, ID 2)**:
  - `id`: `2`
  - `camera_id`: `camera_02`
  - `source`: `http://192.168.137.166:8080/video`
  - `source_type`: `http`
  - `enabled`: `1`

---

## 3. Network Test Results (OS & Socket Layer)

Network diagnostic audits were executed directly from the host Windows environment:

1. **Host Network Interfaces (`ipconfig /all`)**:
   - Wireless LAN adapter Wi-Fi:
     - IPv4 Address: `10.57.213.216` (Preferred)
     - Subnet Mask: `255.255.255.0`
     - Default Gateway: `10.57.213.131`
     - DHCP Server: `10.57.213.131`
   - Mobile Hotspot / Wi-Fi Direct:
     - `Media State: Media disconnected`
   - Active Subnet: `10.57.213.0/24`. Host is NOT on `192.168.137.0/24`.

2. **TCP Socket Probe (`192.168.137.166:8080`)**:
   - Diagnostic script tested a non-blocking TCP socket connect with a 2.0-second timeout:
   - Result: **`FAILED` (Timed out after 2.0s, WSAETIMEDOUT 10060)**.
   - Conclusion: The target IP is not present on the current local network or the phone is not broadcasting on that IP.

---

## 4. HTTP Test Results

An HTTP GET request was dispatched directly to `http://192.168.137.166:8080/video` using `urllib.request`:
- Request: `GET http://192.168.137.166:8080/video HTTP/1.1`
- Timeout: 3.0 seconds
- Result: **`URLError: <urlopen error timed out>`**
- Conclusion: HTTP server is completely unreachable from the host environment.

---

## 5. OpenCV Test Results

OpenCV `cv2.VideoCapture` was invoked directly against `http://192.168.137.166:8080/video`:
```python
cap = cv2.VideoCapture("http://192.168.137.166:8080/video")
opened = cap.isOpened()
```
- Standard Error output:
  ```
  [tcp @ 0000021c5f3ba2c0] Connection to tcp://192.168.137.166:8080 failed: Error number -138 occurred
  ```
- OpenCV return: `cap.isOpened() == False`.

---

## 6. Frame-Read Result

Because `cap.isOpened()` was `False`, `cap.read()` returned:
- `ret == False`
- `frame is None`
- Zero bytes acquired.

---

## 7. Bounded Retry Behavior & State Machine Fix

### Problem
Previously, when the retry loop exhausted all attempts (`attempt 5/5`), the worker did not mark the state as `OFFLINE`, and did not capture the ISO timestamp of the last attempt or the exact network failure reason.

### Implemented Fix
1. **Fast Socket Pre-flight Check**:
   - `is_network_endpoint_reachable(source, timeout=0.8)` was introduced.
   - For network/HTTP/RTSP streams, a socket probe runs before calling `cv2.VideoCapture`. If the host/port cannot establish a TCP handshake in 0.8s, the worker immediately logs a network failure rather than blocking for 30 seconds inside FFmpeg.
2. **Clean Transition to `OFFLINE`**:
   - Once `reconnect_attempts >= policy.max_retries`, the worker transitions cleanly to `CameraState.OFFLINE`.
   - Records `self.metrics.last_error = f"Connection failed: host unreachable or stream offline at {self.safe_source}"`.
   - Records `self.metrics.last_attempt_timestamp = now`.
   - Records `self.metrics.retry_count = reconnect_attempts`.
3. **Status Schema Export**:
   - `get_status()` formats `last_attempt` as an ISO timestamp (`2026-09-28T15:19:47.528318+00:00`).
   - Both `CameraStatus` and `CameraMetrics` schemas now expose `last_attempt`, `last_error`, and `retry_count`.
4. **Fault Isolation**:
   - `camera_01` (webcam index 0) operates in an independent thread and is completely decoupled from `camera_02`.
   - The AI pipeline, database persistence, and WebSocket events remain active and unaffected.
   - Fire and smoke detection rules run on every frame and do not require workers to be present.

---

## 8. Files Changed

1. **`backend/app/camera/schemas.py`**:
   - Added `last_attempt: Optional[str]`, `last_attempt_timestamp: Optional[float]`, `retry_count: int`, and `last_error: Optional[str]` to `CameraMetrics` and `CameraStatus`.
2. **`backend/app/camera/worker.py`**:
   - Added `is_network_endpoint_reachable()` pre-flight socket validation with 0.8s timeout.
   - Updated retry exhaustion handler: sets `self.state = CameraState.OFFLINE`, logs transition, and populates `last_error`, `last_attempt_timestamp`, and `retry_count`.
   - Updated `get_status()` to populate all offline diagnostic fields.
3. **`backend/app/api/cameras.py`**:
   - Added explicit `@router.post("/{camera_id}/retry")` and `@router.post("/{camera_id}/reconnect")` endpoints that reset retry counters and restart worker loops.
4. **`backend/app/camera/manager.py`**:
   - Hardened `test_camera_source` with fast socket reachability check and detailed diagnostic error codes (`HOST_UNREACHABLE`, `FRAME_ACQUISITION_FAILED`).
5. **`frontend/src/types/safety.ts`**:
   - Added `last_attempt`, `last_error`, `retry_count` fields to `CameraConfig`.
6. **`frontend/src/components/AddCameraModal.tsx`**:
   - Added support for editing existing cameras via `editCamera` prop.
   - Added structured mobile IP camera configuration fields:
     - Phone Host/IP (e.g. `10.57.213.x` or `192.168.1.x`)
     - Port (default `8080`)
     - Stream Path (default `/video`, `/mjpeg`, `/videofeed`)
     - Dynamic full stream URL compilation
   - Integrated pre-flight "Test Feed" connection testing with visual success/error badges.
7. **`frontend/src/components/CameraLiveCard.tsx`**:
   - Improved offline card presentation: shows `CAM-02 OFFLINE`, last attempt time, failure reason, and dedicated `Retry Connection` and `Configure Source` buttons.
8. **`frontend/src/pages/CamerasView.tsx`**:
   - Added `editingCamera` state.
   - Wired `onEdit` handler to open the modal prepopulated with `camera_02`'s current configuration.
   - Mapped `last_attempt`, `last_error`, and `retry_count` in `loadCameras`.

---

## 9. Tests Executed & Verification

| Test Scenario | Description | Result |
| :--- | :--- | :--- |
| **Network Socket Diagnostic** | Tested connection to `192.168.137.166:8080` outside OpenCV | `FAILED` (WSAETIMEDOUT 10060 as expected) |
| **Worker Bounded Retries** | Ran `CameraWorker` against unreachable source with `max_retries=2` | `PASSED` (Exhausted 2 retries and transitioned to OFFLINE) |
| **Worker Telemetry Validation** | Checked `status.state`, `status.last_error`, `status.last_attempt`, `status.retry_count` | `PASSED` (`OFFLINE`, error string set, ISO timestamp present, count=2) |
| **Frontend TypeScript Build** | Ran `npm run build` (`tsc -b && vite build`) in `frontend/` | `PASSED` (0 errors, dist compiled in 6.94s) |
| **Fault Isolation Check** | Verified `camera_01` and AI components when `camera_02` is offline | `PASSED` (100% isolated, no main thread stalls) |

---

## 10. Final Camera State

- **`camera_01` (USB Index 0)**:
  - State: `STREAMING` / `ONLINE`
  - Frames captured: Active
  - AI Safety & Compliance: Active
- **`camera_02` (Android IP Webcam)**:
  - State: `OFFLINE` (Clean, non-crashing state)
  - Last Attempt: Recorded (ISO timestamp)
  - Last Error: `"Connection failed: host unreachable or stream offline at http://192.168.137.166:8080/video"`
  - Retry Count: `5`

---

## 11. Operational Instructions for Operators

When using a smartphone as `camera_02` (via Android IP Webcam or DroidCam), mobile IP addresses change dynamically depending on the network.

### How to Reconnect Camera 02 (Zero Code Edits):
1. **Open the Camera App on Phone**:
   - Open **IP Webcam** on Android.
   - Scroll down to the bottom and tap **"Start server"**.
   - Note the IPv4 address shown on the phone screen (e.g. `http://10.57.213.xxx:8080` or `http://192.168.1.xxx:8080`).
   - Ensure the phone is connected to the **same Wi-Fi network** as the SafeSync PC (or connected via USB tethering/Mobile Hotspot).
2. **Update in SafeSync Web UI**:
   - In SafeSync, navigate to **Cameras** view (`/cameras`).
   - On the `camera_02` card (showing `OFFLINE`), click the **"Configure Source"** button (or click **"Add Camera"**).
   - Under **Stream Source Type**, select **"Mobile IP Camera (Android)"**.
   - Enter the **Phone IP Address** and **Port** displayed on the phone screen.
   - Click **"Test Feed"**:
     - If the phone is reachable, a green checkmark will appear showing *"Stream verified! Received valid frame from hardware."*
     - If unreachable, a red warning will show the specific error (e.g., host unreachable).
   - Click **"Update Camera"** (or **"Add Camera"**).
3. **Trigger Reconnect**:
   - The worker immediately connects to the new URL and transitions to `STREAMING` with real-time video and AI analytics active.
