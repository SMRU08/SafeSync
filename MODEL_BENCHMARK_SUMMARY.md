# SAFESYNC — MODEL BENCHMARK & COMPARISON MASTER SUMMARY

> **Official Benchmark Report:** Full empirical evaluation across all existing trained model checkpoints in the SafeSync repository on the common held-out test dataset (`datasets/processed_v3/data_v3.yaml`).

---

## 1. EXECUTIVE SUMMARY

* **Evaluation Scope:** All 9 discovered model checkpoints across production, shadow, experimental, legacy, and specialist categories were benchmarked on the identical 410-image, 1,235-annotation test suite.
* **Production Safety Status:** 
  * Production V3 Model (`models/detection/ppe_fire_smoke_v3/weights/best.pt`): **UNTOUCHED & UNMODIFIED** (SHA-256: `9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe`)
  * Shadow V6 Model (`models/detection/safesync_v6_hardnegative/weights/best.pt`): **UNTOUCHED & UNMODIFIED** (SHA-256: `c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc`)
* **Final Verdict:** **KEEP EXISTING SINGLE PRODUCTION MODEL (V3)**. Multi-model pipelines increase inference latency by ~100% on CPU and introduce massive false positives (e.g. 31,012 FPs from hazard specialist without distractor training), making the unified V3 model the optimal choice for real-time edge CPU performance.

---

## 2. COMPREHENSIVE MODEL INVENTORY

| Model | Status | Framework | File Size | Classes | SHA-256 |
|---|---|---|---|---|---|
| **`ppe_fire_smoke_v3`** | **Production** | Ultralytics YOLOv8n | 5.92 MB | 7 classes | `9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe` |
| **`safesync_v6_hardnegative`**| **Shadow** | Ultralytics YOLOv8n | 5.92 MB | 7 classes | `c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc` |
| **`safesync_v5_unified`** | Experimental | Ultralytics YOLOv8n | 5.92 MB | 7 classes | `b2e554beb39d1b6da5c6f600490bba1315904d9c7daaf0a9d8ba2167d4c8a44b` |
| **`ppe_fire_smoke_v4`** | Experimental | Ultralytics YOLOv8n | 5.92 MB | 7 classes | `6c6e564a0702cff82255866ee15d9da6c5d1ae62c162cf5ef9fbefc9751c0313` |
| **`ppe_fire_smoke_v2`** | Legacy | Ultralytics YOLOv8n | 5.92 MB | 7 classes | `490a4867d0c9f137eb1ca4fc00438316c02111d4d6ee1cb1e780447fa484b2f3` |
| **`ppe_fire_smoke_v1`** | Legacy | Ultralytics YOLOv8n | 5.92 MB | 7 classes | `e265d7978b8cfeb7fe2269a941ca72d42bfbe86d26da59d9ec168bf1400cd5bf` |
| **`construction_ppe_v1`** | Experimental | Ultralytics YOLOv8n | 5.93 MB | 7 classes | `213211bc55aebff17a151b72a445d4a9ec7fcf5d96a29d6be47e62a1ea086462` |
| **`fire_smoke_candidate_v2`**| Specialist | Ultralytics YOLOv8n | 5.92 MB | 2 classes (`fire`, `smoke`) | `8b4034368a9010aa2bfbaee3cf700949d604b90e9dfbc1230e9d1078a6832e13` |
| **`safesync_glove_detector`**| Specialist | Ultralytics YOLOv8n | 5.92 MB | 1 class (`gloves`) | `b33582154bd19eb64d7df63f25c796ae7d5fa7bb2a4a75e3a95bf0fa571397b8` |

---

## 3. OVERALL EVALUATION RESULTS (HELD-OUT TEST SET)

Evaluated on **410 test images** containing **1,235 ground-truth objects** (`datasets/processed_v3/data_v3.yaml`):

