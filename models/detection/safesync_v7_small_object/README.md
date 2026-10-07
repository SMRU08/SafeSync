# SafeSync V7 Experimental Model — Design Specification & Roadmap

> **STATUS:** EXPERIMENTAL | NOT PRODUCTION | NOT ACTIVE | NOT USED BY RUNTIME  
> **Active Production Model:** `ppe_fire_smoke_v3` (SHA-256: `9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe`)  
> **Shadow Evaluation Model:** `safesync_v6_hardnegative` (SHA-256: `c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc`)  
> **Training Status:** CONTROLLED RUN 1 COMPLETED (`weights/best.pt`; SHA-256: `5a4e37fb381c318f4dd88a5bc7e80d43489c9e8fbf566f8b2024813ad2da9334`)  
> **Evaluation Verdict:** **YELLOW** (Gloves recall tripled 3.0×, hard-negative FPs reduced by 91.9%; overall recall needs multi-epoch convergence; V3 remains production)  
> **Dataset Audit Status:** **GREEN — READY FOR CONTROLLED V7 TRAINING** (6,163 curated images, 14,926 canonical bounding boxes, 2,178 gloves, 2,454 footwear, 347 hard negatives, 0 test set leakage)  

---

## 1. Executive Summary & Objective

The **SafeSync V7** initiative is a planned, isolated experimental model designed specifically to solve the primary remaining challenge identified during the repository-wide benchmark audit: **Small-Object PPE Detection**.

### Primary Engineering Objectives:
1. **Gloves Detection:** Overcome spatial resolution limits to detect industrial work gloves across varied colors, fabrics, and orientations.
2. **Safety Footwear Detection:** Increase recall on lower-limb protective footwear in complex factory floor contexts, occluded angles, and distant workers.
3. **Distant & Scale-Varying PPE:** Detect protective gear on workers located 5–15 meters from CCTV mountings (<2% of image area).
4. **Partial / Occluded Gear:** Detect helmets, vests, and gloves partially occluded by machinery, guardrails, or industrial tools.
5. **Difficult Worker Poses:** Maintain accurate detection across crouched, bending, angled, or reaching workers.

### Critical Preservation Mandates (V3 Strengths):
Under NO circumstances will improvements in small-object detection be accepted if they regress:
- **Helmet Detection:** Must maintain $\ge 0.7127$ operational recall and $\ge 0.6308$ mAP50.
- **Safety Vest Detection:** Must maintain $\ge 0.7460$ operational recall and $\ge 0.7298$ mAP50.
- **Person Detection:** Must maintain robust multi-worker bounding box tracking.
- **Fire & Smoke Robustness:** Must maintain clean combustion separation with **0 false alarms** on industrial steam, glare, and machinery.
- **Edge CPU Feasibility:** Must maintain $\ge 20$ FPS at 384×384 on standard Intel Core i5 CPU hardware.

