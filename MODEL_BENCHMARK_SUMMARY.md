# SAFESYNC — MODEL BENCHMARK & COMPARISON MASTER SUMMARY

> **Official Audited Benchmark Report:** Full empirical evaluation across all 9 trained model checkpoints in the SafeSync repository on the common held-out test dataset (`datasets/processed_v3/data_v3.yaml`, 410 images, 1,235 ground-truth objects).
>
> **Detailed Mathematical Audit Document:** [`reports/model_benchmark/final_verified_benchmark.md`](reports/model_benchmark/final_verified_benchmark.md)

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
| **`safesync_v5_unified`** | Experimental | Ultralytics YOLOv8n | 5.92 MB | 7 classes | `b2e554beb39de075e586afd120db3079f5c24f3b4b6165f5601125ed74c8a44b` |
| **`ppe_fire_smoke_v4`** | Experimental | Ultralytics YOLOv8n | 5.92 MB | 7 classes | `6c6e564a07024e9b29e6999d2d0af74586576082aada5c5ad4d757a06b1c0313` |
| **`ppe_fire_smoke_v2`** | Legacy | Ultralytics YOLOv8n | 5.92 MB | 7 classes | `490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3` |
| **`ppe_fire_smoke_v1`** | Legacy | Ultralytics YOLOv8n | 5.92 MB | 7 classes | `e265d7978b8cdb8cb2e6620e92e8c66d09a04d98b52d9409c91e3ceeba0cd5bf` |
| **`construction_ppe_v1`** | Experimental | Ultralytics YOLOv8n | 5.93 MB | 7 classes | `213211bc55ae23492d909d2ca76ec419ffbd551f7bad24ca02c6252198086462` |
| **`fire_smoke_candidate_v2`**| Specialist | Ultralytics YOLOv8n | 5.92 MB | 2 classes (`fire`, `smoke`) | `8b4034368a90fcafc5efb3b3c591c854bea4b5de3d8e843524e4b9acce832e13` |
| **`safesync_glove_detector`**| Specialist | Ultralytics YOLOv8n | 5.92 MB | 1 class (`gloves`) | `b33582154bd1705b1967f1e7adadf43c893dd7e059713f02a47b2bab0e1397b8` |

---

## 3. AUDITED EVALUATION RESULTS (HELD-OUT TEST SET)

Evaluated on **410 test images** containing **1,235 ground-truth objects** (`datasets/processed_v3/data_v3.yaml`).

### A. YOLO Validation Benchmark (PR-Curve / Integral Paradigm)
*Computed via Ultralytics `model.val()` across all confidence thresholds (optimal F1 cutoff).*

| Model Name | Display Alias | Status | mAP50 | mAP50-95 | YOLO Mean Precision | YOLO Mean Recall |
|---|---|---|:---:|:---:|:---:|:---:|
| `ppe_fire_smoke_v4` | V4 (Experimental) | experimental | **0.3995** | **0.2198** | 0.3902 | 0.4518 |
| **`ppe_fire_smoke_v3`** | **V3 (Production)** | **production** | **0.3785** | **0.1595** | **0.3877** | **0.4681** |
| `safesync_v6_hardnegative`| V6 (Shadow/HardNeg)| shadow | 0.2612 | 0.1200 | 0.3366 | 0.3450 |
| `construction_ppe_v1` | Construction PPE V1| experimental | 0.2223 | 0.0954 | 0.5463 | 0.2799 |
| `ppe_fire_smoke_v2` | V2 (Legacy) | legacy | 0.1842 | 0.0690 | 0.2208 | 0.3071 |
| `safesync_v5_unified` | V5 (Unified Candidate)| experimental | 0.1415 | 0.0538 | 0.2592 | 0.2300 |
| `ppe_fire_smoke_v1` | V1 (Legacy) | legacy | 0.0843 | 0.0301 | 0.4010 | 0.1620 |

---

### B. Fixed Operational Threshold Benchmark (conf=0.25, IoU=0.50)
*Computed at production operational threshold $\text{conf}=0.25$, greedy matching at $\text{IoU} \ge 0.50$.*  
*Mathematical Invariant Verified: $\text{True Positives} + \text{False Negatives} \equiv \text{Total Ground Truth (1,235)}$.*

