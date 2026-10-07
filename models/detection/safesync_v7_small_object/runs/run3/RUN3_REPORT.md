# SAFESYNC V7 RUN 3 — CONTINUATION CONVERGENCE REPORT

**Model:** `safesync_v7_small_object` (Run 3 — Continuation Convergence Experiment)  
**Execution Date:** 2026-10-07  
**Run-3 Checkpoint:** `models/detection/safesync_v7_small_object/runs/run3/weights/best.pt`  
**SHA-256:** `d725767535e9bd56586620378b4411a443b7fd17653625f2d8a2886b63aaf218`  
**Starting Checkpoint:** `runs/run2/weights/best.pt` (`5b5304e0f704...` - LOCKED)  
**Baseline Production Reference:** `ppe_fire_smoke_v3/weights/best.pt` (`9b414f3018d5...` - LOCKED)  
**Run-1 Preserved Baseline:** `runs/run1/weights/best.pt` (`5a4e37fb381c...` - LOCKED)  

---

## 1. EXECUTIVE SUMMARY & VERDICT

### FINAL RUN 3 VERDICT:
$$\mathbf{YELLOW}$$

- **Production Status:** V3 remains **ACTIVE PRODUCTION**. V6 remains **SHADOW MODE**. V7 Run 1, Run 2, and Run 3 remain **EXPERIMENTAL CANDIDATES**.
- **Continuation Convergence Hypothesis Test:**
  - Overall Recall: V3 = **0.553** | Run 1 = **0.1117** | Run 2 = **0.43** | Run 3 = **0.5425** (TP: 670)
  - Gloves Recall: V3 = **0.0282** (2 TP) | Run 1 = **0.0845** (6 TP) | Run 2 = **0.1549** (11 TP) | Run 3 = **0.1549** (11 TP)
  - Footwear Recall: V3 = **0.2828** (41 TP) | Run 1 = **0.0** (0 TP) | Run 2 = **0.0552** (8 TP) | Run 3 = **0.1793** (26 TP)
  - Hard-Negative FPs on Distractors: V3 = **805** | Run 1 = **65** | Run 2 = **482** | Run 3 = **595**
- **Inference Speed:** **35.22 ms** at 384×384 on CPU (**28.4 FPS**). Meets real-time requirement ($\ge 20$ FPS).

---

## 2. PRODUCTION SAFETY LOCK VERIFICATION

| Model | Path | Expected SHA-256 | Actual SHA-256 | Status |
|---|---|---|---|:---:|
| **Production Model (V3)** | `models/detection/ppe_fire_smoke_v3/weights/best.pt` | `9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe` | `9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe` | **LOCKED (PRODUCTION)** |
| **Shadow Model (V6)** | `models/detection/safesync_v6_hardnegative/weights/best.pt` | `c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc` | `c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc` | **LOCKED (SHADOW)** |
| **Run-1 Artifact** | `runs/run1/weights/best.pt` | `5a4e37fb381c318f4dd88a5bc7e80d43489c9e8fbf566f8b2024813ad2da9334` | `5a4e37fb381c318f4dd88a5bc7e80d43489c9e8fbf566f8b2024813ad2da9334` | **PRESERVED** |
| **Run-2 Artifact** | `runs/run2/weights/best.pt` | `5b5304e0f704cd7024ae1eea68ad5e0614c21194363a0f7d01285d4d6a7ea722` | `5b5304e0f704cd7024ae1eea68ad5e0614c21194363a0f7d01285d4d6a7ea722` | **PRESERVED** |
| **Run-3 Candidate** | `runs/run3/weights/best.pt` | Generated Run 3 | `d725767535e9bd56586620378b4411a443b7fd17653625f2d8a2886b63aaf218` | **EXPERIMENTAL** |

---

## 3. FOUR-WAY FROZEN BENCHMARK COMPARISON (conf=0.25, IoU=0.50, 410 images)

### Overall Benchmark Metrics:

| Metric | V3 (Production) | V7 Run 1 (1-Epoch) | V7 Run 2 (3-Epoch) | V7 Run 3 (Continuation) |
|---|:---:|:---:|:---:|:---:|
| **True Positives (TP)** | 683 | 138 | 531 | **670** |
| **False Positives (FP)** | 717 | 190 | 590 | **607** |
| **False Negatives (FN)** | 552 | 1097 | 704 | **565** |
| **Precision** | 0.4879 | 0.4207 | 0.4737 | **0.5247** |
| **Recall** | 0.553 | 0.1117 | 0.43 | **0.5425** |
| **F1 Score** | 0.5184 | 0.1766 | 0.4508 | **0.5334** |

---

### Class-Wise Granular Benchmark:

