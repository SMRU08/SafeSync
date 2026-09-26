# SafeSync Fire & Smoke Model Training & Production Hardening Guide

## 1. Overview & Strategy

This document details the training configuration, dataset expansion, hard-negative curation, and model evaluation procedure for SafeSync's Fire and Smoke detection pipeline.

### Core Architecture & Hardware Budget
- **Model Architecture**: YOLOv8n (Nano profile, ~3.0M parameters, 8.1 GFLOPs)
- **Deployment Target**: Edge / Industrial Server (CPU-only PyTorch, Intel Core i5-13420H, 16GB RAM)
- **Input Resolution**: 384x384 (inference) / 1280x720 (native camera stream, letterboxed)
- **Classes**:
  - `0: fire`
  - `1: smoke`

---

## 2. Dataset Composition & Hard Negatives

The training corpus consists of positive annotations from D-Fire and curated industrial hard negatives:

| Subset | Positive Images (D-Fire) | Hard Negative Images | Total Images | Fire Boxes | Smoke Boxes | Total Boxes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | 4,175 | 500 | 4,675 | 4,992 | 4,974 | 9,966 |
| **Validation** | 354 | 70 | 424 | 303 | 309 | 612 |
| **Test** | 102 | 30 | 132 | 38 | 90 | 128 |
| **TOTAL** | **4,631** | **600** | **5,231** | **5,333** | **5,373** | **10,706** |

### Hard Negatives Rationale
Standard public datasets often omit background negative images, leading models to predict fire/smoke on high-contrast objects (e.g. orange clothing, fluorescent lighting, white walls, and steam). SafeSync curates 600 industrial background scenes with **empty `.txt` label files** (11.5% negative ratio) to penalize false activations.

---

## 3. Training Hyperparameters

```yaml
model: yolov8n.pt
imgsz: 384
batch: 16
workers: 0
optimizer: AdamW
lr0: 0.005
lrf: 0.01
weight_decay: 0.0005
warmup_epochs: 0.3
mosaic: 0.3
hsv_h: 0.015
hsv_s: 0.4
hsv_v: 0.3
fliplr: 0.5
flipud: 0.0
patience: 5
seed: 42
```

---

## 4. Evaluation & Production Promotion Rule

Per Section 17 of the SafeSync Hardening Directive:
- **Baseline Model**: `models/detection/ppe_fire_smoke_v2/weights/best.pt` (SHA-256: `490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3`)
- **Candidate Model**: `models/detection/fire_smoke/candidate_v2/weights/best.pt` (SHA-256: `8b4034368a90fcafc5efb3b3c591c854bea4b5de3d8e843524e4b9acce832e13`)

### Benchmark Comparison
- **15-Scenario Challenge Suite**:
  - Baseline `ppe_fire_smoke_v2`: **0/13 False Positives** (Clean across steam, sunlight, orange clothes, reflections, dust, welding, etc.)
  - Under-trained Candidate `candidate_v2` (2 epochs on CPU): **8/13 False Positives** (Under-converged classification head)
- **Decision**: **KEEP EXISTING PRODUCTION MODEL `ppe_fire_smoke_v2`**. The candidate is preserved as an experiment checkpoint without replacing the stable production model.
