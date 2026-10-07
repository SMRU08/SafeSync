# SafeSync V7 Training Plan (Phase A — Proposed Blueprint)

> **IMPORTANT:** NO TRAINING IS EXECUTED IN THIS PHASE.  
> This document outlines the technical staging requirements for future authorized training.

---

## 1. Planned Training Pipeline

### Step 1: Dataset Assembly & Leakage Audit
- Source datasets: `datasets/v7_candidate/`
- Verify camera/scene-aware partitioning (no duplicate backgrounds between train and val/test).
- Confirm zero presence of test set images (`datasets/processed_v3/images/test`) in training or validation splits.

### Step 2: Class Balancing & Small-Object Curation
- Re-balance training distribution:
  - Increase glove instances via high-resolution crops from multi-color glove datasets.
  - Increase footwear instances across angled and distant workers.
  - Maintain 100% of hard-negative suppression images (steam, dust, machinery, glare, bare hands).

### Step 3: Model Architecture Configuration
- Base: Ultralytics YOLOv8n backbone and neck.
- Input resolution: 640×640.
- Hyperparameters:
  - `epochs`: 100
  - `batch`: 16
  - `optimizer`: SGD / AdamW (learning rate $0.01$ with cosine decay)
  - `patience`: 20 epochs

### Step 4: Staged Progression
1. **Pre-flight Check:** Verify GPU memory, dataset paths, checksums.
2. **Epoch 1–100:** Train on `datasets/v7_candidate/` using deterministic seed `42`.
3. **Artifact Freezing:** Save `best.pt`, record SHA-256, lock weights.
4. **Dual-Paradigm Audit:** Execute `verify_benchmark_pipeline.py`.
5. **Gating Check:** Compare against V3 production baseline in `EXPERIMENT_TRACKER.md`.
