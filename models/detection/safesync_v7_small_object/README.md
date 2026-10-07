# SafeSync V7 Experimental Model — Design Specification & Roadmap

> **STATUS:** EXPERIMENTAL | NOT PRODUCTION | NOT ACTIVE | NOT USED BY RUNTIME  
> **Active Production Model:** `ppe_fire_smoke_v3` (SHA-256: `9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe`)  
> **Shadow Evaluation Model:** `safesync_v6_hardnegative` (SHA-256: `c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc`)  
> **Training Status:** NOT TRAINED YET (Preparation & Specification Phase Only)  
> **Dataset Audit Status:** **RED — NOT SAFE FOR TRAINING** (Candidate scaffold contains 0 images; requires controlled curation pass)  

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
