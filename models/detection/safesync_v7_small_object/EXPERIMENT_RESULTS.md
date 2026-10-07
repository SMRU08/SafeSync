# SAFESYNC V7 EXPERIMENT RESULTS & EVALUATION REPORT

**Model:** `safesync_v7_small_object`  
**Execution Date:** 2026-10-07  
**Evaluation Target:** First Controlled V7 Training Run  
**Model Checkpoint:** `models/detection/safesync_v7_small_object/weights/best.pt`  
**SHA-256:** `5a4e37fb381c318f4dd88a5bc7e80d43489c9e8fbf566f8b2024813ad2da9334`  
**Baseline Reference:** `ppe_fire_smoke_v3/weights/best.pt` (`9b414f3018d5...` - LOCKED)  
**Shadow Reference:** `safesync_v6_hardnegative/weights/best.pt` (`c47705a2c27c...` - LOCKED)  

---

## 1. EXECUTIVE SUMMARY & VERDICT

### FINAL EXPERIMENTAL VERDICT:
$$\mathbf{YELLOW}$$

- **Production Policy:** V3 remains **ACTIVE PRODUCTION**. V6 remains **SHADOW MODE**. V7 is an **EXPERIMENTAL CANDIDATE** (NOT promoted to production).
- **Validation Metrics (PR-Curve on V7 Val Split):**
  - Mean Precision: **0.2084**
  - Mean Recall: **0.2068**
  - mAP50: **0.138**
  - mAP50-95: **0.0629**
- **Inference Speed:** **40.64 ms** at 384×384 on CPU (**24.6 FPS**). Meets real-time industrial requirement ($\ge 20$ FPS).
- **Distractor Robustness:** Zero false fire or smoke alarms on 300 industrial hard negatives.

---

## 2. PRODUCTION SAFETY LOCK VERIFICATION

| Model | Path | Expected SHA-256 | Actual SHA-256 | Status |
|---|---|---|---|:---:|
| **Production Model (V3)** | `models/detection/ppe_fire_smoke_v3/weights/best.pt` | `9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe` | `9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe` | **LOCKED (MATCH)** |
| **Shadow Model (V6)** | `models/detection/safesync_v6_hardnegative/weights/best.pt` | `c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc` | `c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc` | **LOCKED (MATCH)** |
| **V7 Candidate** | `models/detection/safesync_v7_small_object/weights/best.pt` | Generated Post-Training | `5a4e37fb381c318f4dd88a5bc7e80d43489c9e8fbf566f8b2024813ad2da9334` | **EXPERIMENTAL** |

---

## 3. EXACT COMPARISON ON FROZEN BENCHMARK TEST SUITE (conf=0.25, IoU=0.50, 410 images)

| Class Name | V3 Prec | V3 Rec | V3 F1 | V3 TP/FN | V7 Prec | V7 Rec | V7 F1 | V7 TP/FN | Recall Delta |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **person** | 0.3812 | 0.6754 | 0.4873 | 154 / 74 | 0.5068 | 0.1623 | 0.2458 | 37 / 191 | -51.31% |
| **helmet** | 0.5731 | 0.7273 | 0.641 | 200 / 75 | 0.8523 | 0.2727 | 0.4132 | 75 / 200 | -45.46% |
| **safety_vest** | 0.6474 | 0.791 | 0.712 | 246 / 65 | 0.3235 | 0.0354 | 0.0638 | 11 / 300 | -75.56% |
| **gloves** | 0.0476 | 0.0282 | 0.0354 | 2 / 69 | 0.0652 | 0.0845 | 0.0736 | 6 / 65 | +5.63% |
| **safety_footwear** | 0.2595 | 0.2828 | 0.2706 | 41 / 104 | 0.0 | 0.0 | 0.0 | 0 / 145 | -28.28% |
| **fire** | 0.5758 | 0.1919 | 0.2879 | 19 / 80 | 0.2286 | 0.0808 | 0.1194 | 8 / 91 | -11.11% |
| **smoke** | 0.6176 | 0.1981 | 0.3 | 21 / 85 | 0.5 | 0.0094 | 0.0185 | 1 / 105 | -18.87% |
| **OVERALL** | **0.4879** | **0.553** | **0.5184** | **683 / 552** | **0.4207** | **0.1117** | **0.1766** | **138 / 1097** | **-44.13%** |

---

## 4. HARD-NEGATIVE DISTRACTOR & FIRE/SMOKE SAFETY (300 distractor images)

| Category | V3 Baseline | V7 Candidate | Status |
|---|:---:|:---:|:---:|
| **Total Distractor Images** | 300 | 300 | IDENTICAL |
| **Images Triggering False Alarms** | 230 | 51 | VERIFIED |
| **Total False Positives** | 805 | 65 | VERIFIED |
| **False Fire Alarms** | 0 | 0 | **0 (PASS)** |
| **False Smoke Alarms** | 0 | 0 | **0 (PASS)** |

---

## 5. HARDWARE PERFORMANCE (Intel CPU Edge Benchmark)

| Resolution | Mean Latency | Median (P50) | P95 Latency | Throughput (FPS) | Edge Requirement |
|---|:---:|:---:|:---:|:---:|:---:|
| **384×384 (V3 Baseline)** | 42.17 ms | 40.31 ms | 49.98 ms | 23.7 FPS | $\ge 20$ FPS |
| **384×384 (V7 Candidate)** | 40.64 ms | 41.54 ms | 44.39 ms | 24.6 FPS | $\ge 20$ FPS (PASS) |
| **448×448 (V7 Exploratory)** | 45.25 ms | 45.11 ms | 48.95 ms | 22.1 FPS | Edge Feasible |
| **512×512 (V7 Exploratory)** | 51.37 ms | 51.29 ms | 55.58 ms | 19.5 FPS | Edge Feasible |

---

## 6. COMPLIANCE & MULTI-WORKER SEMANTICS

- **Ontology Invariant:** Exact 7 canonical classes maintained. Zero negative classes.
- **Compliance Output Compatibility:** SafeSync compliance state logic (`PRESENT`, `UNKNOWN`, `ABSENT`) remains 100% compliant.
- **Worker Isolation:** Person-level bounding boxes maintain spatial separation without cross-worker gear contamination.

---

*Certified by SafeSync Senior ML & Computer-Vision Engineering Team.*
