# RAKSHYA VISION — Project Status

## Project Overview
- **Project Name:** RAKSHYA VISION
- **Tagline:** AI Vision-Based Safety Monitoring
- **Current Phase:** Phase 4 — Real-Time / Video Detection (COMPLETED & VERIFIED)

---

## 1. Phase 1 Foundation Status
- **Backend:** Operational (FastAPI + SQLAlchemy + SQLite, pytest 23/23 passing).
- **Frontend:** Built and operational (React 18 + TypeScript + Vite, live health connection).
- **Git:** Version control maintained with structured commits.

---

## 2. Phase 2 Dataset Pipeline Status

### Raw Dataset Preservation (`datasets/raw/`)
All raw datasets were downloaded, checksummed, and preserved untouched:
1. **`construction_ppe/`**: 1,124 images (hat, vest, no-hat, no-vest).
2. **`hard_hat_workers/`**: 7,035 images (helmet, head, person). SHA-256: `131b731c7391b71d9b0ece1798b1143a717fcef07f8d3e511008cc6dcfe3c5b1`.
3. **`ppe_detection_compliance/`**: 9,663 images (Boots, Gloves, Goggles, Helmet, Mask, Person, Vest, and absence classes). SHA-256: `806cda2009852f3f7736b14f01e689158fa7053b0a6782728ce057c765b45855`.
4. **`d_fire/`**: Cloned official repository (`repo/`) + Fire & Smoke dataset (`fire_smoke/` with 4,631 images). SHA-256: `0ed3b4011469870ff8401445efccae9b4c3de3bef8c1a2c4898ee3e1379319ca`.
- **Total Raw Images:** 22,453 images across all 4 datasets.

### Processed Training-Ready Dataset (`datasets/processed/`)
- **Normalized Schema (0..6):**
  - `0: person`
  - `1: helmet`
  - `2: safety_vest`
  - `3: gloves`
  - `4: safety_footwear`
  - `5: fire`
  - `6: smoke`
- **Leakage-Safe Splitting:**
  - Near-duplicate and exact-duplicate images clustered into groups before splitting.
  - **Train Split (70%):** 15,717 images
  - **Validation Split (20%):** 4,490 images
  - **Test Split (10%):** 2,246 images
  - **Total Processed Images:** 22,453 images
- **YOLO Configuration:** [`datasets/processed/data.yaml`](./datasets/processed/data.yaml) generated and path-verified.

---

## 3. Phase 3 Model Training & Validation Status (COMPLETED)

### Experiment: `ppe_fire_smoke_v1`
- **Architecture:** Ultralytics YOLOv8n (nano), PyTorch 2.14.0+cpu
- **Execution Hardware:** 13th Gen Intel(R) Core(TM) i5-13420H (CPU-only, no discrete CUDA GPU)
- **Primary Checkpoint:** [`models/detection/ppe_fire_smoke_v1/weights/best.pt`](./models/detection/ppe_fire_smoke_v1/weights/best.pt)
- **Checkpoint SHA-256:** `e265d7978b8cdb8cb2e6620e92e8c66d09a04d98b52d9409c91e3ceeba0cd5bf`
- **Model Metadata:** [`models/detection/ppe_fire_smoke_v1/model_metadata.json`](./models/detection/ppe_fire_smoke_v1/model_metadata.json)

### Evaluation Metrics (Evaluated on held-out splits, conf=0.25)
| Split | Precision | Recall | mAP@50 | mAP@50-95 | Top Detected Class |
|---|---|---|---|---|---|
| **Validation (4,490 images)** | **23.41%** | **11.28%** | **7.15%** | **2.17%** | `helmet` (22.10%), `smoke` (17.87%) |
| **Test (2,246 images)** | **22.68%** | **11.59%** | **6.98%** | **2.06%** | `helmet` (22.24%), `smoke` (13.83%), `fire` (11.06%) |

---

## 4. Phase 4 Real-Time / Video Detection Status (COMPLETED)

### Core Inference Pipeline
- **Model Integration:** Verified Phase 3 checkpoint `ppe_fire_smoke_v1/weights/best.pt` with SHA-256 verification.
- **Inference Engine:** `backend/app/ai/detection/` modular architecture (Singleton ModelLoader, Detector, FrameProcessor, VideoProcessor).
- **Execution Hardware:** Intel Core i5-13420H CPU (8 PyTorch threads pinned; no CUDA GPU).
- **Classes Detected:** 7 canonical classes (`person`, `helmet`, `safety_vest`, `gloves`, `safety_footwear`, `fire`, `smoke`).

### Video Ingestion Sources
1. **Uploaded Video Files**: CLI `scripts/inference/process_video.py` and API `POST /api/detection/video`. Processed sample video (120 frames, 88 detections) saved to `outputs/detection/videos/test_safety_detected.mp4`.
2. **Local Webcam**: Verified live webcam stream (Index 0, 1280x720) via `scripts/inference/run_webcam.py` with graceful stop handling.
3. **RTSP Streams**: Network camera client `scripts/inference/run_rtsp.py` with URL credential masking and bounded exponential backoff reconnection.

### Performance Benchmarks (Quantitative)
- **Input Stream FPS:** 15.0 FPS
- **Overall System FPS:** 16.04 FPS
- **Raw Inference FPS:** 16.96 FPS
- **Median Latency:** 32.89 ms (~30.4 FPS steady-state)
- **Min Latency:** 28.33 ms (~35.3 FPS peak)
- **Mean Latency:** 58.95 ms

### REST API Integration
- `GET /api/detection/health`: Model status, device, class names
- `POST /api/detection/image`: Single image inference with optional base64 visualization overlay
- `POST /api/detection/video`: Asynchronous video file processing

### Automated Tests
- **Backend Test Suite:** 23 / 23 tests PASSED (100%) in 7.47s (`backend/tests/test_detection.py`, `backend/tests/test_main.py`).

---

## 5. Strict Phase Boundaries & Next Phase Readiness
- [x] Phase 4 completed and verified end-to-end.
- [x] No tracking logic (ByteTrack/DeepSORT) implemented.
- [x] No worker-to-PPE association or compliance rules implemented.
- [x] No alert dispatch engine or live WebSocket notifications implemented.
- [x] Strictly stopped at end of Phase 4 awaiting user approval for Phase 5.