# RAKSHYA VISION — Model Registry

This registry tracks all trained models, checkpoints, performance benchmarks, and deployment artifacts across the project lifecycle.

---

## Active Models

| Model ID | Task | Architecture | Framework | Classes | Target Hardware | Primary Checkpoint | Status | SHA-256 |
|---|---|---|---|---|---|---|---|---|
| `ppe_fire_smoke_v1` | Multi-Class Object Detection | YOLOv8n (nano) | Ultralytics 8.4.156 / PyTorch 2.14.0 | 7 canonical classes | Edge / CPU / GPU | `models/detection/ppe_fire_smoke_v1/weights/best.pt` | **Validated** (Baseline) | `e265d7978b8cdb8cb2e6620e92e8c66d09a04d98b52d9409c91e3ceeba0cd5bf` |

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

*Note: Absence classes (`no_helmet`, `no_vest`, etc.) are derived downstream in Phase 4 via person-PPE spatial association.*

---

## Experiment History

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
  - **Top Class:** `helmet` (mAP@50: 22.24% on test), `smoke` (mAP@50: 13.83%), `fire` (mAP@50: 11.06%)
- **Inference Latency (Intel Core i5-13420H CPU):**
  - Mean Latency: **32.89 ms**
  - Median Latency: **33.18 ms**
  - Throughput: **30.4 FPS** (Real-time capability confirmed)
- **Artifacts:**
  - Checkpoints: `weights/best.pt`, `weights/last.pt`
  - Checksum: `model.sha256`
  - Metadata: `model_metadata.json`
  - Evaluation: `MODEL_EVALUATION_REPORT.md`, `evaluation_metrics.json`
  - Error Analysis: `error_analysis.md`
  - Confidence Thresholds: `confidence_analysis.csv`
  - Latency Benchmark: `benchmark_results.json`
  - Visual Samples: `validation_samples/` (20 annotated sample predictions)
