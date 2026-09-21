# Model Registry & Checksum Verification

RAKSHYA VISION implements an explicit model governance and registry subsystem to ensure that the production inference pipeline only loads verified, untampered neural network weights.

---

## 1. Registry Architecture

The central registry configuration file is located at:
`models/registry/model_registry.yaml`

```
ModelLoader.load_model()
    │
    ▼
Read models/registry/model_registry.yaml
    │
    ▼
Resolve Target Status ("production") -> "ppe_fire_smoke_v2"
    │
    ▼
Locate Weight File -> "models/detection/ppe_fire_smoke_v2/weights/best.pt"
    │
    ▼
Compute SHA-256 Checksum of On-Disk File
    │
    ├── Checksum Match? ──► YES ──► Initialize YOLOv8 Model In-Memory
    │                                └── Log Model Name, Version & Latency
    │
    └── Checksum Mismatch? ─► NO ──► Security Exception (ModelCorruptedError)
                                     └── Safe Fallback to Last Verified Checkpoint
```

---

## 2. Model States & Governance

The registry recognizes three lifecycle states:

| Status | Definition | Routing |
|---|---|---|
| **`production`** | Verified model deployed for active real-time camera inference. | Loaded by default by `ModelLoader`. |
| **`candidate`** | Shadow or benchmarking candidate under integration testing. | Loaded during comparative benchmarks. |
| **`archived`** | Deprecated or superseded checkpoint retained for rollback. | Offline reference only. |

### Active Production Entry

```yaml
models:
  ppe_fire_smoke_v2:
    version: "2.0.0"
    status: "production"
    path: "models/detection/ppe_fire_smoke_v2/weights/best.pt"
    framework: "ultralytics_yolo"
    input_size: [384, 384]
    sha256: "490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3"
    created_at: "2026-09-20"
    verified_at: "2026-09-21"
    classes:
      0: person
      1: helmet
      2: safety_vest
      3: gloves
      4: safety_footwear
      5: fire
      6: smoke
```

---

## 3. Cryptographic Verification & Tamper Resistance

1. **Pre-Execution Checksum Calculation:**
   Before allocating PyTorch tensors or initializing weights on CPU/GPU, `ModelLoader` streams the checkpoint file in 64 KB chunks and computes its SHA-256 hash.
2. **Strict Bitwise Validation:**
   The computed digest must match the registry `sha256` value exactly. If a checkpoint is truncated, modified by malicious injection, or corrupted during deployment, loading halts with a `ModelCorruptedError`.
3. **Automated Companion Check:**
   Every model directory contains a standalone `.sha256` digest file (e.g. `models/detection/ppe_fire_smoke_v2/model.sha256`) allowing automated CI/CD pipeline integrity verification via `sha256sum -c`.
