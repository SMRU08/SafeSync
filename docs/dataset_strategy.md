# RAKSHYA VISION — Dataset & Compliance Strategy

## 1. Architectural Philosophy: Positive Object Detection vs. Absence Classes

In vision-based industrial safety systems, detecting "absence" (e.g., *NO-Helmet*, *NO-Vest*, *NO-Gloves*, *NO-Boots*) directly as primary object detection bounding boxes introduces fundamental machine learning failure modes:
1. **Ambiguity of Absence:** A bounding box around a bare head or bare hands lacks distinct visual patterns compared to the actual PPE item (which has distinct geometry, high-visibility coloration, reflective tape, or standardized contours).
2. **Context Blindness:** An unadorned head is only a violation if located within an active hazardous zone requiring head protection. Labeling it as an intrinsic violation conflates object detection with spatial policy.
3. **Occlusion Sensitivity:** Partial occlusion (e.g., worker turning away or behind machinery) frequently triggers false "NO-PPE" alarms if detection relies on absence labels.

Therefore, RAKSHYA VISION adopts a decoupled, multi-stage compliance architecture:

```
[Camera Stream / Frame]
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ Stage 1: Positive Object Detection (YOLO)               │
│ - person                                               │
│ - helmet                                               │
│ - safety_vest                                          │
│ - gloves                                               │
│ - safety_footwear                                      │
│ - fire                                                 │
│ - smoke                                                │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Stage 2: Spatial Person-PPE Association Engine         │
│ - Bounding Box Geometric Containment / IoU Overlap     │
│ - Keypoint / Anatomical Region Mapping (Head, Torso)   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Stage 3: Zone PPE Requirements & Rule Engine           │
│ - Geofenced Zone Config (Mandatory Helmet, Vest, etc.) │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Stage 4: Temporal Smoothing & Validation               │
│ - Multi-frame Persistence Filter (e.g. N of M frames)  │
│ - False-Positive Debouncing                            │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
            [COMPLIANCE / VIOLATION DECISION]
```

---

## 2. Compliance Decision Formula

$$\text{Person Detected} + \text{PPE Associated} = \text{PPE Compliant}$$

$$\text{Person Detected} + \text{PPE Required in Zone} + \text{PPE Not Associated} = \text{Potential Violation}$$

$$\text{Potential Violation} + \text{Temporal Persistence Check} = \text{Actionable Alert}$$

---

## 3. Handling of Source Dataset Absence Annotations

Source datasets often come with classes such as:
- `NO-Helmet`
- `NO-Vest`
- `NO-Gloves`
- `NO-Boots` / `no-boots`
- `no hat`
- `head`

### Policy:
1. **Raw Preservation:** All original annotations, including absence classes, are preserved verbatim in `datasets/raw/`.
2. **Normalized Dataset Filtering:** In `datasets/processed/`, absence classes are excluded from the primary YOLO detector to prevent model confusion and negative transfer.
3. **Future Head/Hand Detection Utility:** The `head` class from sources such as *Hard Hat Workers* is preserved in raw archives for potential secondary anatomical landmark verification in subsequent phases.