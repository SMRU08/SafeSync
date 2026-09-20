# RAKSHYA VISION — Project Status

## Project Overview
- **Project Name:** RAKSHYA VISION
- **Tagline:** AI Vision-Based Safety Monitoring
- **Current Phase:** Phase 3.1 — Model Diagnosis, Correction & Retraining (COMPLETED & VERIFIED)

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
- **Normalized Schema (0..6):** `0: person`, `1: helmet`, `2: safety_vest`, `3: gloves`, `4: safety_footwear`, `5: fire`, `6: smoke`
- **Total Processed Images:** 22,453 images (Train: 15,717, Val: 4,490, Test: 2,246)
- **Total Annotations:** 51,195 verified clean bounding boxes (0 out-of-bounds, 0 malformed lines, 0 invalid IDs).
- **Leakage-Safe:** 0 exact name overlaps between train, val, and test splits.

---

## 3. Phase 3 Baseline Model Status (`ppe_fire_smoke_v1`)
- **Architecture:** Ultralytics YOLOv8n (nano), PyTorch 2.14.0+cpu
- **Checkpoint:** [`models/detection/ppe_fire_smoke_v1/weights/best.pt`](./models/detection/ppe_fire_smoke_v1/weights/best.pt)
- **Checkpoint SHA-256:** `e265d7978b8cdb8cb2e6620e92e8c66d09a04d98b52d9409c91e3ceeba0cd5bf`
- **Measured Metrics (Test Split, conf=0.25):**
  - Precision: 22.68% | Recall: 11.59% | mAP@50: 6.98% | mAP@50-95: 2.06%
  - Non-functional classes (0.00% mAP): `person`, `gloves`, `safety_footwear`

---

## 4. Phase 3.1 Diagnosis, Correction & Retraining Status (COMPLETED)

### Root Causes Discovered
1. **RC-01 (CRITICAL - Dataset Prefix Slicing)**: In `ultralytics.data.dataset.YOLODataset.get_img_files`, `fraction=0.25` slices sorted filenames. Because paths had dataset prefixes (`cppe_`, `fs_`, `hhw_`, `ppec_`), the first 25% contained ONLY `cppe_` and `fs_`. The model was exposed to **0 instances of person, gloves, and footwear during v1 training**.
2. **RC-02 (CRITICAL - Training Under-convergence)**: 1 epoch on 25% data was only 245 steps. The model terminated before warmup finished (`val/cls_loss` = 12.27).

### Remediation & Controlled Training (`ppe_fire_smoke_v2`)
- **Balanced Manifest**: 5,418 images with 100% of available rare PPE classes (`datasets/processed/train_balanced.txt`).
- **Warmup & Optimization**: 2 full epochs (676 batches), warmup completed at batch 169.
- **Tuned Hyperparameters**: `cls: 1.0` (doubled classification loss weight), `box: 7.5`, `imgsz: 384`.
- **Primary Checkpoint**: [`models/detection/ppe_fire_smoke_v2/weights/best.pt`](./models/detection/ppe_fire_smoke_v2/weights/best.pt)
- **Checkpoint SHA-256:** `490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3`

### Measured Verification Results (Held-out Test Split: 2,246 images)
| Metric | V1 Baseline | V2 Improved | Delta |
|---|---|---|---|
| **Precision** | 22.68% | **37.60%** | **+14.92%** |
| **Recall** | 11.59% | **37.44%** | **+25.85% (3.23×)** |
| **mAP@50** | 6.98% | **25.23%** | **+18.25% (3.61×)** |
| **mAP@50-95** | 2.06% | **12.03%** | **+9.97% (5.84×)** |

### Per-Class Test Split Improvements
- `person`: 0.00% $\rightarrow$ **22.64% mAP50** (50.00% recall)
- `helmet`: 22.24% $\rightarrow$ **72.84% mAP50** (81.09% recall)
- `safety_vest`: 1.74% $\rightarrow$ **28.89% mAP50** (50.88% recall)
- `gloves`: 0.00% $\rightarrow$ **9.15% mAP50** (16.13% recall)
- `safety_footwear`: 0.00% $\rightarrow$ **0.34% mAP50** (test) / **4.78% mAP50** (val)
- `fire`: 11.06% $\rightarrow$ **20.15% mAP50** (30.62% recall)
- `smoke`: 13.83% $\rightarrow$ **22.62% mAP50** (30.48% recall)

### Inference Latency Benchmark (Intel Core i5-13420H CPU)
- **Median Latency:** **40.36 ms** (~24.8 FPS)
- **Mean Latency:** **52.04 ms** (19.2 FPS)
- **Min Latency:** **29.53 ms** (~33.9 FPS)

---

## 5. Automated Test Suite
- Full test suite passing: `pytest backend/tests -v` (23/23 tests passed).

---

## 6. Strict Phase Boundaries
- [x] Phase 3.1 completed and fully verified.
- [x] Baseline V1 preserved untouched.
- [x] Raw datasets in `datasets/raw/` untouched.
- [x] No fabricated or simulated metrics.
- [x] Stopped at end of Phase 3.1 awaiting explicit user approval.