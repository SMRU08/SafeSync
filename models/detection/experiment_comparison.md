# Experiment Comparison: `ppe_fire_smoke_v1` vs `ppe_fire_smoke_v2`
**Project:** SafeSync — AI Vision-Based Safety Monitoring  
**Phase:** Phase 3.1 — Model Diagnosis, Correction & Retraining  
**Date:** 2026-09-20  

---

## 1. Executive Summary & Controlled Parameters

This controlled experiment directly addresses the root causes diagnosed during Phase 3.1:
1. **RC-01 (Dataset Prefix Slicing)**: In v1, `fraction: 0.25` on sorted filenames caused Ultralytics to load only the first 25% of alphabetical paths (`cppe_` and `fs_`), resulting in literally 0 instances of `person`, `gloves`, and `safety_footwear`. In v2, a balanced manifest (`train_balanced.txt`) was used with `fraction: 1.0`, ensuring 100% representation for rare classes.
2. **RC-02 (Severe Under-convergence)**: In v1, 1 epoch with batch 16 was only 245 iterations and terminated during warmup. In v2, 2 full epochs on 5,418 images (676 batches) completed warmup at batch 169 and allowed classification head loss to drop.

| Parameter | V1 Baseline (`ppe_fire_smoke_v1`) | V2 Improved (`ppe_fire_smoke_v2`) | Rationale / Change |
|---|---|---|---|
| **Architecture** | `yolov8n.pt` (nano) | `yolov8n.pt` (nano) | Unchanged (controlled baseline) |
| **Model Size** | 6.2 MB (3.01M params) | 6.2 MB (3.01M params) | Unchanged |
| **Resolution** | 384 × 384 px | 384 × 384 px | Unchanged (edge CPU target) |
| **Batch Size** | 16 | 16 | Unchanged |
| **Device** | CPU (Intel Core i5-13420H) | CPU (Intel Core i5-13420H) | Unchanged |
| **Dataset Train Set** | Sliced 25% (3,929 images) | Balanced 5,418 images | All 7 classes represented |
| **Validation Set** | 4,490 images (held-out) | 4,490 images (identical split) | Unchanged |
| **Test Set** | 2,246 images (held-out) | 2,246 images (identical split) | Unchanged |
| **Epochs** | 1 | 2 | Completed warmup and optimization |
| **Classification Weight** | `cls: 0.5` | `cls: 1.0` | Stronger multi-class discrimination |
| **Training Duration** | 887 s (~14.8 min) | 2,998 s (~50.0 min) | 2 full epochs |

---

## 2. Overall Detection Performance Comparison

All metrics are evaluated at `conf=0.25`, `iou=0.5` on the identical held-out validation and test sets:

### Validation Split (4,490 images, 10,257 GT instances)
| Metric | V1 Baseline | V2 Improved | Delta | Fact-Based Observation |
|---|---|---|---|---|
| **Precision** | 23.41% | **38.30%** | **+14.89%** | V2 achieved 38.30% precision compared with V1's 23.41%. |
| **Recall** | 11.28% | **38.05%** | **+26.77%** | V2 achieved 38.05% recall compared with V1's 11.28% (3.37× increase). |
| **mAP@50** | 7.15% | **25.12%** | **+17.97%** | V2 achieved 25.12% mAP50 compared with V1's 7.15% (3.51× increase). |
| **mAP@50-95** | 2.17% | **11.87%** | **+9.70%** | V2 achieved 11.87% mAP50-95 compared with V1's 2.17% (5.47× increase). |

### Held-out Test Split (2,246 images, 4,960 GT instances)
| Metric | V1 Baseline | V2 Improved | Delta | Fact-Based Observation |
|---|---|---|---|---|
| **Precision** | 22.68% | **37.60%** | **+14.92%** | V2 achieved 37.60% precision compared with V1's 22.68%. |
| **Recall** | 11.59% | **37.44%** | **+25.85%** | V2 achieved 37.44% recall compared with V1's 11.59% (3.23× increase). |
| **mAP@50** | 6.98% | **25.23%** | **+18.25%** | V2 achieved 25.23% mAP50 compared with V1's 6.98% (3.61× increase). |
| **mAP@50-95** | 2.06% | **12.03%** | **+9.97%** | V2 achieved 12.03% mAP50-95 compared with V1's 2.06% (5.84× increase). |

