# SafeSync V7 Experiment Tracking Ledger

> **STATUS:** PREPARED | ZERO EXPERIMENTS RUN IN PHASE A  
> **Evaluation Protocol:** Frozen Held-Out Test Set (`datasets/processed_v3/data_v3.yaml`, 410 images, 1,235 ground-truth annotations).  
> **Production Baseline (V3):** Micro Precision: 0.4610 | Micro Recall: 0.5223 | Operational F1: 0.4897 | Total FN: 590 | 12/12 Real-World Pass | CPU Latency: 42.6 ms (23.5 FPS).  

---

## 1. Structured Experiment Ledger

| Exp ID | Dataset Version | Img Size | Epochs | Batch | Model Architecture | Augmentation Config | Class Balancing | Loss Config | Val mAP50 | Op Precision | Op Recall | Op F1 | Glove Recall | Footwear Recall | Fire Recall | Smoke Recall | False Positives | False Negatives | CPU Latency | FPS | Hard-Negative Test | Final Decision |
|---|---|:---:|:---:|:---:|---|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| *BASELINE_V3* | `processed_v3` | 640 | 100 | 16 | YOLOv8n (Standard) | Default Mosaic+Fliplr | Standard | Box=7.5, Cls=0.5, DFL=1.5 | 0.3785 | 0.4610 | 0.5223 | 0.4897 | 0.0986 | 0.2966 | 0.1414 | 0.2453 | 754 | 590 | 42.57 ms (384) | 23.5 | 12/12 PASS | **ACTIVE PRODUCTION** |
| *SHADOW_V6* | `v6_candidate` | 640 | 100 | 16 | YOLOv8n (HardNeg) | HardNeg Suppression | Weighted | Box=7.5, Cls=0.5, DFL=1.5 | 0.2612 | 0.3598 | 0.4332 | 0.3931 | 0.1831 | 0.2966 | 0.2323 | 0.0755 | 952 | 700 | 42.30 ms (384) | 23.6 | 12/12 PASS | **ACTIVE SHADOW** |
| `EXP_V7_01` | *Pending* | 640 | 100 | 16 | YOLOv8n + P2 Head | Scale Crop + Mosaic | Glove / Boot Over-sampling | Scale-weighted Focal Loss | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *PLANNED* |
| `EXP_V7_02` | *Pending* | 640 | 120 | 16 | YOLOv8s (Exploratory) | Scale Crop + Mosaic | Balanced 7-class | Small-object Loss Boost | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *TBD* | *PLANNED* |

---

## 2. Experiment Logging Guidelines

For every future training run, engineers must record:
1. **Exact Git Commit Hash:** Tag the codebase before launching training.
2. **Deterministic Random Seed:** Ensure repeatable data ordering (`seed=42`).
3. **Dataset Manifest Checksum:** Verify MD5/SHA-256 of `train.txt`, `val.txt`, and `test.txt`.
4. **Hardware Specifications:** Document training GPU, batch size, and total GPU hours.
5. **Exact Artifact Checksum:** Record the SHA-256 of the generated `best.pt`.
6. **Dual-Paradigm Benchmark Results:** Execute `verify_benchmark_pipeline.py` and populate the exact columns above.
