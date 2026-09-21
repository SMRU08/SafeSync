# Multi-Camera Management

RAKSHYA VISION manages multiple concurrent video streams across diverse camera hardware through a resilient, thread-isolated multi-camera architecture.

---

## 1. Architectural Design

The camera subsystem is governed by a centralized singleton lifecycle manager (`CameraManager`) that spawns and oversees independent worker threads (`CameraWorker`):

```
                   ┌───────────────────────────┐
                   │       CameraManager       │ (Singleton Lifecycle Controller)
                   └─────────────┬─────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  CameraWorker 1 │     │  CameraWorker 2 │     │  CameraWorker 3 │
│  (RTSP Stream)  │     │  (USB Webcam)   │     │  (Video File)   │
│  State: CONNECTED     │State: RECONNECT │     │  State: CONNECTED
│  Thread-Isolated│     │Backoff: 2.0s    │     │  Thread-Isolated│
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 1.1 Key Operational Invariants
1. **Thread Isolation:** Each video feed runs in a dedicated background daemon thread. A stall, decode error, or network drop on one camera never impacts neighboring cameras or the FastAPI backend.
2. **Credential Masking:** Cleartext RTSP/HTTP passwords embedded in URLs (e.g. `rtsp://admin:pass123@192.168.1.10:554/live`) are masked as `rtsp://admin:********@192.168.1.10:554/live` across all logs, telemetry endpoints, and frontend views.
3. **Environment Variable Expansion:** Credentials and hostnames can be securely passed using `${ENV_VAR}` syntax in configuration files (e.g. `rtsp://${CAMERA_USER}:${CAMERA_PASS}@${CAMERA_HOST}/stream`).

---

## 2. Reconnection Policy & Backoff

When an RTSP connection drops or an optical sensor disconnects, `CameraWorker` transitions to `RECONNECTING` and executes bounded exponential backoff:

$$\text{delay} = \min\left(\text{max\_delay},\; \text{initial\_delay} \times 2^{(\text{attempt} - 1)}\right)$$

### Default Reconnection Parameters
- `initial_delay_seconds`: `1.0`
- `max_delay_seconds`: `30.0`
- `max_retries`: `10`

If the maximum retry limit is reached without restoring connection, the worker enters an `ERROR` state, updates system metrics, and alerts the operator via the dashboard.

---

## 3. Configuration Specification

Cameras are configured declaratively in `configs/cameras.yaml`:

```yaml
cameras:
  - id: "camera_01"
    name: "Primary Entrance & Assembly"
    zone_id: "zone_a"
    source_type: "opencv"
    source: "0"  # Laptop / USB Webcam index 0
    enabled: true
    fps_target: 30
    reconnect_policy:
      max_retries: 5
      initial_delay_seconds: 1.0
      max_delay_seconds: 10.0

  - id: "camera_02"
    name: "Turbine Hall East"
    zone_id: "turbine_deck"
    source_type: "rtsp"
    source: "rtsp://${RTSP_USER}:${RTSP_PASS}@192.168.1.50:554/h264Preview_01_main"
    enabled: true
    fps_target: 25
    reconnect_policy:
      max_retries: 10
      initial_delay_seconds: 2.0
      max_delay_seconds: 30.0
```

---

## 4. Operational Lifecycle States

```
DISABLED ──(Start)──► CONNECTING ──► CONNECTED ──► (Read Frame)
                            │              │
                            │ (Failure)    │ (Frame Lost)
                            ▼              ▼
                          ERROR ◄─── RECONNECTING
```

- **`DISABLED`:** Camera is registered in configuration but halted.
- **`CONNECTING`:** Worker thread initializing video capture backend.
- **`CONNECTED`:** Actively decoding frames and passing to inference loop.
- **`RECONNECTING`:** Temporary network drop; backoff timer in progress.
- **`ERROR`:** Failed to reconnect after exhausting maximum retries.
