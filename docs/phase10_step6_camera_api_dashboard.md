# RAKSHYA VISION — Phase 10 Step 6: Camera API & Dashboard Integration

## 1. Overview & Objective
In **Phase 10 Step 6**, the Multi-Camera Manager built in Step 5 has been integrated across both the backend REST API layer and the frontend React/TypeScript dashboard.

Previously, the dashboard relied on static mock camera lists (`CAM-01..CAM-04`) with dummy `ACTIVE` badges. Step 6 replaces all placeholder camera telemetry with **live, verified operational state reporting directly from active backend CameraWorkers**.

---

## 2. Backend REST API (`/api/cameras`)

Mounted in [`backend/app/api/cameras.py`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/backend/app/api/cameras.py) and registered in [`backend/app/main.py`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/backend/app/main.py):

| Endpoint | Method | Response Model | Description |
| :--- | :--- | :--- | :--- |
| `/api/cameras` | `GET` | `List[CameraStatus]` | Returns real-time status, FPS, total frames, dropped frames, reconnect counts, and masked source URLs for all registered cameras. |
| `/api/cameras/{camera_id}` | `GET` | `CameraStatus` | Returns detailed telemetry for a single camera. Returns `404` if camera does not exist. |
| `/api/cameras/{camera_id}/start` | `POST` | `CameraStatus` | Starts capture worker for the specified camera. |
| `/api/cameras/{camera_id}/stop` | `POST` | `CameraStatus` | Gracefully terminates capture loop for the specified camera. |
| `/api/cameras` | `POST` | `CameraStatus` | Dynamically registers or updates a camera configuration. |
| `/api/cameras/{camera_id}/snapshot` | `GET` | `image/jpeg` | Retrieves latest raw frame buffer as a live JPEG snapshot. Returns `503` if camera is offline. |

---

## 3. Frontend Dashboard Integration (`CamerasView.tsx`)

Located at [`frontend/src/pages/CamerasView.tsx`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/frontend/src/pages/CamerasView.tsx):
- **Real-Time Feeds Grid:** Shows each camera with its authentic lifecycle badge (`CONNECTED`, `CONNECTING`, `RECONNECTING`, `DISCONNECTED`, `ERROR`, `DISABLED`).
- **Live Stream Inspector:** Polls `/api/cameras/{id}/snapshot` dynamically to render live video frames from active workers.
- **Worker Controls:** Start/Stop toggle buttons that trigger `/api/cameras/{id}/start` and `/api/cameras/{id}/stop`.
- **Operational Telemetry Cards:** Displays actual FPS, total captured frames, dropped frame counts, and reconnect attempts.
- **Masked Source Security:** RTSP passwords (e.g. `rtsp://user:********@192.168.1.104:554/stream1`) are never visible to the operator.

---

## 4. Verification & Testing

1. **Automated Unit & API Suite (`backend/tests/test_camera_api_phase10.py`):**
   - `test_list_cameras_endpoint`: **PASSED**
   - `test_get_single_camera_endpoint`: **PASSED**
   - `test_get_nonexistent_camera_returns_404`: **PASSED**
   - `test_stop_and_start_camera_endpoints`: **PASSED**
   - `test_register_camera_endpoint`: **PASSED**
   - `test_get_camera_snapshot_endpoint`: **PASSED**
   - `test_get_camera_snapshot_offline_returns_503`: **PASSED**
2. **Frontend Build Verification:**
   - `npm run build` completed with **0 TypeScript errors and 0 lint failures**.