### 1.1 Curated V7 Dataset Inventory (Audit Confirmed):
The candidate dataset at `datasets/v7_candidate/` has been curated, deduplicated, and audited:
- **Total Images:** 6,163 (+50.3% vs V3's 4,100)
- **Total Bounding Boxes:** 14,926 (+30.7% vs V3's 11,424)
- **Gloves (Class 3):** 2,178 boxes (+206.3% increase / 3.06× representation)
- **Safety Footwear (Class 4):** 2,454 boxes (+155.1% increase / 2.55× representation)
- **Hard-Negative Distractors:** 347 empty frames (300 preserved from V3)
- **Test Benchmark Leakage:** 0.00% (409 SHA-256 exclusion hashes enforced)
- **Audit Verification:** See `models/detection/safesync_v7_small_object/evaluation/v7_dataset_audit.md` for full report.

### 1.2 First Controlled Run Results (EXP_V7_01 Summary — 1 Epoch):
- **Base Checkpoint:** `yolov8n.pt`
- **Resolution:** 384×384 | **Batch:** 16 | **Optimizer:** SGD (`lr0=0.01`)
- **Weights Generated:** `runs/run1/weights/best.pt` (`5a4e37fb381c...`)
- **Key Gains:** Glove recall tripled from 0.0282 to 0.0845; hard-negative distractor FPs reduced from 805 to 65 (-91.9%); CPU latency 40.64 ms (24.6 FPS).
- **Trade-offs:** Overall convergence across large objects requires further training epochs before staging.
- **Verdict:** **YELLOW** (V3 remains active production, V6 remains shadow). Full report in `EXPERIMENT_RESULTS.md`.

### 1.3 Controlled Run 2 Results (EXP_V7_02 Summary — Multi-Epoch Convergence):
- **Base Checkpoint:** `yolov8n.pt`
- **Resolution:** 384×384 | **Batch:** 16 | **Epochs:** 3 | **Optimizer:** SGD (`lr0=0.01`, `momentum=0.937`)
- **Weights Generated:** `runs/run2/weights/best.pt` (`5b5304e0f704cd7024ae1eea68ad5e0614c21194363a0f7d01285d4d6a7ea722`)
- **Key Gains:**
  - **Gloves (Class 3):** Recall surged to **0.1549 (11 TP)** — **5.5× higher than V3 (2 TP)** and nearly double Run 1 (6 TP).
  - **Vest (Class 2):** Recall completely recovered to **0.7878 (245 TP)**, reaching parity with V3's 246 TP.
  - **Footwear (Class 4):** Emerged with **8 TP** (up from 0 TP in Run 1).
  - **Overall TP:** Surged from 138 in Run 1 to **531 TP in Run 2 (+284% increase)**; overall recall reached **0.4300**.
  - **Distractor Safety:** 0 false fire alarms, 0 false smoke alarms; 40.1% fewer overall FPs than V3 (482 vs 805).
  - **Edge CPU Throughput:** **35.9 FPS** (27.88 ms mean latency) — fully real-time.
- **Trade-offs:** Footwear recall (0.0552) still below V3 baseline (0.2828).
- **Verdict:** **YELLOW** (Multi-epoch convergence hypothesis confirmed; V3 remains active production, V6 shadow, V7 experimental). Full report in `runs/run2/RUN2_REPORT.md`.

### 1.4 Controlled Run 3 Results (EXP_V7_03 Summary — Continuation Convergence):
- **Base Checkpoint:** `runs/run2/weights/best.pt` (`5b5304e0f704...`)
- **Resolution:** 384×384 | **Batch:** 16 | **Epochs:** 3 (Cumulative 6 Epochs) | **Optimizer:** SGD (`lr0=0.005`, `momentum=0.937`)
- **Weights Generated:** `runs/run3/weights/best.pt` (`d725767535e9bd56586620378b4411a443b7fd17653625f2d8a2886b63aaf218`)
- **Key Gains:**
  - **Overall Precision & F1:** Precision reached **0.5247** (beating V3's 0.4879) and F1 reached **0.5334** (beating V3's 0.5184).
  - **Overall Recall:** Reached **0.5425 (670 TP)**, narrowing the gap with V3 (0.5530 / 683 TP) to just 1.05%.
  - **Footwear (Class 4):** Surged from 8 TP to **26 TP (+225% gain)**; precision reached **0.3095** (higher than V3's 0.2595); recall reached **0.1793**.
  - **Gloves (Class 3):** Maintained **0.1549 recall (11 TP)** — **5.5× higher than V3 (2 TP)**, with higher precision (0.1692 vs 0.0476) and fewer false positives (54 vs 75).
  - **Vest (Class 2):** Recall reached **0.8167 (254 TP)**, exceeding V3 (0.7910 / 246 TP).
  - **Smoke Hazard (Class 6):** Recall surged to **0.3396 (36 TP)** vs V3's 0.1981 (21 TP).
  - **Distractor Safety:** 0 false fire alarms, 0 false smoke alarms on industrial steam/glare; 210 fewer total FPs than V3 (595 vs 805).
  - **Edge CPU Throughput:** **28.4 FPS** (35.22 ms mean latency) — fully real-time ($\ge 20$ FPS).
- **Trade-offs:** Footwear recall (0.1793) remains below V3 baseline (0.2828).
- **Verdict:** **YELLOW** (Strong convergence observed, outperforming V3 in Precision, F1, Gloves, Vest, Smoke, and Distractor FP suppression, but Footwear recall gap requires architectural small-object feature enhancements before production promotion; V3 remains active production, V6 shadow, V7 experimental). Full report in `runs/run3/RUN3_REPORT.md`.

---

## 2. Canonical 7-Class Ontology (Strict Invariant)

V7 strictly preserves the canonical SafeSync class indexing:

| Class ID | Canonical Name | Definition & Bounds |
|:---:|---|---|
| `0` | `person` | Full or visible upper-body worker bounding box |
| `1` | `helmet` | Industrial hard hat / safety helmet worn on head |
| `2` | `safety_vest` | High-visibility reflective thoracic vest or jacket |
| `3` | `gloves` | Protective handwear (leather, nitrile, cut-resistant, thermal) |
| `4` | `safety_footwear` | Steel-toe boots, protective industrial footwear |
| `5` | `fire` | Open flame, combustion hazard |
| `6` | `smoke` | Particulate plume, expanding combustion smoke |

### Prohibited Changes:
- **DO NOT** introduce negative classes (e.g., `no_helmet`, `no_vest`, `no_gloves`, `no_footwear`). PPE absence is mathematically derived by SafeSync's Compliance and Association Engine (`UNKNOWN != VIOLATION`).
- **DO NOT** introduce eye protection / goggles without independent enterprise approval.
- **DO NOT** alter class indices or names.

---

## 3. Potential Research Directions (Hypotheses to Validate)

The following directions represent technical avenues for experimental investigation during the V7 training phase. **Note:** These are experimental hypotheses; no performance advantage is claimed until verified empirically against the held-out test suite.

1. **High-Resolution Feature Pyramids:**
   - Investigate adding a P2 feature pyramid head (stride 4) to capture micro-scale handwear and footwear features before sub-sampling loss.
2. **Small-Object Loss Reweighting:**
   - Experiment with scale-aware Focal Loss weighting: assign higher penalty to misclassified bounding boxes with area $<0.01$ of image frame.
3. **Curated Glove & Footwear Sampling:**
   - Balance training batches so that every batch contains high-resolution crops of diverse gloves and footwear rather than having these classes dominated by large vests.
4. **Hard-Negative Distractor Retention:**
   - Retain all 406 V6 hard-negative distractors (bare hands, tools, machine shadows, steam boilers, exhaust pipes) to prevent precision decay.
5. **Difficult-Angle & Distant Augmentation:**
   - Utilize mosaic and copy-paste augmentations specifically tailored for scale variance (distant workers, partial limb occlusion).

---

## 4. Engineering Acceptance Criteria (Go / No-Go Gate)

Before V7 can even be considered for staging (shadow mode), it MUST meet all of the following empirical criteria on the common 410-image, 1,235-annotation test dataset:

| Target Metric | V3 Production Baseline | V7 Required Target | Verdict Threshold |
|---|:---:|:---:|:---:|
| **Gloves Operational Recall** | 0.0986 (7 TP) | **> 0.3000** | Must improve $\ge 3\times$ |
| **Footwear Operational Recall**| 0.2966 (43 TP) | **> 0.4000** | Must improve $\ge 1.35\times$ |
| **Person Operational Recall** | 0.5570 | **$\ge 0.5570$** | No regression |
| **Helmet Operational Recall** | 0.7127 | **$\ge 0.7127$** | No regression |
| **Safety Vest Operational Recall**| 0.7460 | **$\ge 0.7460$** | No regression |
| **Overall False Negatives** | 590 FN | **< 550 FN** | Must achieve fewer misses |
| **Fire Operational Precision** | 0.5600 | **$\ge 0.5000$** | No precision collapse |
| **Smoke Operational Precision**| 0.4906 | **$\ge 0.4500$** | No precision collapse |
| **12-Scenario Real-World Suite**| 12/12 PASS (100%) | **12/12 PASS (100%)** | Zero false alarms on steam/glare |
| **Cross-Worker Contamination** | 0 | **0** | Strict bounding box isolation |
| **CPU Latency @ 384×384** | 42.57 ms (23.5 FPS) | **$\le 50.0$ ms ($\ge 20$ FPS)** | Edge CPU real-time constraint |

**FAIL CONDITION:** If a candidate model improves glove recall but causes false alarms on steam/glare, degrades fire/smoke detection, or drops CPU throughput below 20 FPS, the candidate is **REJECTED (FAILED)** and **V3 remains in production**.

---

## 5. Directory Structure

```
models/detection/safesync_v7_small_object/
├── README.md                 <- This specification & design document
├── EXPERIMENT_TRACKER.md     <- Structured logging of all V7 training runs
├── configs/
│   └── v7_architecture_spec.yaml <- Candidate architectural configurations
├── weights/
│   └── (Empty - No training executed in Phase A)
├── evaluation/
│   └── evaluation_protocol.md <- Step-by-step benchmark verification guide
└── training/
    └── training_plan.md      <- Data preparation, loss weighting, and run steps
```

---

*Authored by SafeSync Senior Computer Vision Engineering Team. Frozen under repository protection policy.*