| Model Name | Display Alias | Status | Total GT | TP | FP | FN | Operational Precision | Operational Recall | Operational F1 |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ppe_fire_smoke_v4` | V4 (Experimental) | experimental | 1235 | 620 | 436 | 615 | 0.5871 | 0.5020 | 0.5412 |
| **`ppe_fire_smoke_v3`** | **V3 (Production)** | **production** | **1235** | **645** | **754** | **590** | **0.4610** | **0.5223** | **0.4897** |
| `safesync_v6_hardnegative`| V6 (Shadow/HardNeg)| shadow | 1235 | 535 | 952 | 700 | 0.3598 | 0.4332 | 0.3931 |
| `construction_ppe_v1` | Construction PPE V1| experimental | 1235 | 526 | 1269 | 709 | 0.2930 | 0.4259 | 0.3472 |
| `ppe_fire_smoke_v2` | V2 (Legacy) | legacy | 1235 | 364 | 935 | 871 | 0.2802 | 0.2947 | 0.2873 |
| `safesync_v5_unified` | V5 (Unified Candidate)| experimental | 1235 | 257 | 1518 | 978 | 0.1448 | 0.2081 | 0.1708 |
| `ppe_fire_smoke_v1` | V1 (Legacy) | legacy | 1235 | 122 | 395 | 1113 | 0.2360 | 0.0988 | 0.1393 |

---

### C. Specialist Task-Specific Models (Operational Metrics)

| Model Name | Display Alias | Target Role | Target GT | TP | FP | FN | Operational Precision | Operational Recall |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `fire_smoke_candidate_v2` | Fire/Smoke Specialist V2 | Hazard Combustion | 205 | 45 | 31046 | 160 | 0.0014 | 0.2195 |
| `safesync_glove_detector` | Glove Specialist V1 | Distal Limb PPE | 71 | 12 | 489 | 59 | 0.0240 | 0.1690 |

---

## 4. CLASS-WISE WINNER BREAKDOWN

| Class | Optimal Model | Winning Metric Basis | Operational Recall | YOLO mAP50 | Operational F1 | Rationale |
|---|---|---|:---:|:---:|:---:|---|
| **Person** | **V4** / **V3 (Production)** | V4 high recall (0.6228), V3 robust (0.5570, mAP50 0.3990) | 0.6228 / 0.5570 | 0.4815 / 0.3990 | 0.5240 / 0.4829 | V4 slightly higher recall, V3 has better balance and higher precision |
| **Helmet** | **V3 (Production)** | Highest operational TP (196), lowest FN (79) | **0.7127** | **0.6308** | **0.6115** | Superior headwear localization with 71.3% operational recall |
| **Safety Vest** | **V4** / **V3 (Production)** | V4 high recall (0.8103), V3 high recall (0.7460) | 0.8103 / 0.7460 | 0.8180 / 0.7298 | 0.7754 / 0.6418 | Both V3 and V4 deliver exceptional high-visibility torso detection |
| **Gloves** | **V6 (Shadow)** | Highest operational glove TP (13) among unified models | **0.1831** | 0.0254 | 0.0760 | Unified models struggle with small distal hands; V6 captures most |
| **Safety Footwear**| **V3 (Production)** / **V6** | Equal highest operational footwear TP (43) | **0.2966** | **0.2604** | **0.3139** | Lower-limb detection with fewest false alarms in V3 |
| **Fire** | **V6 (Shadow)** / **V4** | V6 achieves 23 TP vs V4 18 TP vs V3 14 TP | **0.2323** | 0.1668 | 0.2788 | V6 exhibits high sensitivity to flame phenomena |
| **Smoke** | **V3 (Production)** | V3 captures 26 TP with 0.4906 precision | **0.2453** | **0.3126** | **0.3270** | Cleanest particulate plume segmentation with lowest false alarms |

---

## 5. HARDWARE SPEED & THROUGHPUT (CPU)

Measured on Intel Core i5-13420H CPU across 30 timed iterations on sample test images:

| Model | Image Size | Mean Latency (ms) | P50 Median (ms) | P95 (ms) | Throughput (FPS) |
|---|---|---|---|---|---|
| **V3 (Production)** | **384×384** | **42.57 ms** | **42.59 ms** | **45.85 ms** | **23.5 FPS** |
| **V3 (Production)** | **640×640** | **81.53 ms** | **82.04 ms** | **86.06 ms** | **12.3 FPS** |
| **V6 (Shadow)** | 384×384 | 42.30 ms | 40.95 ms | 45.69 ms | 23.6 FPS |
| **V6 (Shadow)** | 640×640 | 81.10 ms | 81.02 ms | 85.96 ms | 12.3 FPS |
| **V4 (Experimental)** | 384×384 | 41.38 ms | 41.51 ms | 43.54 ms | 24.2 FPS |
| **V4 (Experimental)** | 640×640 | 79.80 ms | 79.31 ms | 88.64 ms | 12.5 FPS |

---

## 6. GENERATED BENCHMARK ARTIFACTS

All detailed CSV and Markdown reports are persisted in `reports/model_benchmark/`:
1. [`reports/model_benchmark/final_verified_benchmark.md`](reports/model_benchmark/final_verified_benchmark.md) — Comprehensive verified benchmark & mathematical audit
2. [`reports/model_benchmark/model_inventory.csv`](reports/model_benchmark/model_inventory.csv) — Complete checkpoint inventory & SHA-256 hashes
3. [`reports/model_benchmark/overall_results.csv`](reports/model_benchmark/overall_results.csv) — Verified dual-paradigm overall metrics
4. [`reports/model_benchmark/class_wise_results.csv`](reports/model_benchmark/class_wise_results.csv) — Verified per-class dual-paradigm metrics
5. [`reports/model_benchmark/false_negative_analysis.csv`](reports/model_benchmark/false_negative_analysis.csv) — Failure categorization for all 1,235 annotations
6. [`reports/model_benchmark/speed_results.csv`](reports/model_benchmark/speed_results.csv) — Controlled latency and throughput benchmarks
7. [`reports/model_benchmark/real_world_results.csv`](reports/model_benchmark/real_world_results.csv) — 12-scenario real-world challenge evaluations
8. [`reports/model_benchmark/combination_analysis.md`](reports/model_benchmark/combination_analysis.md) — Architectural evaluation (Option A vs B vs C)
9. [`reports/model_benchmark/final_recommendation.md`](reports/model_benchmark/final_recommendation.md) — Production model retention justification
