# Baseline Detection Model: `ppe_fire_smoke_v1`

## Overview
- **Project:** RAKSHYA VISION — AI Vision-Based Safety Monitoring
- **Experiment:** `ppe_fire_smoke_v1`
- **Phase:** Phase 3 — Model Training & Validation
- **Architecture:** YOLOv8n (nano)
- **Framework:** Ultralytics YOLOv8 8.4.156 / PyTorch 2.14.0+cpu
- **Input Resolution:** 640 × 640 × 3 RGB

## Target Classes
The model detects the 7 canonical safety classes:
1. `person` (Class 0)
2. `helmet` (Class 1)
3. `safety_vest` (Class 2)
4. `gloves` (Class 3)
5. `safety_footwear` (Class 4)
6. `fire` (Class 5)
7. `smoke` (Class 6)

## Training Configuration
- **Dataset:** 22,453 total images (15,717 train / 4,490 val / 2,246 test)
- **Bounding Boxes:** 51,195 validated annotations across all classes
- **Hardware:** Intel(R) Core(TM) i5-13420H CPU (8 physical / 12 logical cores, 16 GB RAM)
- **Batch Size:** 16
- **Epochs:** 3 (CPU baseline)
- **Dataloader Workers:** 0 (Windows main-thread execution)
- **Augmentation:** Mosaic (1.0), Mixup (0.1), CopyPaste (0.1), Horizontal Flip (0.5), HSV tuning

## Directory Structure
```
models/detection/ppe_fire_smoke_v1/
├── weights/
│   ├── best.pt                    # Highest validation metric checkpoint
│   └── last.pt                    # Final epoch checkpoint
├── validation_samples/            # Visual prediction overlays on val set
├── model.sha256                   # SHA-256 checksum of best.pt
├── model_metadata.json            # Machine-readable model metadata
├── evaluation_metrics.json        # Detailed metrics per class and overall
├── confidence_analysis.csv        # Precision/recall across confidence thresholds
├── benchmark_results.json         # Inference latency measurements (CPU & GPU)
├── error_analysis.md              # Systematic failure analysis and bias review
├── MODEL_EVALUATION_REPORT.md     # Comprehensive evaluation report
└── README.md                      # Model documentation (this file)
```

## Checksum Verification
To verify the integrity of the trained checkpoint:
```bash
certutil -hashfile models/detection/ppe_fire_smoke_v1/weights/best.pt SHA256
```
Compare the output against `models/detection/ppe_fire_smoke_v1/model.sha256`.
