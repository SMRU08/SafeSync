# Troubleshooting Guide

This guide details resolutions for common operational, hardware, and configuration issues encountered when running RAKSHYA VISION.

---

## 1. Camera & Video Ingestion Issues

### 1.1 Local Laptop / USB Webcam Fails to Open
- **Symptom:** `CameraWorker` logs `Cannot open capture for camera_01 (source=0)`.
- **Causes & Solutions:**
  1. *Windows Privacy Settings:* Go to *Settings > Privacy & Security > Camera* and enable *"Allow desktop apps to access your camera"*.
  2. *Device Index Conflict:* Another software (e.g. Teams, Zoom, browser) is holding an exclusive handle to webcam index 0. Close contending applications or test index `1` in `configs/cameras.yaml`.
  3. *Linux Permissions:* Ensure the executing user belongs to the `video` group:
     ```bash
     sudo usermod -aG video $USER
     ```

### 1.2 RTSP Stream Frequently Reconnects
- **Symptom:** Worker transitions continuously between `CONNECTED` and `RECONNECTING`.
- **Causes & Solutions:**
  1. *RTSP Transport Protocol:* By default, OpenCV uses UDP for RTSP, which suffers packet loss on congested Wi-Fi. Force TCP transport in environment variables:
     ```bash
     export OPENCV_FFMPEG_CAPTURE_OPTIONS="rtsp_transport;tcp"
     ```
  2. *Camera Bitrate Too High:* Reduce the IP camera's sub-stream bitrate to 1080p @ 15–20 FPS or 720p @ 25 FPS for edge analytics.

---

## 2. AI Model & Inference Issues

### 2.1 ModelCorruptedError on Startup
- **Symptom:** Application fails with `ModelCorruptedError: Checksum mismatch for ppe_fire_smoke_v2`.
- **Cause:** The weights file `models/detection/ppe_fire_smoke_v2/weights/best.pt` was partially downloaded or modified.
- **Solution:**
  Recompute the local checksum and compare against `models/registry/model_registry.yaml`:
  ```bash
  python -c "import hashlib; print(hashlib.sha256(open('models/detection/ppe_fire_smoke_v2/weights/best.pt', 'rb').read()).hexdigest())"
  # Must equal: 490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3
  ```

### 2.2 Slow Frame Rates / High CPU Usage
- **Symptom:** Dashboard shows inference latency > 80 ms, effective FPS drops below 10.
- **Solutions:**
  1. Ensure `infer_interval_frames = 2` is enabled in `CameraWorker` (processes every second frame while maintaining smooth capture).
  2. If an NVIDIA GPU is available, install the matching PyTorch CUDA build:
     ```bash
     pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
     ```

---

## 3. Database & Persistence Issues

### 3.1 `database is locked` Error
- **Symptom:** SQLite raises `OperationalError: database is locked`.
- **Cause:** Multiple concurrent writers without WAL mode enabled, or long-running transactions.
- **Solution:**
  Verify WAL mode is active via the health endpoint:
  ```bash
  curl http://localhost:8000/health/database
  # "journal_mode" should report "wal", and "busy_timeout" should be 5000.
  ```

---

## 4. Frontend & WebSocket Issues

### 4.1 WebSocket Fails to Connect
- **Symptom:** Dashboard displays red `WS DISCONNECTED` status badge.
- **Solutions:**
  1. *Authentication Enabled:* If `AUTH_ENABLED=True` is set in the backend, the WebSocket requires a valid JWT token query param: `ws://localhost:8000/ws/alerts?token=<jwt>`.
  2. *Reverse Proxy Timeout:* When running behind Nginx, ensure `proxy_read_timeout 86400s;` is set in the `/ws/` block to prevent Nginx from dropping idle connections.
