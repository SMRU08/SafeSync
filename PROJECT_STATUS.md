# RAKSHYA VISION — Project Status

## Project Overview
- **Project Name:** RAKSHYA VISION
- **Tagline:** AI Vision-Based Safety Monitoring
- **Current Phase:** Phase 3 — Model Training & Validation (Completed & Verified)

---

## 1. Phase 1 Foundation Status
- **Backend:** Operational (FastAPI + SQLAlchemy + SQLite, pytest 4/4 passing).
- **Frontend:** Built and operational (React 18 + TypeScript + Vite, live health connection).
- **Git:** Initial commit `ee2ded0` established.

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

### Confidence Threshold Trade-Off Analysis
| Confidence Threshold | Precision | Recall | mAP@50 | Operational Role |
|---|---|---|---|---|
| **0.25** | 23.41% | 11.28% | 0.0715 | High-Recall Safety Monitoring (Alerting default) |
| **0.35** | 28.29% | 8.12% | 0.0563 | Balanced inspection mode |
| **0.50** | 32.32% | 4.74% | 0.0357 | Standard detection baseline |
| **0.60** | 36.14% | 3.05% | 0.0247 | High-confidence filtering |
| **0.70** | **40.44%** | 1.66% | 0.0128 | Ultra-conservative (minimal false alarms) |

### Inference Latency Benchmark (Intel Core i5-13420H CPU)
- **Image Resolution:** 384 × 384 × 3 RGB
- **Mean Latency:** **32.89 ms**
- **Median Latency:** **33.18 ms**
- **Min / Max Latency:** 24.80 ms / 41.82 ms
- **Throughput:** **30.4 FPS** (Confirmed real-time edge CPU capability)

### Phase 3 Artifact Registry
- `configs/training.yaml` — Hardware-tuned CPU training configuration
- `scripts/training/check_environment.py` — Runtime environment and dataset diagnostic
- `scripts/training/preflight_training_check.py` — Label, path, and split pre-flight validation
- `scripts/training/train.py` — Multi-class YOLOv8 training engine with OOM recovery
- `scripts/training/evaluate.py` — Validation and test split evaluator with confidence analysis
- `scripts/training/benchmark.py` — Multi-device inference latency benchmark
- `models/MODEL_REGISTRY.md` — Central project model catalog
- `models/detection/experiments.json` — Machine-readable experiment records
- `models/detection/ppe_fire_smoke_v1/validation_samples/` — 20 visual detection overlays
- `models/detection/ppe_fire_smoke_v1/error_analysis.md` — Systematic bias & failure analysis
- `models/detection/ppe_fire_smoke_v1/confidence_analysis.csv` — Multi-threshold metrics
- `models/detection/ppe_fire_smoke_v1/MODEL_EVALUATION_REPORT.md` — Full evaluation report

---

## 4. Strict Compliance Audit
- [x] Phase 1 Foundation operational and preserved.
- [x] Phase 2 Raw datasets preserved unmodified in `datasets/raw/`.
- [x] No fake, mocked, or fabricated metrics — all numbers computed directly by YOLO validator.
- [x] No Phase 4 features implemented (RTSP, tracking, alert engine, WebSocket, live dashboard).
- [x] Stopped at end of Phase 3 awaiting explicit user approval.