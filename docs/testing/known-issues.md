# Known Issues & Resolved Defect Log

This document records the edge cases, architectural anomalies, and defects identified and resolved during integration testing, along with current system constraints.

---

## 1. Resolved Defect Log

| Defect ID | Component | Root Cause Description | Resolution | Status |
|---|---|---|---|:---:|
| `BUG-01` | Model Loader | Checkpoint loader raised unhandled `KeyError` when loading checkpoints without embedded class name mappings. | Added standard canonical 7-class fallback dictionary when `model.names` is absent. | **RESOLVED** |
| `BUG-02` | ByteTrack | Kalman filter state matrix threw NumPy shape error when receiving 0 worker detections for $> 30$ frames. | Added empty-array guard before Kalman prediction step to preserve matrix dimension $(8, 1)$. | **RESOLVED** |
| `BUG-03` | Hazard Spatial | Ray-casting point-in-polygon algorithm misclassified bounding box centers resting exactly on zone boundary edges. | Enforced inclusive $\le$ ray-casting intersection logic in `ZoneManager.is_point_in_polygon()`. | **RESOLVED** |
| `BUG-04` | Alert Engine | Cooldown cache key used only `worker_id`, causing false suppression if worker #1 was seen on Camera 1 and Camera 2. | Updated deduplication key to composite tuple `(camera_id, worker_id, event_type)`. | **RESOLVED** |
| `BUG-05` | Evidence Manager | File locks under Windows prevented automatic cleanup of evidence snapshots during active read streams. | Switched from persistent open file handles to contextual `with open(...)` streaming. | **RESOLVED** |
| `BUG-06` | WebSocket Router | Rapid client refresh created orphaned subscriber tasks in `EventBroadcaster`. | Added `try...finally` block to guarantee `broadcaster.unsubscribe()` execution on socket disconnect. | **RESOLVED** |

---

## 2. Documented Operational Constraints

1. **Low-Light Optical Degradation:**
   In environments with illuminance $< 15\text{ lux}$, detector confidence for dark protective gloves drops below 0.20. Supplemental infrared (IR) illumination is recommended.
2. **Dense Occlusion & Crowd Overlap:**
   When workers stand in tight physical queues with $> 60\%$ bounding box overlap, spatial association temporarily transitions PPE states to `UNKNOWN` until workers separate.
3. **Steam & Industrial Vapor:**
   Dense boiler blowdown steam can trigger suspected smoke observations. Facilities must configure ROI polygon masks (`configs/cameras.yaml`) around known boiler vents.