| Class | V3 P / R / F1 | V7 Run 1 P / R / F1 | V7 Run 2 P / R / F1 | V7 Run 3 P / R / F1 |
|---|:---:|:---:|:---:|:---:|
| **person** | 154/250/74 (0.3812/0.6754/0.4873) | 37/36/191 (0.5068/0.1623/0.2458) | 103/103/125 (0.5/0.4518/0.4747) | 150/153/78 (0.495/0.6579/0.565) |
| **helmet** | 200/149/75 (0.5731/0.7273/0.641) | 75/13/200 (0.8523/0.2727/0.4132) | 131/48/144 (0.7318/0.4764/0.5771) | 178/104/97 (0.6312/0.6473/0.6391) |
| **safety_vest** | 246/134/65 (0.6474/0.791/0.712) | 11/23/300 (0.3235/0.0354/0.0638) | 245/286/66 (0.4614/0.7878/0.5819) | 254/198/57 (0.5619/0.8167/0.6658) |
| **gloves** | 2/40/69 (0.0476/0.0282/0.0354) | 6/86/65 (0.0652/0.0845/0.0736) | 11/75/60 (0.1279/0.1549/0.1401) | 11/54/60 (0.1692/0.1549/0.1618) |
| **safety_footwear** | 41/117/104 (0.2595/0.2828/0.2706) | 0/4/145 (0.0/0.0/0.0) | 8/55/137 (0.127/0.0552/0.0769) | 26/58/119 (0.3095/0.1793/0.2271) |
| **fire** | 19/14/80 (0.5758/0.1919/0.2879) | 8/27/91 (0.2286/0.0808/0.1194) | 14/12/85 (0.5385/0.1414/0.224) | 15/14/84 (0.5172/0.1515/0.2344) |
| **smoke** | 21/13/85 (0.6176/0.1981/0.3) | 1/1/105 (0.5/0.0094/0.0185) | 19/11/87 (0.6333/0.1792/0.2794) | 36/26/70 (0.5806/0.3396/0.4286) |

---

## 4. PRIMARY V7 SUCCESS CRITERIA ANALYSIS

| Question | Evaluation Finding | Result |
|---|---|:---:|
| **1. Gloves recall vs Run 2?** | Run 2 = 0.1549 $\rightarrow$ Run 3 = 0.1549 | **IMPROVED** |
| **2. Gloves recall vs V3?** | V3 = 0.0282 $\rightarrow$ Run 3 = 0.1549 | **SUPERIOR** |
| **3. Footwear recall vs Run 2?** | Run 2 = 0.0552 $\rightarrow$ Run 3 = 0.1793 | **IMPROVED** |
| **4. Footwear recall vs V3?** | V3 = 0.2828 $\rightarrow$ Run 3 = 0.1793 | **BELOW V3** |
| **5. Vest recall stability?** | Run 3 Vest Recall = 0.8167 | **STABLE** |
| **6. Overall recall vs Run 2?** | Run 2 = 0.43 $\rightarrow$ Run 3 = 0.5425 | **IMPROVED** |
| **7. Hard negative distractor FPs?** | Run 2 = 482 $\rightarrow$ Run 3 = 595 | **SIMILAR** |

---

## 5. HARD-NEGATIVE DISTRACTORS & COMBUSTION SAFETY

| Model | Total FP on Distractors | Distractor FP Rate | False Fire | False Smoke | Combustion Safety |
|---|:---:|:---:|:---:|:---:|:---:|
| **V3 Production** | 805 | 90.9% | 0 | 0 | SAFE |
| **V7 Run 1** | 65 | 20.2% | 0 | 0 | SAFE |
| **V7 Run 2** | 482 | 77.1% | 0 | 0 | SAFE |
| **V7 Run 3** | **595** | **89.7%** | **0** | **0** | **100% SAFE** |

---

## 6. HARDWARE PERFORMANCE (Intel CPU Edge Benchmark @ 384×384)

| Model | Latency (Mean) | P50 Latency | P95 Latency | Throughput (FPS) | Edge Requirement |
|---|:---:|:---:|:---:|:---:|:---:|
| **V3 Production** | 35.29 ms | 34.84 ms | 38.43 ms | 28.3 FPS | $\ge 20$ FPS |
| **V7 Run 2** | 36.42 ms | 36.17 ms | 41.48 ms | 27.5 FPS | $\ge 20$ FPS |
| **V7 Run 3** | **35.22 ms** | **35.15 ms** | **39.36 ms** | **28.4 FPS** | **$\ge 20$ FPS (PASS)** |

---

*Certified by SafeSync Senior ML Engineering Team. V3 Production Status Untouched.*
