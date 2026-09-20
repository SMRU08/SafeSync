# RAKSHYA VISION — Model Registry

This registry tracks all trained models, checkpoints, performance benchmarks, and deployment artifacts across the project lifecycle.

---

## Active Models

| Model ID | Task | Architecture | Framework | Classes | Target Hardware | Primary Checkpoint | Status | SHA-256 |
|---|---|---|---|---|---|---|---|---|
| `ppe_fire_smoke_v2` | Multi-Class Object Detection | YOLOv8n (nano) | Ultralytics 8.4.156 / PyTorch 2.14.0 | 7 canonical classes | Edge / CPU / GPU | `models/detection/ppe_fire_smoke_v2/weights/best.pt` | **Validated Candidate (Phase 3.1)** | `490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3` |
| `ppe_fire_smoke_v1` | Multi-Class Object Detection | YOLOv8n (nano) | Ultralytics 8.4.156 / PyTorch 2.14.0 | 7 canonical classes | Edge / CPU / GPU | `models/detection/ppe_fire_smoke_v1/weights/best.pt` | Preserved (Phase 3 Baseline) | `e265d7978b8cdb8cb2e6620e92e8c66d09a04d98b52d9409c91e3ceeba0cd5bf` |

---

## Canonical Class Schema (0..6)

| ID | Class Name | Category | Description |
|---|---|---|---|
| 0 | `person` | Subject | Human worker / occupant in monitored area |
| 1 | `helmet` | Head PPE | Hard hat or protective safety helmet |
| 2 | `safety_vest` | Torso PPE | High-visibility reflective safety vest |
| 3 | `gloves` | Hand PPE | Industrial protective gloves |
| 4 | `safety_footwear` | Foot PPE | Steel-toe boots / protective work footwear |
| 5 | `fire` | Hazard | Active open flame or combustion |
| 6 | `smoke` | Hazard | Airborne smoke plume or particulate cloud |

*Note: Absence classes (`no_helmet`, `no_vest`, etc.) are derived downstream via person-PPE spatial association.*

---

## Experiment History

### `ppe_fire_smoke_v2` (Phase 3.1 Controlled Improvement)
- **Objective:** Fix root causes RC-01 (prefix slicing in fraction=0.25) and RC-02 (under-convergence). Train with balanced 7-class representation.
- **Training Set:** 5,418 balanced images (`datasets/processed/train_balanced.txt`)
- **Validation Set:** 4,490 images (`datasets/processed/images/val`)
- **Test Set:** 2,246 images (`datasets/processed/images/test`)
- **Hyperparameters:** YOLOv8n, imgsz=384, fraction=1.0, batch=16, epochs=2 (676 batches), cls=1.0, box=7.5, warmup_epochs=0.5
- **Duration:** 2,998 seconds (~50.0 minutes)
- **Directory:** [`models/detection/ppe_fire_smoke_v2/`](./detection/ppe_fire_smoke_v2/)
- **Checkpoint SHA-256:** `490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3`
- **Performance Summary:**
  - **Validation Set:** Precision: 38.30%, Recall: 38.05%, mAP@50: **25.12%**, mAP@50-95: **11.87%**
  - **Test Set:** Precision: 37.60%, Recall: 37.44%, mAP@50: **25.23%**, mAP@50-95: **12.03%**
  - **Per-Class Test mAP@50:**
    - `person`: **22.64%** (Recall: 50.00%, Precision: 30.28%)
    - `helmet`: **72.84%** (Recall: 81.09%, Precision: 60.75%)
    - `safety_vest`: **28.89%** (Recall: 50.88%, Precision: 31.45%)
    - `gloves`: **9.15%** (Recall: 16.13%, Precision: 34.78%)
    - `safety_footwear`: **0.34%** (Recall: 2.92%, Precision: 6.19%)
    - `fire`: **20.15%** (Recall: 30.62%, Precision: 41.99%)
    - `smoke`: **22.62%** (Recall: 30.48%, Precision: 57.74%)
- **Inference Latency (Intel Core i5-13420H CPU):**
  - Mean Latency: **52.04 ms**
  - Median Latency: **40.36 ms** (~24.8 FPS)
  - Min Latency: **29.53 ms** (~33.9 FPS)
  - Throughput: **19.2 - 24.8 FPS**
- **Artifacts:**
  - Checkpoints: `weights/best.pt`, `weights/last.pt`
  - Checksum: `model.sha256`
  - Metadata: `model_metadata.json`
  - Evaluation: `MODEL_EVALUATION_REPORT.md`, `evaluation_metrics.json`
  - Error Analysis: `error_analysis.md`
  - Confidence Thresholds: `confidence_analysis.csv`
  - Latency Benchmark: `benchmark_results.json`
  - Visual Samples: `validation_samples/`

---

### `ppe_fire_smoke_v1` (Phase 3 Baseline)
- **Objective:** Train baseline 7-class safety detector on normalized multi-source dataset.
- **Training Set:** 15,717 images (`datasets/processed/images/train`)
- **Validation Set:** 4,490 images (`datasets/processed/images/val`)
- **Test Set:** 2,246 images (`datasets/processed/images/test`)
- **Hyperparameters:** YOLOv8n, imgsz=384, fraction=0.25, batch=16, epochs=1 (CPU baseline), workers=0
- **Duration:** 887 seconds (~14.8 minutes)
- **Directory:** [`models/detection/ppe_fire_smoke_v1/`](./detection/ppe_fire_smoke_v1/)
- **Checkpoint SHA-256:** `e265d7978b8cdb8cb2e6620e92e8c66d09a04d98b52d9409c91e3ceeba0cd5bf`
- **Performance Summary:**
  - **Validation Set:** Precision: 23.41%, Recall: 11.28%, mAP@50: 7.15%, mAP@50-95: 2.17%
  - **Test Set:** Precision: 22.68%, Recall: 11.59%, mAP@50: 6.98%, mAP@50-95: 2.06%
- **Inference Latency (Intel Core i5-13420H CPU):**
  - Mean Latency: **32.89 ms**
  - Median Latency: **33.18 ms**
  - Throughput: **30.4 FPS**
