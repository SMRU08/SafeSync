# RAKSHYA VISION — Phase 10 Step 2: Model Registry & Checksum Verification Report

**Document ID:** DOC-PHASE10-STEP2  
**System:** RAKSHYA VISION (AI Vision-Based Safety Monitoring System)  
**Date:** 2026-09-21  
**Status:** **STEP 2 VERIFIED & PASSING**  

---

## 1. Executive Summary

Phase 10 Step 2 establishes the production model governance layer for RAKSHYA VISION. It ensures that the computer vision inference pipeline only executes trusted, verified neural network checkpoints whose integrity has been cryptographically validated via SHA-256 checksums before loading weights into memory.

---

## 2. Model Registry Specification

Location: [`models/registry/model_registry.yaml`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/models/registry/model_registry.yaml)

### Active Production Model
- **Model Key:** `ppe_fire_smoke_v2`
- **Version:** `2.0.0`
- **Model Path:** `models/detection/ppe_fire_smoke_v2/weights/best.pt`
- **Framework:** `Ultralytics YOLO (PyTorch)`
- **Input Size:** `[384, 384]`
- **Status:** `production`
- **Created Date:** `2026-09-20`
- **Verified Date:** `2026-09-21`
- **Canonical Classes (7):**
  - `0: person`
  - `1: helmet`
  - `2: safety_vest`
  - `3: gloves`
  - `4: safety_footwear`
  - `5: fire`
  - `6: smoke`

### Cryptographic SHA-256 Checksum
- **Actual Measured SHA-256:**
  `490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3`
- **Companion File Match:** Verified against `models/detection/ppe_fire_smoke_v2/model.sha256`.
- **Integrity Validation:** **PASS (Bitwise Exact Match)**

### Supported Model States in Registry
1. **`production`:** Active model deployed for live inference (`ppe_fire_smoke_v2`).
2. **`candidate`:** Pre-release model evaluated under shadow or benchmark modes (`ppe_fire_smoke_v2_candidate`).
3. **`archived`:** Historical models retained for reproducibility and rollback (`ppe_fire_smoke_v1`).

---

## 3. ModelLoader Architecture & Enforcement Flow

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
Locate Weight File: models/detection/ppe_fire_smoke_v2/weights/best.pt
    │
    ├─ File Missing? ──> Raise FileNotFoundError
    │
    ▼
Compute SHA-256 Checksum (in 64KB chunks)
    │
    ├─ Checksum Mismatch? ──> STOP. Raise ValueError:
    │                         "MODEL CHECKSUM VERIFICATION FAILED"
    │
    ▼ (Checksum Match Confirmed)
Instantiate Ultralytics YOLO(weights)
    │
    ▼
Verify Canonical 7-Class Ontology
    │
    ▼
Model Successfully Initialized & Cached in Singleton
```

---

## 4. Automated Tests Executed

Automated test suite implemented in [`backend/tests/test_model_registry_phase10.py`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/backend/tests/test_model_registry_phase10.py):

| Test Case | Scenario | Expected Behavior | Actual Result |
|---|---|---|---|
| `test_registry_file_structure_and_statuses` | Verify registry loads and contains `production`, `candidate`, `archived` models | All three statuses present and retrievable | **PASS** |
| `test_valid_checksum_model_loads` | Load production model with authentic SHA-256 | Model loads into memory, 7 classes validated | **PASS** |
| `test_invalid_checksum_model_rejected` | Load with corrupt/tampered expected SHA-256 | Execution stops; raises `MODEL CHECKSUM VERIFICATION FAILED` | **PASS** |
| `test_missing_model_file_error` | Request missing weights file | Raises `FileNotFoundError` with clear description | **PASS** |
| `test_missing_registry_file_error` | Point to non-existent registry YAML | Raises `FileNotFoundError` with clear description | **PASS** |
| `test_malformed_registry_file_error` | Load malformed YAML syntax | Raises `ValueError` with `Malformed model registry` | **PASS** |
| `test_registry_missing_models_key_error` | Load registry missing `models` key | Raises `ValueError` with `Missing 'models' mapping` | **PASS** |

### Test Suite Execution Summary
- **Pytest Suite:** **88 / 88 tests PASSED (100% passing in 13.12s)**
  - Existing Phase 1–9 baseline: 81 tests
  - Phase 10 Step 2 tests: 7 tests
- **Integration Test Suite:** **39 / 39 scenarios PASSED (100% passing)**

---

## 5. Limitations & Future Operational Guidance

1. **Static Weights Only:** The SHA-256 enforcement targets static YOLO `.pt` weight checkpoints. If weights are updated, the registry must be updated with the new hash via controlled release procedures.
2. **Local Registry File:** Currently stored in `models/registry/model_registry.yaml`. In multi-node cloud deployments, the registry can be mirrored from a central artifact store (e.g. MLflow or AWS S3).
