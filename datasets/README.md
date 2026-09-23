# Datasets Directory — RAKSHYA VISION

This directory manages training, validation, testing, and hard-negative data for the **RAKSHYA VISION Safety & Hazard Monitoring System**.

## Directory Structure

```
datasets/
├── raw/                     # Original, immutable raw source datasets (read-only)
│   ├── ppe_detection_compliance/
│   ├── construction_ppe/
│   ├── hard_hat_workers/
│   └── d_fire/
├── processed/               # Normalized, class-mapped datasets for training & evaluation
├── manifests/               # Dataset provenance manifests and canonical class taxonomies
│   ├── dataset_manifest.yaml
│   └── canonical_classes.yaml
├── reports/                 # Comprehensive audit reports and quality inspections
├── samples/                 # Representative visual samples for verification
└── README.md
```

## Approved Source Datasets

1. **PPE Detection & Compliance** (`izanagi/ppe-detection-and-compliance`)
   - 9,663 images, CC BY 4.0 license.
   - Provides primary PPE classes + explicit negative non-PPE samples (`NO-Helmet`, `NO-Vest`).
2. **Construction PPE** (`skcet-g4h72/construction-ppe-rdhzo`)
   - 1,124 images, CC BY 4.0 license.
   - Construction site workers with hard hats and safety vests.
3. **Hard Hat Workers** (`public.roboflow.com/hard-hat-workers`)
   - 7,035 images, Public Domain license.
   - High-volume person, helmet, and unhelmeted head dataset.
4. **D-Fire & Smoke Hazard Dataset** (`DFireDataset`)
   - 4,631 images, CC BY 4.0 license.
   - Dedicated fire and smoke hazard dataset for decoupled emergency detection.

## Canonical Classes

### PPE Model (`models/ppe/`)
- `0: person`
- `1: helmet`
- `2: safety_vest`
- `3: gloves`
- `4: safety_footwear`

### Hazard Model (`models/hazards/`)
- `0: fire`
- `1: smoke`