---

## 3. Per-Class Performance Comparison (Held-out Test Split)

| Class ID | Class Name | V1 mAP@50 | V2 mAP@50 | Delta mAP@50 | V1 Recall | V2 Recall | V1 Precision | V2 Precision |
|---|---|---|---|---|---|---|---|---|
| 0 | `person` | 0.00% | **22.64%** | **+22.64%** | 0.00% | **50.00%** | 0.00% | **30.28%** |
| 1 | `helmet` | 22.24% | **72.84%** | **+50.60%** | 34.61% | **81.09%** | 49.77% | **60.75%** |
| 2 | `safety_vest` | 1.74% | **28.89%** | **+27.15%** | 5.11% | **50.88%** | 17.47% | **31.45%** |
| 3 | `gloves` | 0.00% | **9.15%** | **+9.15%** | 0.00% | **16.13%** | 0.00% | **34.78%** |
| 4 | `safety_footwear`| 0.00% | **0.34%** | **+0.34%** | 0.00% | **2.92%** | 0.00% | **6.19%** |
| 5 | `fire` | 11.06% | **20.15%** | **+9.09%** | 17.70% | **30.62%** | 48.08% | **41.99%** |
| 6 | `smoke` | 13.83% | **22.62%** | **+8.79%** | 23.71% | **30.48%** | 43.43% | **57.74%** |

> [!NOTE]
> On the validation split, `safety_footwear` reached **4.78% mAP@50** and **7.78% recall**. On the test split, footwear mAP is 0.34%, reflecting the severe physical challenge of resolving small footgear at 384×384 resolution on wide-angle camera perspectives.

---

## 4. Confidence Threshold Trade-Off Comparison

| Threshold | V1 Precision | V2 Precision | V1 Recall | V2 Recall | V1 mAP@50 | V2 mAP@50 | Operational Application |
|---|---|---|---|---|---|---|---|
| **0.25** | 23.41% | **38.30%** | 11.28% | **38.05%** | 7.15% | **25.12%** | Default Safety Alerting Mode |
| **0.35** | 28.29% | **46.03%** | 8.12% | **32.14%** | 5.63% | **22.62%** | Balanced Monitoring Mode |
| **0.50** | 32.32% | **54.00%** | 4.74% | **22.95%** | 3.57% | **17.68%** | High-Confidence Standard Mode |
| **0.60** | 36.14% | **60.23%** | 3.05% | **17.51%** | 2.47% | **14.28%** | Low False-Alarm Mode |
| **0.70** | 40.44% | **65.02%** | 1.66% | **12.27%** | 1.28% | **10.64%** | High-Certainty Auditing Mode |

---

## 5. Inference Latency Benchmark Comparison (CPU)

Measured on Intel Core i5-13420H at 384×384 px resolution:

| Metric | V1 Baseline | V2 Improved | Delta / Impact |
|---|---|---|---|
| **Mean Latency** | 32.89 ms | **52.04 ms** | +19.15 ms |
| **Median Latency** | 33.18 ms | **40.36 ms** | +7.18 ms (~24.8 FPS) |
| **Min Latency** | 24.80 ms | **29.53 ms** | ~33.9 FPS peak |
| **Throughput (FPS)** | 30.4 FPS | **19.2 - 24.8 FPS** | Real-time capable on edge CPU ($\ge 15$ FPS) |

---

## 6. Conclusion: Did V2 Improve Over V1?

**YES. V2 demonstrated substantial, measurable improvements across all core detection metrics:**
1. **mAP@50** increased by **+18.25 percentage points** (from 6.98% to 25.23% on held-out test data).
2. **Recall** tripled (from 11.59% to 37.44%).
3. **`person`** detection was unlocked from non-functional (0.00%) to **22.64% mAP50** and **50.00% recall**.
4. **`helmet`** detection reached production-grade **72.84% mAP50** and **81.09% recall**.
5. **`safety_vest`** detection leaped from 1.74% to **28.89% mAP50** and **50.88% recall**.
6. **`gloves`** detection improved from 0.00% to **9.15% mAP50**.
7. Latency remains well within real-time edge processing limits (median 40.36 ms $\approx$ 25 FPS).
