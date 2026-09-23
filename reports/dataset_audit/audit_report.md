# Dataset Audit & Annotation Quality Report — RAKSHYA VISION

## 1. Executive Summary

This audit evaluates the 4 approved source datasets for the **RAKSHYA VISION Safety Intelligence Pipeline** before model training and deployment. Original raw data directories remain strictly immutable and untouched.

| Dataset Name | Source / Universe | License | Total Images | Total Annotations | Canonical Target |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PPE Detection & Compliance** | `izanagi/ppe-detection-and-compliance` | CC BY 4.0 | 9,663 | 39,510 | Dedicated PPE Model |
| **Construction PPE** | `skcet-g4h72/construction-ppe-rdhzo` | CC BY 4.0 | 1,124 | 5,325 | Dedicated PPE Model |
| **Hard Hat Workers** | `public.roboflow.com/hard-hat-workers` | Public Domain | 7,035 | 27,039 | Dedicated PPE Model |
| **D-Fire (Fire & Smoke)** | `DFireDataset` / Roboflow | CC BY 4.0 | 4,631 | ~8,900 | Dedicated Hazard Model |
| **TOTAL** | — | — | **22,453** | **71,874+** | — |

---

## 2. Dataset Quality & False Positive Root-Cause Analysis

### Problem 1: Unhelmeted Heads & "NO-Helmet" Class Treatment
- In `ppe_detection_compliance`, there are **3,665** bounding boxes labeled `NO-Helmet`.
- In `construction_ppe`, there are **993** bounding boxes labeled `no hat`.
- In `hard_hat_workers`, there are **6,677** bounding boxes labeled `head`.
- **Root Cause of Hair $\rightarrow$ Helmet Confusion**: When previous naive training routines simply dropped `head` or `NO-Helmet` annotations without converting them into unannotated negative regions, the model learned that round human craniums in worker contexts correlated with helmets.
- **Correction Strategy**:
  1. No synthetic `no_helmet` class in the model (non-compliance is derived through spatial absence + temporal confirmation).
  2. Images containing workers with bare heads, curly hair, caps, and hoods are incorporated as **Hard Negatives** (with `person` labeled, but 0 `helmet` boxes). This teaches the loss function that human hair on a person produces zero helmet score.

### Problem 2: Casual Clothing & "NO-Vest" Class Treatment
- In `ppe_detection_compliance`, there are **2,714** bounding boxes labeled `NO-Vest`.
- In `construction_ppe`, there are **1,370** bounding boxes labeled `no vest`.
- **Root Cause of Shirt $\rightarrow$ Vest Confusion**: Ordinary casual shirts (navy, blue, black, white, red, brown, khaki) were appearing on workers without explicit penalty when mispredicted as vests.
- **Correction Strategy**:
  1. No synthetic `no_vest` class in the model.
  2. In the spatial pipeline, enforce high-visibility fluorescent chroma (fluorescent yellow-green `H: 24-60`, fluorescent orange `H: 5-22`) and retro-reflective silver tape (`S <= 65, V >= 190`). Casual monochrome shirts lacking these optical properties are rejected as false positives.

### Problem 3: Class Pollution (Mixing Fire/Smoke into PPE Model)
- Previous models combined fire, smoke, and PPE into a single 7-class YOLO head.
- This creates multi-task competition in the backbone and feature pyramid, diluting gradients for small PPE items (gloves, footwear) and causing thermal/light patterns to cross-interfere with worker clothing.
- **Correction Strategy**:
  - Complete decoupling into two dedicated models:
    1. **PPE Model** (`models/ppe/`): `person`, `helmet`, `safety_vest`, `gloves`, `safety_footwear`.
    2. **Hazard Model** (`models/hazards/`): `fire`, `smoke`.

---

## 3. Class Normalization & Canonical Schema

```
Target PPE Classes (Dedicated PPE Model):
  0: person
  1: helmet
  2: safety_vest
  3: gloves
  4: safety_footwear

Target Hazard Classes (Dedicated Hazard Model):
  0: fire
  1: smoke
```

Strict Negative Policy:
- Disallowed classes: `no_helmet`, `no_vest`, `no_gloves`, `no_footwear`, `no-mask`, `no-goggles`.
- Absence is evaluated downstream by the **Safety Engine** using:
  $$\text{Person Track} + \text{Spatial Association} + \text{Visibility Check} + \text{Temporal Confirmation (5 frames)}$$

---

## 4. Hard Negatives Set Composition

The dedicated hard-negative set consists of images of workers and individuals in industrial and outdoor settings with:
- Natural dark, black, and brown hair
- Blonde, grey, and curly hair
- Baseball caps, beanies, and winter hoods
- Dark navy, black, and grey casual t-shirts and polos
- Light white and beige cotton shirts
- Patterned and plaid shirts
- Backpacks and carried tools across the chest

When these images pass through the model and associator, the expected output is:
$$\text{Helmet: ABSENT, Vest: ABSENT, Overall: NON-COMPLIANT (Zero False Positives)}$$
