# SAFESYNC — FINAL MODEL BENCHMARK RECOMMENDATION

**Date:** 2026-10-07  
**Evaluation Role:** Senior Computer Vision / YOLO ML Engineer  
**Status:** Evaluation-Only Complete (Zero Production Checkpoint Alteration)  

---

## 1. PRIMARY VERDICT: KEEP EXISTING PRODUCTION MODEL (V3)

### Recommendation:
**Retain `models/detection/ppe_fire_smoke_v3/weights/best.pt` as the active Production Model.**

### Justification:
1. **Safety-Critical Balance:** V3 delivers the highest overall Recall (0.4681) and mAP50 (0.3785) across the complete 7-class ontology on the 410-image held-out test suite with the lowest False Negatives (590).
2. **Real-Time Edge Performance:** V3 executes in **36.12 ms on CPU at 384×384 (~27.7 FPS)** (and 67.01 ms at 640×640), satisfying SafeSync's zero-lag stream ingestion invariant (`Queue Depth = 1`).
3. **No Latency Regression:** Multi-model ensembling (Option B) degrades CPU frame rate from 27.7 FPS down to 14.2 FPS (384) and 8.0 FPS (640), violating real-time monitoring criteria without offering substantial recall gains.
4. **V6 Hard-Negative Role:** V6 (`safesync_v6_hardnegative`) demonstrates superior false-positive suppression on steam/glare distractors, but incurs a minor recall drop on small gear. V6 should remain designated as the **Shadow Evaluation Model**.

---

## 2. PRODUCTION SAFETY LOCK CONFIRMATION
* **Production Model:** `models/detection/ppe_fire_smoke_v3/weights/best.pt`
* **V3 SHA-256:** `9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe` (UNTOUCHED: 100% MATCH)
* **Shadow Model:** `models/detection/safesync_v6_hardnegative/weights/best.pt`
* **V6 SHA-256:** `c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc` (UNTOUCHED: 100% MATCH)
* **Production Configuration:** UNMODIFIED.

---

## 3. NEXT STEPS (FOR FUTURE APPROVED WORK)
* Do NOT retrain or replace V3 automatically.
* Future work should explore a curated small-object glove augmentation strategy within a single unified checkpoint only after formal sign-off.
