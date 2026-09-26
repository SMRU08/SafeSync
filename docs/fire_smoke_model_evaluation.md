# SafeSync Fire & Smoke Model Evaluation & Challenge Report

## 1. Executive Summary

This report documents the rigorous evaluation of the SafeSync Fire & Smoke baseline model (`ppe_fire_smoke_v2`) and the experimental candidate model (`hazard_candidate_v2`) on:
1. Standard Validation and Test Splits
2. 15-Scenario Real-World Optical Challenge Benchmark
3. CPU Pipeline Latency and Throughput

---

## 2. Standard Benchmark Metrics Comparison

### Validation Split (`val`)

| Class | Model | Precision | Recall | mAP@50 | mAP@50-95 | F1 Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fire** | **Baseline (`ppe_fire_smoke_v2`)** | **45.02%** | **26.79%** | **17.96%** | **7.16%** | **0.336** |
| **Fire** | Candidate (`candidate_v2`) | 100.0% | 0.00% | 0.10% | 0.03% | 0.000 |
| **Smoke** | **Baseline (`ppe_fire_smoke_v2`)** | **52.62%** | **29.02%** | **22.27%** | **8.92%** | **0.374** |
| **Smoke** | Candidate (`candidate_v2`) | 5.60% | 12.00% | 2.40% | 0.60% | 0.076 |
| **ALL** | **Baseline (`ppe_fire_smoke_v2`)** | **48.82%** | **27.91%** | **20.12%** | **8.04%** | **0.355** |
| **ALL** | Candidate (`candidate_v2`) | 52.80% | 6.00% | 1.23% | 0.33% | 0.108 |

### Test Split (`test`)

| Class | Model | Precision | Recall | mAP@50 | mAP@50-95 | F1 Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fire** | **Baseline (`ppe_fire_smoke_v2`)** | **41.99%** | **30.62%** | **20.15%** | **9.02%** | **0.354** |
| **Fire** | Candidate (`candidate_v2`) | 0.00% | 0.00% | 0.00% | 0.00% | 0.000 |
| **Smoke** | **Baseline (`ppe_fire_smoke_v2`)** | **57.74%** | **30.48%** | **22.62%** | **8.56%** | **0.399** |
| **Smoke** | Candidate (`candidate_v2`) | 12.50% | 28.90% | 7.30% | 2.40% | 0.174 |
| **ALL** | **Baseline (`ppe_fire_smoke_v2`)** | **49.87%** | **30.55%** | **21.39%** | **8.79%** | **0.377** |
| **ALL** | Candidate (`candidate_v2`) | 56.20% | 14.40% | 3.65% | 1.20% | 0.229 |

---

## 3. Real-World 15-Scenario Challenge Benchmark

Tested against 15 synthetic and modeled environmental challenges:

| Challenge Scenario | Target Type | Baseline FP (`ppe_fire_smoke_v2`) | Candidate FP (`candidate_v2`) |
| :--- | :--- | :--- | :--- |
| **Steam** | Negative | **CLEAN (0 FP)** | False Alarm (1) |
| **Dust** | Negative | **CLEAN (0 FP)** | CLEAN (0 FP) |
| **Fog** | Negative | **CLEAN (0 FP)** | CLEAN (0 FP) |
| **Vehicle Exhaust** | Negative | **CLEAN (0 FP)** | False Alarm (1) |
| **Welding Glare** | Negative | **CLEAN (0 FP)** | False Alarm (1) |
| **Sunlight Glare** | Negative | **CLEAN (0 FP)** | CLEAN (0 FP) |
| **Specular Reflections** | Negative | **CLEAN (0 FP)** | False Alarm (1) |
| **White Walls** | Negative | **CLEAN (0 FP)** | CLEAN (0 FP) |
| **Orange / Red Clothing** | Negative | **CLEAN (0 FP)** | False Alarm (1) |
| **Industrial Lighting** | Negative | **CLEAN (0 FP)** | False Alarm (1) |
| **CCTV Compression** | Negative | **CLEAN (0 FP)** | False Alarm (1) |
| **Motion Blur** | Negative | **CLEAN (0 FP)** | CLEAN (0 FP) |
| **Real Industrial Scene** | Negative | **CLEAN (0 FP)** | False Alarm (1) |
| **Small Distant Smoke** | Positive | Detected (Candidate) | Detected (Candidate) |
| **Small Distant Fire** | Positive | Detected (Candidate) | Missed |
| **Total False Positives** | — | **0 / 13 (0.0% FP)** | **8 / 13 (61.5% FP)** |

---

## 4. CPU Performance & Latency Benchmark

Measured on 13th Gen Intel Core i5-13420H @ 1280x720 (50 timed runs):

| Stage | Mean (ms) | P50 (ms) | P95 (ms) | P99 (ms) |
| :--- | :--- | :--- | :--- | :--- |
| **YOLO Inference** | 56.40 | 56.06 | 60.09 | 67.46 |
| **ByteTrack Tracking** | 0.01 | 0.01 | 0.02 | 0.02 |
| **PPE Association** | 0.00 | 0.00 | 0.00 | 0.00 |
| **Temporal State Machine**| 0.00 | 0.00 | 0.00 | 0.01 |
| **Total E2E Pipeline** | **56.45** | **56.10** | **60.13** | **67.50** |

- **Effective AI Processing Rate**: **17.7 FPS**
- **Camera Capture Rate**: Decoupled background worker targeting **30.0 FPS**
- **Queue Depth**: 1 (latest-frame-wins; no memory buffer growth)

---

## 5. Model Selection Decision

Per SafeSync Production Directive Section 17:
> *"Promote the candidate only if fire/smoke accuracy improves meaningfully and false positives do not become unacceptable. If the candidate is worse: KEEP THE EXISTING PRODUCTION MODEL. Document why."*

### Final Verdict: KEEP BASELINE MODEL `ppe_fire_smoke_v2`
- **Rationale**:
  1. The baseline model exhibits **0% false alarms** on the 13 negative optical challenges, whereas the 2-epoch candidate produced false alarms in 8 scenarios.
  2. The baseline mAP@50 (20.15% fire, 22.62% smoke) is substantially higher than the under-converged candidate (0.10% fire, 2.40% smoke).
  3. The 7-stage temporal state machine and spatial consistency gates in SafeSync provide the necessary false-positive rejection on top of `ppe_fire_smoke_v2`.
- **Active Model Path**: `models/detection/ppe_fire_smoke_v2/weights/best.pt`
- **SHA-256 Checksum**: `490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3`
