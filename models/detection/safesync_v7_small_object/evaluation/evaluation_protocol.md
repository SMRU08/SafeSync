# SafeSync V7 Empirical Evaluation Protocol

> **PURPOSE:** Enforces strict, reproducible benchmarking on any future V7 candidate checkpoint before consideration for staging.  

---

## 1. Frozen Test Set Requirement
All evaluation MUST be performed against the held-out test dataset:
- **Path:** `datasets/processed_v3/data_v3.yaml` (test split)
- **Image Directory:** `datasets/processed_v3/images/test` (410 images)
- **Label Directory:** `datasets/processed_v3/labels/test` (1,235 annotations)
- **Invariant:** Test split must never be modified, expanded, pruned, or seen during training.

---

## 2. Dual-Paradigm Benchmark Execution
Every candidate checkpoint must be evaluated across BOTH paradigms using `scripts/benchmark/verify_benchmark_pipeline.py`:

### A. YOLO Validation Benchmark (PR-Curve / Optimal F1)
- Framework: Ultralytics `model.val()`
- Device: CPU, batch 16, imgsz 640.
- Metrics Recorded: $mAP_{50}$, $mAP_{50-95}$, Mean Precision ($mp$), Mean Recall ($mr$), Class-wise AP50.

### B. Operational Fixed-Threshold Benchmark ($\text{conf}=0.25, \text{IoU}=0.50$)
- Match method: Greedy bipartite matching against ground truth annotations.
- Invariant check: $\text{True Positives} + \text{False Negatives} \equiv \text{Ground Truth Instances}$.
- Metrics Recorded: Micro/Macro Operational Precision, Recall, F1, Class-wise TP/FP/FN.

---

## 3. Real-World Challenge Suite Evaluation
The candidate must be evaluated against the 12 industrial challenge scenarios in `scripts/testing/`:
1. `CHAL_01` — Frontal Full-Body Worker (Pose variation)
2. `CHAL_02` — Multi-Worker Crowded Scene (Cross-worker occlusion)
3. `CHAL_03` — Angled / Crouched Worker (Non-vertical spine)
4. `CHAL_04` — Waist-Up Cropped Worker (Edge boundary)
5. `CHAL_05` — Distant Small-Scale Workers (Small object challenge)
6. `CHAL_06` — Open Flame Phenomenon (Combustion fire)
7. `CHAL_07` — Atmospheric Smoke Plume (Particulate smoke)
8. `CHAL_08` — Dual Fire + Smoke Chamber (Multi-hazard)
9. `CHAL_09` — Person + Fire Co-existence (Worker near flame)
10. `CHAL_10` — Person + Smoke Co-existence (Worker near plume)
11. `CHAL_11` — Hard Negative Industrial Machine (Zero false alarm check)
12. `CHAL_12` — Hard Negative Glare / Steam (Zero false alarm check)

**Target:** 12/12 PASS (100%). Any false alarm on CHAL_11 or CHAL_12 constitutes an automatic disqualification.

---

## 4. Hardware Latency Verification
- Device: Identical CPU hardware (standard Intel Core i5).
- Input Resolutions: 384×384 (edge stream) and 640×640 (detail frame).
- Warmup: 10 iterations.
- Timed Runs: 30 iterations.
- Required Latency: $\le 50.0$ ms at 384×384 ($\ge 20.0$ FPS).
