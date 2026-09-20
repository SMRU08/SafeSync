# Phase 3.1 — Root Cause Analysis & Severity Matrix
**Project:** RAKSHYA VISION — AI Vision-Based Safety Monitoring  
**Experiment:** `ppe_fire_smoke_v1`  
**Date:** 2026-09-20  

---

## 1. Severity Classification Matrix

| Finding ID | Classification | Severity | Impact on Detection Performance |
|---|---|---|---|
| **RC-01** | **Dataset Prefix Slicing via `fraction=0.25`** (`YOLODataset.get_img_files` slices sorted paths) | **CRITICAL** | Alphabetical sort took only `cppe_` and `fs_`. **Literally 0 instances of `person`, `gloves`, and `safety_footwear` were present in the v1 training set!** |
| **RC-02** | **Severe Training Under-convergence** (`epochs=1`, 245 steps) | **CRITICAL** | Model was terminated during warmup. `val/cls_loss` was 12.27. Head weights never converged. |
| **RC-03** | **Extreme Class Imbalance** (`helmet`: 47.9% vs `safety_footwear`: 2.9%) | **HIGH** | Helmet gradients swamped minority classes when present. |
| **RC-04** | **Small Object Spatial Downsampling** (`imgsz=384`) | **HIGH** | At 384×384, boots and gloves occupy < 15 px. Deep features lose spatial resolution. |
| **RC-05** | **Empty Background Frame Ratio** (18.8% empty label files) | **LOW** | With only 245 steps, empty frames diluted the few positive PPE signals. |

---

## 2. In-Depth Root Cause Breakdown

### CRITICAL: RC-01 — Dataset Prefix Slicing via `fraction=0.25`
- **Code Audit Evidence:**
  In `ultralytics.data.dataset.YOLODataset.get_img_files`:
  ```python
  im_files = sorted(...)
  count = self.fraction if isinstance(self.fraction, int) else max(1, round(len(im_files) * self.fraction))
  im_files = im_files[:count] if count < len(im_files) else im_files
  ```
- **Empirical Proof:**
  - When `fraction = 0.25` was set on 15,717 train images, Ultralytics took the first 3,929 files alphabetically:
    - `cppe_` images: 811
    - `fs_` (fire/smoke) images: 3,118
    - `hhw_` images: **0**
    - `ppec_` images: **0**
  - Actual ground-truth classes present in the 3,929 images trained in v1:
    - `helmet` (1): 1,209
    - `safety_vest` (2): 983
    - `fire` (5): 3,467
    - `smoke` (6): 3,619
    - `person` (0): **0 instances** (0.0%)
    - `gloves` (3): **0 instances** (0.0%)
    - `safety_footwear` (4): **0 instances** (0.0%)
- **Conclusion:**
  The model was literally never exposed to a single instance of `person`, `gloves`, or `safety_footwear` during training! This directly explains why validation and test mAP for those three classes was precisely **0.00%**.

### CRITICAL: RC-02 — Severe Training Under-convergence
- **Evidence:**
  - `epochs = 1`, `batch = 16` $\rightarrow$ exactly 245 training steps.
  - In `models/detection/ppe_fire_smoke_v1/results.csv`:
    - `epoch`: 1
    - `val/cls_loss`: **12.2696** (unconverged classification head)
    - `lr/pg0`: **0.000909** (still ramped in initial learning rate warmup)
- **Technical Explanation:**
  - YOLOv8 warmup runs for ~1,000 iterations or 3 epochs. In v1, training terminated before the optimizer exited warmup.

---

## 3. Disproven Hypotheses (What Was NOT the Problem)

- **Annotation Corruption:** Zero out-of-bounds, zero negative w/h, zero malformed labels, zero missing files. Annotations are verified clean.
- **Class Mapping Errors:** Mapping from 4 source datasets to 7 canonical classes is 100% faithful and verified.
- **Data Leakage:** Train/val/test splits share zero image name overlaps and exhibit identical per-class proportions.
- **Fire/Smoke Format:** D-Fire labels are verified standard YOLO bounding boxes, not classification or masks.

---

## 4. Remediation Strategy for `ppe_fire_smoke_v2`

1. **Fix Training Data Selection:**
   - Either train with `fraction: 1.0` (all 15,717 train images) or use a class-stratified / prefix-balanced training subset so all 7 classes (`person`, `helmet`, `safety_vest`, `gloves`, `safety_footwear`, `fire`, `smoke`) are well-represented!
2. **Increase Training Epochs:**
   - Train for multiple epochs (e.g. 3-5 epochs) so warmup completes and classification loss converges.
3. **Class Loss Weighting:**
   - Increase classification loss weight (`cls: 1.0`) to give stronger gradients to multi-class discrimination.
4. **Controlled Experiment Record:**
   - Keep baseline v1 intact. Log all hyperparameter changes in `models/detection/experiment_comparison.csv`.
