# Dataset Strategy & Class Normalization

This document details the dataset engineering strategy, class normalization philosophy, and annotation policies adopted by SafeSync.

---

## 1. Architectural Philosophy: Positive Detection vs. Absence Classes

In vision-based industrial safety systems, attempting to detect the absence of gear (e.g. labeling bounding boxes as *NO-Helmet*, *NO-Vest*, or *NO-Gloves*) introduces fundamental machine learning failure modes:

1. **Ambiguity of Absence:** A bounding box around an unprotected head or bare hands lacks distinct visual patterns compared to the actual PPE item (which features standardized geometry, high-visibility coloration, and retroreflective materials).
2. **Context Blindness:** An unadorned head is only a safety violation if located within an active hazardous zone requiring head protection. Training a neural network to classify bare heads as violations conflates physical object detection with administrative spatial policy.
3. **Occlusion Sensitivity:** If a worker turns away or steps behind equipment, absence-based models frequently generate false positive alarms.

### 1.1 Decoupled Compliance Formula
SafeSync decouples physical object detection from operational safety rules:

$$\text{Person Detected} + \text{PPE Associated to Anatomy} = \text{Compliant}$$

$$\text{Person Detected} + \text{PPE Required in Zone} + \text{PPE Not Associated} = \text{Provisional Violation}$$

$$\text{Provisional Violation} + \text{Persistence for } N_{\text{confirm}} \ge 3 \text{ Frames} = \text{Actionable Incident}$$

---

## 2. Source Annotation Normalization

Source safety datasets frequently contain noisy, conflicting, or absence-based annotation classes:
- `NO-Helmet` / `no-helmet` / `no hat`
- `NO-Vest` / `no-vest`
- `NO-Gloves` / `no-gloves`
- `NO-Boots` / `no-boots`
- `head` / `face` / `hand`

### Normalization Rules:
1. **Raw Preservation:** All original annotations are preserved verbatim in `datasets/raw/` with verified cryptographic SHA-256 archives.
2. **Exclusion of Absence Classes:** Absence labels are strictly excluded from the processed training split (`datasets/processed/`) to avoid negative transfer and confusing the convolutional feature extractor.
3. **Canonical 7-Class Mapping:** Permitted positive labels are mapped to canonical class indices $0 \dots 6$:
   - `person` $\leftarrow$ `person`, `worker`, `human`
   - `helmet` $\leftarrow$ `helmet`, `hard-hat`, `hard_hat`
   - `safety_vest` $\leftarrow$ `vest`, `safety-vest`, `safety_vest`
   - `gloves` $\leftarrow$ `glove`, `gloves`
   - `safety_footwear` $\leftarrow$ `boot`, `boots`, `safety-boot`, `safety-shoe`
   - `fire` $\leftarrow$ `fire`, `flame`
   - `smoke` $\leftarrow$ `smoke`, `plume`