| Model Name | Precision | Recall | mAP50 | mAP50-95 | True Positives | False Positives | False Negatives |
|---|---|---|---|---|---|---|---|
| **V3 (Production)** | **0.3877** | **0.4681** | **0.3785** | **0.1595** | **645** | **754** | **590** |
| **V4 (Experimental)** | 0.3902 | 0.4518 | 0.3995 | 0.2198 | 620 | 436 | 615 |
| **V6 (Shadow/HardNeg)** | 0.3366 | 0.3450 | 0.2612 | 0.1200 | 535 | 952 | 700 |
| **Construction PPE V1** | 0.5463 | 0.2799 | 0.2223 | 0.0954 | 526 | 1269 | 709 |
| **V2 (Legacy)** | 0.2208 | 0.3071 | 0.1842 | 0.0690 | 364 | 935 | 871 |
| **V5 (Unified)** | 0.2592 | 0.2300 | 0.1415 | 0.0538 | 257 | 1518 | 978 |
| **V1 (Legacy)** | 0.4010 | 0.1620 | 0.0843 | 0.0301 | 122 | 395 | 1113 |
| **Fire/Smoke Specialist V2**| 0.0014 | 0.2195 | 0.0000 | 0.0000 | 45 | 31046 | 160 |
| **Glove Specialist V1** | 0.0240 | 0.1690 | 0.0000 | 0.0000 | 12 | 489 | 59 |

---

## 4. CLASS-WISE WINNER BREAKDOWN

| Class | Winner Model | Precision | Recall | mAP50 | False Negatives | Selection Rationale |
|---|---|---|---|---|---|---|
| **Person** | **V4 (Experimental)** | 0.3804 | **0.7500** | **0.4815** | 86 | Highest recall across diverse worker poses |
| **Helmet** | **V3 (Production)** | 0.4611 | **0.7491** | **0.6308** | 79 | Outstanding headwear recall & tight IoU localization |
| **Safety Vest** | **V4 (Experimental)** | 0.6553 | **0.8424** | **0.8180** | 59 | Best high-visibility thoracic coverage |
| **Gloves** | **V6 (Shadow)** | 0.0592 | **0.2113** | **0.0254** | 58 | Highest glove recall among full-ontology models |
| **Safety Footwear**| **V3 (Production)** | 0.3199 | **0.4483** | **0.2604** | 102 | Reliable lower-limb detection (nearly 2x next best) |
| **Fire** | **V4 (Experimental)** | 0.4157 | **0.2929** | **0.2529** | 81 | Highest flame recall (V3 highest precision: 0.5221) |
| **Smoke** | **V3 (Production)** | **0.4790** | **0.3396** | **0.3126** | 80 | Highest smoke plume mAP & strong precision (0.4790) |

---

## 5. HARDWARE SPEED & THROUGHPUT (CPU)

Measured on Intel Core i5 CPU across 30 timed iterations on sample test images:

| Model | Image Size | Mean Latency (ms) | P50 Median (ms) | P95 (ms) | Throughput (FPS) |
|---|---|---|---|---|---|
| **V3 (Production)** | **384×384** | **36.12 ms** | **34.73 ms** | **45.32 ms** | **27.7 FPS** |
| **V3 (Production)** | **640×640** | **67.01 ms** | **57.21 ms** | **101.78 ms** | **14.9 FPS** |
| **V6 (Shadow)** | 384×384 | 81.47 ms | 66.15 ms | 156.29 ms | 12.3 FPS |
| **V6 (Shadow)** | 640×640 | 62.11 ms | 60.74 ms | 72.45 ms | 16.1 FPS |
| **V4 (Experimental)** | 384×384 | 34.38 ms | 33.89 ms | 40.62 ms | 29.1 FPS |
| **V4 (Experimental)** | 640×640 | 129.75 ms | 116.30 ms | 242.61 ms | 7.7 FPS |
| **Multi-Model Pipeline (V3 + Hazard)** | 384×384 | 70.31 ms | 68.32 ms | 87.39 ms | 14.2 FPS |
| **Multi-Model Pipeline (V3 + Hazard)** | 640×640 | 125.35 ms | 115.21 ms | 164.19 ms | 8.0 FPS |

---

## 6. GENERATED BENCHMARK ARTIFACTS

All detailed CSV and Markdown reports are persisted in `reports/model_benchmark/`:
1. `reports/model_benchmark/model_inventory.csv`
2. `reports/model_benchmark/overall_results.csv`
3. `reports/model_benchmark/class_wise_results.csv`
4. `reports/model_benchmark/false_negative_analysis.csv`
5. `reports/model_benchmark/speed_results.csv`
6. `reports/model_benchmark/real_world_results.csv`
7. `reports/model_benchmark/combination_analysis.md`
8. `reports/model_benchmark/final_recommendation.md`
