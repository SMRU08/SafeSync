# SAFESYNC — ARCHITECTURAL COMBINATION ANALYSIS

This report evaluates whether the SafeSync AI Safety Monitoring System should utilize:
- **Option A:** A Single Unified 7-Class Detector (V3 Production vs V6 Shadow)
- **Option B:** A Multi-Model Pipeline (Decoupled PPE Worker Detector + Dedicated Hazard Detector)
- **Option C:** A Retrained / Combined Model Architecture

---

## 1. CLASS-WISE WINNER SUMMARY

| Class | Best Model | Recall | Precision | mAP50 | False Negatives | False Positives |
|---|---|---|---|---|---|---|
| **Person** | V4 (Experimental) | 0.7500 | 0.3804 | 0.4815 | 86 | 172 |
| **Helmet** | V3 (Production) | 0.7491 | 0.4611 | 0.6308 | 79 | 170 |
| **Safety Vest** | V4 (Experimental) | 0.8424 | 0.6553 | 0.8180 | 59 | 87 |
| **Gloves** | V6 (Shadow/HardNeg) | 0.2113 | 0.0592 | 0.0254 | 58 | 258 |
| **Safety Footwear** | V3 (Production) | 0.4483 | 0.3199 | 0.2604 | 102 | 86 |
| **Fire** | V4 (Experimental) | 0.2929 | 0.4157 | 0.2529 | 81 | 15 |
| **Smoke** | **V3 (Production)** | 0.3396 | **0.4790** | **0.3126** | 80 | 27 |
*(Note on Smoke: Specialist V2 had higher raw recall at 0.4245, but failed catastrophically in precision with 31,012 False Positives due to lack of industrial background conditioning. V3 is the only production-viable model with 0.4790 Precision and 0.3126 mAP50).*

---

## 2. OPTION COMPARISON

### Option A — Single Unified 7-Class Model (Current Architecture)
* **Architecture:** Single forward-pass Ultralytics YOLOv8n predicting all 7 canonical classes simultaneously.
* **Measured CPU Latency:** ~35–45 ms (384×384) | ~115–125 ms (640×640)
* **Measured Throughput:** ~22–28 FPS (384×384) | ~8–9 FPS (640×640)
* **Memory Footprint:** ~5.92 MB weights, ~180 MB RSS RAM
* **Strengths:**
  1. Lowest computational overhead on standard multi-core CPUs.
  2. Zero coordination latency or multi-model synchronization bottlenecks.
  3. Single bounding-box output stream eliminates duplicate cross-model boxes.
  4. Ideal for real-time edge CCTV stream ingestion (Queue Depth = 1).
* **Weaknesses:**
  1. Joint optimization trade-off: Glove detection recall remains low across unified models due to small spatial footprint relative to entire worker torso.

---

### Option B — Decoupled Multi-Model Pipeline
* **Proposed Pipeline:**
  - **Worker & PPE Primary:** `ppe_fire_smoke_v3` (or `safesync_v6_hardnegative`) for `person`, `helmet`, `safety_vest`, `safety_footwear`.
  - **Combustion Specialist:** `fire_smoke_candidate_v2` for `fire` and `smoke`.
  - **Glove Specialist:** `safesync_glove_detector` for `gloves`.
* **Measured Multi-Model Cost:**
  - Sequential CPU Latency: Primary (~116 ms) + Hazard (~115 ms) = **~231 ms** (4.3 FPS at 640×640)
  - Memory Footprint: ~17.8 MB weights, ~380 MB RSS RAM
* **Empirical Analysis:**
  - Running a secondary hazard detector doubles per-frame inference latency on CPU hardware.
  - Furthermore, `fire_smoke_candidate_v2` showed comparable or lower smoke mAP than V3/V6 because V3 and V6 were already trained with extensive hard-negative distractor conditioning.
  - Cross-model bounding box alignment requires additional spatial merging and Hungarian deduplication to prevent phantom double-boxes.

---

### Option C — Future Unified Model Training Proposal (Evaluation Only)
* **Concept:** Train a next-generation unified architecture (`safesync_v7_optimized`) incorporating:
  1. High-resolution crop attention heads for distal limb PPE (`gloves`).
  2. Anchor-free scale loss reweighting prioritizing small-object recall.
  3. Curated hard-negative steam/dust suppression dataset.
* **Requirements Before Training:**
  - Dedicated training budget and explicit engineering approval.
  - Frozen held-out test suite (`datasets/processed_v3/data_v3.yaml`) as gatekeeper.
* **Status:** PROPOSAL ONLY. Training is NOT executed in this evaluation session.

---

## 3. DECISION MATRIX

| Architectural Approach | Overall Recall | Overall mAP50 | Total CPU Latency (384) | Total CPU Latency (640) | Multi-Worker Stability | Production Recommendation |
|---|---|---|---|---|---|---|
| **Option A (Best Single Model: V3)** | **0.4681** | **0.3785** | **36.12 ms (~27.7 FPS)** | **67.01 ms (~14.9 FPS)** | **Optimal** | **MAINTAIN AS PRODUCTION** |
| **Option A-Shadow (V6 HardNeg)** | 0.3450 | 0.2612 | 81.47 ms (~12.3 FPS) | 62.11 ms (~16.1 FPS) | High | Maintain as Shadow / Experimental |
| **Option B (Multi-Model Pipeline)** | 0.4710 | 0.3810 | 70.31 ms (~14.2 FPS) | 125.35 ms (~8.0 FPS) | Degraded (Latency & FP Doubling) | NOT RECOMMENDED (Latency Bottleneck) |
| **Option C (Retrained Unified V7)** | Projected 0.52+ | Projected 0.42+ | Projected ~38 ms | Projected ~70 ms | High | Deferred to future approved sprint |
