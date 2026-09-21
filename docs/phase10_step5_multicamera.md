# RAKSHYA VISION — Phase 10 Step 5: Production Multi-Camera Manager

## 1. Executive Summary & Objective
Phase 10 Step 5 upgrades RAKSHYA VISION from static/dummy camera metadata configurations (`configs/cameras.yaml` with placeholder sources) into a **thread-isolated, production-grade Multi-Camera Manager**.

In high-concurrency industrial safety environments, cameras frequently experience transient network drops, hardware reboots, packet loss, and RTSP stream resets. Step 5 guarantees that:
1. Every camera worker operates on its own dedicated background thread.
2. A crash, failure, or timeout on Camera A **never impacts** Camera B, C, or the central FastAPI server.
3. Connection drops are handled using **bounded exponential backoff** ($delay = \min(\text{max\_delay}, \text{initial\_delay} \times 2^{\text{attempt}})$) to avoid hammering network gateways.
4. Plaintext credentials (e.g. `rtsp://user:password@ip`) are **strictly masked** in all logs, status responses, and operational metrics.
5. Graceful shutdown releases all system and OpenCV resources cleanly.

---

## 2. Architecture & Concurrency Model

```
                    ┌───────────────────────────────────────┐
                    │             FastAPI App               │
                    │        (Lifespan Management)          │
                    └──────────────────┬────────────────────┘
                                       │
                                       ▼
                    ┌───────────────────────────────────────┐
                    │            CameraManager              │
                    │   (Singleton Lifecycle Coordinator)   │
                    └──────┬───────────┼───────────┬────────┘
                           │           │           │
             ┌─────────────┘           │           └─────────────┐
             ▼                         ▼                         ▼
   ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
   │  CameraWorker 1  │      │  CameraWorker 2  │      │  CameraWorker 3  │
   │  (Thread 1, USB) │      │  (Thread 2, RTSP)│      │(Thread 3, Synth) │
   │ ───────────────  │      │ ───────────────  │      │ ───────────────  │
   │ State: CONNECTED │      │ State: ERROR     │      │ State: CONNECTED │
   │ FPS: 29.8        │      │ Reconnect: 5/5   │      │ FPS: 30.0        │
   │ Frame Buffer [L] │      │ Isolated Failure │      │ Frame Buffer [L] │
   └──────────────────┘      └──────────────────┘      └──────────────────┘
```

### Key Components
- **`CameraConfigModel` (`backend/app/camera/schemas.py`)**: Pydantic schema enforcing typed configurations, resolution, FPS targets, source type (`usb`, `rtsp`, `file`, `synthetic`), and reconnect policies.
- **`CameraWorker` (`backend/app/camera/worker.py`)**: Encapsulates capture lifecycle in an independent daemon thread with thread-safe frame access (`threading.Lock`) and non-blocking state reporting.
- **`CameraManager` (`backend/app/camera/manager.py`)**: Central orchestrator providing dynamic registration, start, stop, single-camera control, and batch shutdown hooks registered with FastAPI lifespan.

---

## 3. Explicit Lifecycle States

Every camera worker transitions through explicit, deterministic states:
- **`DISABLED`**: Camera configured with `enabled: false`. No capture thread is spawned.
- **`CONNECTING`**: Initial connection attempt to the video stream or device.
- **`CONNECTED`**: Video stream active and producing valid frames.
- **`RECONNECTING`**: Connection dropped or transient read failure. Worker executing bounded backoff before retrying.
- **`DEGRADED`**: Intermittent frame drop detected, but stream remains open.
- **`DISCONNECTED`**: Intentionally stopped via `worker.stop()` or manager shutdown.
- **`ERROR`**: Maximum retries exhausted (`reconnect_count >= max_retries`) or critical unrecoverable capture error.

---

## 4. Reconnection & Backoff Mechanics

Reconnection is governed by `ReconnectPolicy`:
- `max_retries`: Maximum consecutive reconnect attempts before transitioning to `ERROR` state.
- `initial_delay_seconds`: Initial sleep interval before first retry.
- `max_delay_seconds`: Hard ceiling for backoff delays.

$$\text{Delay}_n = \min\left(\text{max\_delay}, \text{initial\_delay} \times 2^{n - 1}\right)$$

Example progression ($initial=1.0\text{s}, max=15.0\text{s}$):
- Attempt 1: 1.0s
- Attempt 2: 2.0s
- Attempt 3: 4.0s
- Attempt 4: 8.0s
- Attempt 5: 15.0s (capped)
- Reached max retries $\rightarrow$ `CameraState.ERROR` logged. Worker stops retry loop to prevent resource leaks.

---

## 5. Security & Credential Protection

- Plaintext RTSP credentials inside `configs/cameras.yaml` are strictly avoided. Sources support environment expansion: `rtsp://${CAMERA_USERNAME}:${CAMERA_PASSWORD}@192.168.1.104:554/stream1`.
- The `mask_camera_source()` function masks all passwords before logging or exposing status payloads:
  - Input: `rtsp://admin:SecretPass123@10.0.0.1:554/ch0`
  - Safe Output: `rtsp://admin:********@10.0.0.1:554/ch0`

---

## 6. Real-World Validation Disclosure

In accordance with Phase 10 global deployment rules:
- **Synthetic Cameras (`synthetic://...`)**: **VERIFIED**. Frame generation, rolling FPS, and simulated moving targets verified without physical hardware.
- **Local Webcam / Device Index 0 (`usb`)**: **VERIFIED**. Direct OpenCV device acquisition verified.
- **Video File Ingestion (`file`)**: **VERIFIED**. MP4 test files stream through workers with frame rate control.
- **Physical Industrial CCTV / Remote IP RTSP Streams**: **NOT TESTED**. Physical enterprise RTSP hardware was unavailable in the current test environment. Software architecture, backoff, and isolation logic are verified using simulated/synthetic network faults.
