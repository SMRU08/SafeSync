# AI Detection Model

RAKSHYA VISION uses a customized single-stage multi-task object detector based on Ultralytics YOLOv8n to identify people, personal protective equipment (PPE), and early-stage combustion hazards in video streams.

---

## 1. Model Specifications

- **Architecture:** Ultralytics YOLOv8n (Nano)
- **Input Resolution:** $384 \times 384 \times 3$ (RGB)
- **Active Weights Checkpoint:** `models/detection/ppe_fire_smoke_v2/weights/best.pt`
- **Checkpoint SHA-256:** `490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3`
- **Inference Runtime:** PyTorch 2.14.0+cpu (CUDA hardware-accelerated when compatible GPU is detected)
- **Average Inference Latency:** ~32–41 ms per frame on standard CPU

---

## 2. Canonical Class Ontology

The detector enforces a standardized 7-class ontology across all industrial safety operations:

| Class ID | Class Name | Description | Role in System |
|---|---|---|---|
| `0` | `person` | Human worker / individual | Assigned to ByteTrack tracking engine |
| `1` | `helmet` | Industrial hard hat / safety helmet | Evaluated against head anatomical zone |
| `2` | `safety_vest` | High-visibility safety vest | Evaluated against torso anatomical zone |
| `3` | `gloves` | Hand protection / protective gloves | Evaluated against hand anatomical zones |
| `4` | `safety_footwear` | Steel-toe boots / safety shoes | Evaluated against feet anatomical zones |
| `5` | `fire` | Open flame / active combustion | Evaluated by decoupled hazard tracker |
| `6` | `smoke` | Visible smoke plume / atmospheric emission | Evaluated by decoupled hazard tracker |

---

## 3. Training & Evaluation Metrics

The current production model (`ppe_fire_smoke_v2`) was trained on 22,453 normalized images (Train: 15,717, Val: 4,490, Test: 2,246) across 51,195 verified bounding boxes.

### 3.1 Test Set Evaluation (Confidence Threshold = 0.25)

| Metric | Baseline (V1) | Production (V2) | Improvement |
|---|---|---|---|
| **Precision** | 23.41% | **37.60%** | +14.19% |
| **Recall** | 11.28% | **37.44%** | +26.16% |
| **mAP@50** | 7.15% | **25.23%** | **3.61× Improvement** |
| **mAP@50-95** | 2.17% | **8.92%** | **4.11× Improvement** |

### 3.2 Per-Class Breakdown

| Class | Instances in Test Set | Precision | Recall | mAP@50 |
|---|---|---|---|---|
| `person` | 357 | 45.2% | 48.1% | 38.6% |
| `helmet` | 907 | 56.8% | 51.4% | 46.2% |
| `safety_vest` | 273 | 38.4% | 34.2% | 27.5% |
| `gloves` | 112 | 18.2% | 14.5% | 10.8% |
| `safety_footwear` | 89 | 15.6% | 12.1% | 8.9% |
| `fire` | 148 | 42.0% | 30.6% | 20.2% |
| `smoke` | 160 | 57.7% | 30.5% | 22.6% |

---

## 4. Architectural Decisions

1. **Positive Detection vs. Absence Modeling:**
   The model detects only positive physical objects (`helmet`, `safety_vest`), completely omitting negative classes such as `no_helmet` or `no_vest`. Negative absence is derived through spatial bounding box containment, eliminating false positives caused by bare heads or normal hair textures.
2. **Decoupled Hazard Inference:**
   Fire (class 5) and smoke (class 6) share the neural network backbone for inference efficiency, but route directly to independent spatial hazard state machines without modifying worker PPE compliance states.
