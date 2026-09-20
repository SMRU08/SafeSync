# Phase 3.1 — Model Diagnosis & Data Audit Report
**Project:** RAKSHYA VISION — AI Vision-Based Safety Monitoring  
**Target:** Phase 3 Baseline Model (`ppe_fire_smoke_v1`)  
**Status:** DIAGNOSIS COMPLETED  

---

## 1. Executive Summary

Phase 3 baseline model (`ppe_fire_smoke_v1`) yielded modest overall detection performance:
- Overall Precision: 23.41%
- Overall Recall: 11.28%
- Overall mAP@50: 7.15% (0.0715)
- Overall mAP@50-95: 2.17% (0.0217)

Per-class breakdown revealed extreme variance:
- `helmet`: mAP@50 = 22.10% (P: 50.76%, R: 34.75%)
- `smoke`: mAP@50 = 17.87% (P: 47.50%, R: 25.77%)
- `fire`: mAP@50 = 8.48% (P: 47.08%, R: 13.53%)
- `safety_vest`: mAP@50 = 1.61% (P: 18.55%, R: 4.92%)
- `person`: mAP@50 = 0.00%
- `gloves`: mAP@50 = 0.00%
- `safety_footwear`: mAP@50 = 0.00%

A comprehensive, evidence-based diagnostic audit was conducted across all 22,453 dataset images, 51,195 bounding boxes, mapping logic, split distributions, and training configurations.

---

## 2. Comprehensive Investigation Findings

### A. Dataset Quality & Bounding Box Audit
- **Total Images Analyzed:** 22,453 (Train: 15,717, Val: 4,490, Test: 2,246)
- **Total Bounding Boxes Evaluated:** 51,195
- **Corrupted / Malformed Lines:** 0
- **Invalid Class IDs:** 0 (all strictly in [0..6])
- **Out-of-Bounds Coordinates:** 0
- **Negative or Zero Width/Height:** 0
- **Duplicate Bounding Boxes:** 0
- **Empty / Background Images:** 4,225 (18.8% of total images)
  - *Observation:* These images contain either pure background scenes or images where only non-target classes (e.g. `head`, `no-helmet`, `no-vest`, `mask`) were present in the source datasets and filtered out during normalization. This ratio is acceptable for object detection to suppress false positive rate, but poses learning hurdles if the model is severely under-trained.

### B. Class Mapping Audit
Source labels were mapped into the 7 canonical classes via `scripts/dataset/normalize_classes.py` and `datasets/manifests/class_mapping.yaml`:
- `0: person` ← `person`, `worker`, `human`
- `1: helmet` ← `helmet`, `hat`, `hard-hat`, `hard_hat`
- `2: safety_vest` ← `vest`, `safety-vest`, `safety_vest`
- `3: gloves` ← `glove`, `gloves`
- `4: safety_footwear` ← `boot`, `boots`, `safety-boot`, `safety-boots`, `safety-shoe`, `Safety Boot`
- `5: fire` ← `Fire`, `fire`
- `6: smoke` ← `Smoke`, `smoke`
- Ignored classes: `head`, `no-helmet`, `no-vest`, `no-gloves`, `no-boots`, `mask`, `goggles`.
- *Audit Outcome:* Mappings are completely correct, unambiguous, and faithful to canonical definitions.

### C. Class Imbalance Analysis
Recorded in [`models/detection/ppe_fire_smoke_v1/class_analysis.csv`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/models/detection/ppe_fire_smoke_v1/class_analysis.csv):
| ID | Class Name | Total Instances | % of Total | Train Images | Val Images | Test Images |
|---|---|---|---|---|---|---|
| 0 | `person` | 5,545 | 10.83% | 2,430 | 663 | 357 |
| 1 | `helmet` | 24,531 | **47.92%** | 6,501 | 1,833 | 907 |
| 2 | `safety_vest` | 6,272 | 12.25% | 2,143 | 585 | 273 |
| 3 | `gloves` | 2,634 | **5.15%** | 985 | 275 | 134 |
| 4 | `safety_footwear` | 1,507 | **2.94%** | 302 | 88 | 55 |
| 5 | `fire` | 5,333 | 10.42% | 1,441 | 403 | 219 |
| 6 | `smoke` | 5,373 | 10.50% | 2,435 | 731 | 349 |

- *Imbalance Factor:* Helmet has **16.3× more instances** than safety footwear and **9.3× more instances** than gloves.
- In rapid single-epoch training, the model's loss gradients were overwhelmingly dominated by helmet bounding box regressions.

### D. Train / Val / Test Split Audit
- Generated [`datasets/reports/phase3_1_split_audit.json`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/datasets/reports/phase3_1_split_audit.json).
- Exact filename overlaps between splits:
  - `train_val`: 0
  - `train_test`: 0
  - `val_test`: 0
- Proportions across all 7 classes are uniformly distributed (~70% train, ~20% val, ~10% test).
- Zero data leakage detected.

### E. Fire / Smoke Data Format Audit
- Source: `d_fire` dataset.
- Verified that annotations are genuine normalized YOLO bounding boxes `(cls x_center y_center width height)` representing localized fire flames and smoke plumes.

### F. Training Configuration Audit (`configs/training.yaml`)
- **Epochs:** `1` (Extremely low)
- **Fraction:** `0.25` (Subsampled 25% of the 15,717 training images = ~3,929 images)
- **Batch Size:** `16`
- **Total Training Iterations:** $\frac{3,929}{16} \approx 245$ iterations!
- **Learning Rate Warmup:** Standard YOLO warmup requires ~3 epochs or 1,000 iterations. In v1, training terminated while still in the initial learning rate warmup phase!
- **Validation Loss:** `val/cls_loss` was 12.27 at epoch 1 termination, showing complete non-convergence of classification heads.

---

## 3. Summary of Visual Inspection
- **Ground-Truth Samples:** 20 train, 20 val, 20 test rendered with bounding boxes in [`datasets/reports/phase3_1_samples/`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/datasets/reports/phase3_1_samples/). Annotations accurately enclose safety gear, workers, and fires.
- **Error Samples:** 16 paired error comparisons generated in [`models/detection/ppe_fire_smoke_v1/error_samples/`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/models/detection/ppe_fire_smoke_v1/error_samples/).
  - Confirmed false negatives on boots, gloves, and persons due to classification head under-training.
