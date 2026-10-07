# SafeSync V7 Candidate Dataset Space & Curation Rules

> **STATUS:** PREPARED / EXPERIMENTAL ONLY | ZERO TRAINING EXECUTED IN PHASE A  
> **Production Dataset Baseline:** `datasets/processed_v3/` (Untouched, Unaltered, Preserved)  

---

## 1. Absolute Integrity Rules

1. **NO Overwrite of Existing Data:**
   - `datasets/processed_v3/` remains the frozen single source of truth for benchmark evaluation.
   - Under no circumstance shall files in `datasets/processed_v3/` be modified or deleted.
2. **Canonical 7-Class Ontology:**
   - `0: person`
   - `1: helmet`
   - `2: safety_vest`
   - `3: gloves`
   - `4: safety_footwear`
   - `5: fire`
   - `6: smoke`
   - **NO NEGATIVE CLASSES:** Never introduce `no_helmet`, `no_vest`, `no_gloves`, or `no_footwear`. Non-compliance is derived downstream by the Compliance Engine (`UNKNOWN != VIOLATION`).
   - **NO UNAUTHORIZED CLASSES:** Do not introduce goggles/glasses into the V7 ontology without enterprise authorization.
   - **NO CLASS RENAMING:** Class indices and identifiers are frozen across the platform.

---

## 2. Data Leakage Prevention (Partitioning Protocol)

To ensure scientifically valid and generalizable models:
1. **Scene / Video / Camera-Aware Splitting:**
   - Images captured from the same physical video sequence, camera angle, or background environment MUST reside within the same split (all in `train` OR all in `val`).
   - Under no circumstances shall adjacent video frames of the same worker scene be split across `train` and `val/test`.
2. **Frozen Held-Out Test Set:**
   - The test set must exactly mirror the 410 images in `datasets/processed_v3/images/test`.
   - Never copy training samples into the test partition.

---

## 3. Glove Dataset Rules

The future V7 model must learn genuine glove appearance and morphology rather than simple color heuristics:

### Positive Glove Samples:
- Varied colors: Orange, neon yellow, gray, black, blue, green, brown leather, white latex/nitrile.
- Varied materials: Heavy-duty leather rigger gloves, textured nitrile, cut-resistant Kevlar weave, electrical rubber.
- Orientations: Palm facing, dorsal facing, side profile, gripping tools, clenched fist, relaxed hand.
- Hand configurations: Left hand, right hand, both hands in frame.
- Scale & Occlusion: Partial gloves behind pipes/tools, distal gloves at 5–10m camera distance.
- Varied worker skin tones and clothing cuffs.

### Hard Negatives for Gloves (Crucial to Prevent False Alarms):
- Bare human hands and fingers.
- Bare wrists, forearms, and rolled-up sleeves.
- Yellow, orange, or high-visibility tool handles (drills, wrenches, tape measures).
- Painted machinery components, control knobs, and lever grips.
- Reflective industrial tape or metallic parts held in hands.
- **NEVER label bare hands as gloves.**

---

## 4. Footwear Dataset Rules

The model must detect industrial safety footwear based on structural protective geometry:

### Positive Footwear Samples:
- Safety boots and protective work shoes (steel-toe caps, heavy lug soles, metatarsal guards).
- Varied colors: Black, brown, tan nubuck, yellow welt, dual-tone leather.
- Diverse worker postures: Walking, standing, kneeling, crouched, climbing ladder rungs.
- Varied factory surfaces: Grated steel walkways, concrete floors, wet/oily surfaces, outdoor gravel, yellow hazard line markings.
- Partial visibility: Feet partially obscured by pallets, machinery bases, or lower tool carts.

### Hard Negatives for Footwear:
- Non-protective athletic shoes, dress shoes, sandals.
- Floor shadow pools and machine base shadows.
- Black toolboxes, rubber hoses, power cables, and floor clutter.
- Dark hazard markings and painted floor tape.

---

## 5. Fire & Smoke Protection & Independent Co-existence

V7 must maintain the robust combustion detection validated in V3:

### Positive Hazard Samples:
- Open combustion flames across scales (flickering flame to active fire).
- Expanding atmospheric smoke plumes, rising particulate clouds.

### Preserved Hard-Negative Distractors (Zero False Alarm Mandate):
- Steam boiler vents and industrial pressure relief valves.
- Welding torch flares and grinding spark showers.
- Fog, particulate dust, and vehicle exhaust fumes.
- Heat shimmer and glare from metal factory roofs.
- Yellow/orange hazard bollards and red safety cones.

### Independent Co-existence Rule:
- **Fire and smoke must be detectable regardless of whether workers are present in the frame.**
- The presence of workers/PPE must NEVER suppress a hazard bounding box.
- Conversely, hazard detections must NEVER suppress worker/PPE detections.

---

## 6. Directory Scaffolding

```
datasets/v7_candidate/
├── dataset.yaml            <- Canonical YOLO dataset definition
├── README.md               <- This specification document
├── manifests/              <- Checksums and file manifests for train/val/test
├── hard_negatives/         <- Curated background distractor images
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```
