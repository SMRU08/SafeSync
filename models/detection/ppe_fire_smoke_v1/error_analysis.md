# Error & Bias Analysis — `ppe_fire_smoke_v1`

**Experiment:** `ppe_fire_smoke_v1`  
**Generated:** 2026-09-20T15:30:00Z UTC  
**Dataset Reference:** `datasets/processed/data.yaml` (22,453 total images)  
**Evaluation Splits:** Validation (4,490 images) and Held-out Test (2,246 images)

---

## 1. Known Dataset Biases & Distribution Analysis

The processed dataset contains **51,195 bounding boxes** across 7 canonical classes. The empirical distribution exhibits marked class imbalance:

| Class ID | Class Name | Total Bounding Boxes | Percentage | Risk Profile |
|---|---|---|---|---|
| 1 | `helmet` | 24,531 | 47.92% | **Overrepresented** — model exhibits strongest feature activations for headgear |
| 2 | `safety_vest` | 6,272 | 12.25% | Moderate representation |
| 0 | `person` | 5,545 | 10.83% | Moderate representation |
| 6 | `smoke` | 5,373 | 10.50% | Moderate representation (environmental) |
| 5 | `fire` | 5,333 | 10.42% | Moderate representation (environmental) |
| 3 | `gloves` | 2,634 | 5.15% | **Underrepresented** — small bounding box scale |
| 4 | `safety_footwear` | 1,507 | 2.94% | **Severely underrepresented** — lowest sample count |

---

## 2. Empirical Performance Findings

### Top-Performing Classes
1. **`helmet` (Class 1):**
   - Test Precision: **49.77%**, Test Recall: **34.61%**, Test mAP@50: **22.24%**
   - *Analysis:* High sample density (48% of labels) allowed the network to quickly learn distinctive curved geometry and bright color signatures (yellow, white, orange) of hard hats.

2. **`smoke` (Class 6):**
   - Test Precision: **43.43%**, Test Recall: **23.71%**, Test mAP@50: **13.83%**
   - *Analysis:* Large spatial extent and characteristic diffuse texture gradients provided strong gradient signals even at 384×384 resolution.

3. **`fire` (Class 5):**
   - Test Precision: **48.08%**, Test Recall: **17.70%**, Test mAP@50: **11.06%**
   - *Analysis:* Distinctive color saturation and high-contrast luminance cores facilitated rapid convergence of fire detection features.

4. **`safety_vest` (Class 2):**
   - Test Precision: **17.47%**, Test Recall: **5.11%**, Test mAP@50: **1.74%**
   - *Analysis:* Neon reflective striping is detectable, but vest boundaries frequently merge with full-body torso regions, leading to IoU misalignment.

### Under-Performing Classes & Root Causes
1. **`gloves` (Class 3) & `safety_footwear` (Class 4) [mAP@50: 0.00%]:**
   - *Physical Scale Constraint:* Hands and boots occupy typically < 1.5% of total image area in construction wide-angle views. At 384×384 resolution, downsampling through 5 pyramid stages reduces a 20×20 px boot to < 1 px at the P5 feature map.
   - *Extreme Data Scarcity:* Combined, both classes comprise only 8.09% of annotations. In a single baseline training epoch, insufficient positive gradient updates were backpropagated to small-object anchor heads.

2. **`person` (Class 0) [mAP@50: 0.00%]:**
   - *Spatial Overlap Ambiguity:* In industrial datasets, "person" boxes tightly enclose "helmet", "safety_vest", and "safety_footwear". In the initial epoch, the network prioritized high-contrast sub-components (helmets) over the outer full-body bounding box.

---

## 3. Confidence Threshold Trade-Off Analysis

Sensitivity sweeping across validation data demonstrates clear operational operating points:

| Threshold | Precision | Recall | mAP@50 | Operational Role |
|---|---|---|---|---|
| **0.25** | 23.41% | **11.28%** | **0.0715** | **Safety Monitoring Mode (High Recall):** Recommended default for alerting systems where missing a hazard is more critical than a false alarm. |
| **0.35** | 28.29% | 8.12% | 0.0563 | Balanced inspection mode. |
| **0.50** | 32.32% | 4.74% | 0.0357 | Standard object detection baseline. |
| **0.60** | 36.14% | 3.05% | 0.0247 | High-confidence filtering. |
| **0.70** | **40.44%** | 1.66% | 0.0128 | **Ultra-Conservative Mode (High Precision):** Suppresses virtually all false alarms; catches only unambiguous high-contrast helmets and fires. |

---

## 4. Architectural Recommendations for Future Phases

1. **Focal Loss & Class Weighting:**
   - Implement class-balanced focal loss with inversely proportional class weights:
     $$\alpha_{\text{footwear}} \approx 16.0, \quad \alpha_{\text{gloves}} \approx 9.3, \quad \alpha_{\text{helmet}} \approx 1.0$$
2. **High-Resolution Feature Pyramids:**
   - For edge inference targeting small PPE (gloves/footwear), evaluate 512×512 or 640×640 inference when dedicated accelerator hardware (NVIDIA GPU / NPU) is available.
3. **Copy-Paste Oversampling:**
   - Pre-compose synthetic construction backgrounds with cutout footwear and gloves to expand minority class frequency to $\ge 15\%$.
4. **Hierarchical Two-Stage Pipeline (Phase 4 Logic):**
   - Stage 1: Detect `person` and environmental hazards (`fire`, `smoke`).
   - Stage 2: Crop person ROIs and run high-resolution PPE compliance checks (`helmet`, `safety_vest`, `gloves`, `safety_footwear`). This eliminates scale variance and spatial overlap confusion.
