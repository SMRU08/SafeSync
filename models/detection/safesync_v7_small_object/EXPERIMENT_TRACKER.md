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
| `EXP_V7_01` | `v7_candidate` | 384 | 1 | 16 | YOLOv8n (Run 1 Exploratory) | Mosaic+Mixup+CopyPaste | Curated Small-Obj | Box=7.5, Cls=0.5, DFL=1.5 | 0.138 | 0.4207 | 0.1117 | 0.1766 | 0.0845 | 0.0 | 0.0808 | 0.0094 | 190 | 1097 | 40.64 ms | 24.6 | 16/16 PASS | **YELLOW** |
| `EXP_V7_02` | `v7_candidate` | 384 | 3 | 16 | YOLOv8n (Run 2 Multi-Epoch) | Mosaic+Mixup+CopyPaste | Curated Small-Obj | Box=7.5, Cls=0.5, DFL=1.5 | 0.3744 | 0.4737 | 0.43 | 0.4508 | 0.1549 | 0.0552 | 0.1414 | 0.1792 | 590 | 704 | 27.88 ms | 35.9 | 16/16 PASS | **YELLOW** |

---

## 2. Experiment Logging Guidelines

For every future training run, engineers must record:
1. **Exact Git Commit Hash:** Tag the codebase before launching training.
2. **Deterministic Random Seed:** Ensure repeatable data ordering (`seed=42`).
3. **Dataset Manifest Checksum:** Verify MD5/SHA-256 of `train.txt`, `val.txt`, and `test.txt`.
4. **Hardware Specifications:** Document training GPU, batch size, and total GPU hours.
5. **Exact Artifact Checksum:** Record the SHA-256 of the generated `best.pt`.
6. **Dual-Paradigm Benchmark Results:** Execute `verify_benchmark_pipeline.py` and populate the exact columns above.
