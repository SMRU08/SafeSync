# RAKSHYA VISION — System Integration Architecture Map

**Document ID:** DOC-PHASE9-ARCH  
**System:** RAKSHYA VISION (AI Vision-Based Safety Monitoring)  
**Version:** 1.0.0 (Phase 9 Integration)  
**Date:** 2026-09-21  

---

## 1. End-to-End System Pipeline

```
┌─────────────────┐
│ Camera / Video  │  (RTSP Stream, Local Webcam, MP4 Video Ingestion)
└────────┬────────┘
         │ cv2.VideoCapture / Frame Packet
         ▼
┌─────────────────┐
│ Video Ingestion │  (Frame decode, RGB conversion, aspect ratio letterboxing)
└────────┬────────┘
         │ (H, W, 3) NumPy Array @ 384x384
         ▼
┌─────────────────┐
│ YOLO Detection  │  (Ultralytics YOLOv8n V2 Checkpoint: canonical classes 0..6)
└────────┬────────┘
         │ Raw Detections: BoundingBox [x1, y1, x2, y2], conf, class_id (0..6)
         ├─────────────────────────────────────────┐
         │ Persons (class 0) & PPE (1..4)           │ Fire (5) & Smoke (6)
         ▼                                         ▼
┌─────────────────┐                       ┌─────────────────┐
│ Worker Tracking │                       │ Hazard Tracking │
│ (ByteTrack)     │                       │ (Decoupled IoU) │
└────────┬────────┘                       └────────┬────────┘
         │ WorkerTrack [track_id, bbox]            │ HazardEvent [hazard_id, type]
         ▼                                         │
┌─────────────────┐                                │
│ PPE Association │                                │
│ (Anatomical)    │                                │
└────────┬────────┘                                │
         │ WorkerTrack + PPEObservations           │
         ▼                                         │
┌─────────────────┐                                │
│ PPE Compliance  │                                │
│ (State Machine) │                                │
└────────┬────────┘                                │
         │ Compliance Observations                 │ Verified Hazard Observations
         │ (PRESENT, ABSENT, UNKNOWN)              │ (SUSPECTED, CONFIRMED, CLEARED)
         └────────────────────┬────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Event Normalizer   │
                   └──────────┬──────────┘
                              │ NormalizedSafetyEvent Envelope
                              ▼
                   ┌─────────────────────┐
                   │     Risk Engine     │  (0..100 Deterministic Scoring & Factors)
                   └──────────┬──────────┘
                              │ RiskScoreBreakdown (Score, Level: LOW/MED/HIGH/CRIT)
                              ▼
                   ┌─────────────────────┐
                   │    Alert Engine     │  (Deduplication, Cooldown, Escalation)
                   └──────────┬──────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
   ┌─────────────────────┐         ┌─────────────────────┐
   │  SQLite Database    │         │  Event Broadcaster  │ (In-Memory Pub/Sub)
   │  (SQLAlchemy ORM)   │         └──────────┬──────────┘
   └─────────────────────┘                    │
                                              ▼
                                   ┌─────────────────────┐
                                   │  WebSocket Router   │ (/ws/alerts)
                                   └──────────┬──────────┘
                                              │
                                              ▼
                                   ┌─────────────────────┐
                                   │    SOC Dashboard    │ (React 18 + TypeScript)
                                   └─────────────────────┘
```

---

## 2. Component Integration Matrix

| Stage | Responsible Module | Input Interface | Output Interface | Primary Data Schema | Failure Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Ingestion** | `VideoProcessor`, `WebcamStream` | Video file, RTSP URI, Camera Index | Decoded BGR frame (`np.ndarray`) | Frame dimensions (W, H, C), FPS | Reconnect attempt with exponential backoff; logs error; skips corrupted frame without crash |
| **2. Detection** | `ModelLoader`, `SafetyDetector` | 384x384 normalized image tensor | List of `DetectionObject` | `[class_id: 0..6, conf: float, bbox: [x1,y1,x2,y2]]` | If model weights missing, raises `FileNotFoundError`; if invalid image, returns empty list |
| **3. Tracking** | `WorkerTracker` (`ByteTrack`) | Detections where `class_id == 0` | List of `WorkerTrack` | `[track_id: int, bbox: [4], active_frames: int]` | Drops tracks older than `max_lost=30`; reassigns new track IDs on re-entry |
| **4. PPE Association** | `PPEAssociator` | Detections where `class_id in [1..4]` + `WorkerTrack` | Associated PPE observations per worker | `ppe_status: {item: 'PRESENT'\|'ABSENT'\|'UNKNOWN'}` | Unassociated PPE objects discarded to background; does not corrupt worker state |
| **5. Compliance** | `ComplianceEvaluator` | Associated PPE per worker | `WorkerComplianceResult` | `overall_compliant: bool, missing_items: list` | Occluded/clipped workers assigned `UNKNOWN`; `UNKNOWN` NEVER generates a violation |
| **6. Hazards** | `HazardTracker`, `ZoneManager` | Detections where `class_id in [5, 6]` | `HazardEventDetail` | `state: 'NO_HAZARD'\|'SUSPECTED'\|'CONFIRMED'\|'CLEARED'` | Stays `SUSPECTED` until $N \ge 5$ frames; clears after 10 consecutive missed frames |
| **7. Normalization**| `EventNormalizer` | Compliance results & Hazard events | `NormalizedSafetyEvent` | `event_type, severity, camera_id, zone_id, tracks` | Invalid payloads dropped; logs parsing warning |
| **8. Risk Engine** | `RiskEngine` | `NormalizedSafetyEvent` | `RiskScoreBreakdown` | `score: int (0..100), level: str, factors: dict` | Clamps scores to $[0, 100]$; fallback to `LOW` if calculation fails |
| **9. Alert Engine**| `AlertEngine` | `NormalizedSafetyEvent`, DB Session | `Incident`, `Alert`, `AlertHistory` | `alert_id, incident_id, status, cooldown_until` | Cooldown drops duplicate alerts within window; deduplication appends to same incident |
| **10. Persistence** | `SQLAlchemy` (`rakshya_vision.db`) | ORM Model Instances | SQLite database rows | Tables: `incidents`, `alerts`, `alert_history`, `hazards` | Database connection error handled gracefully; inference loop continues without data loss |
| **11. Broadcast** | `EventBroadcaster`, `WebSocketManager` | `broadcast(event_name, payload)` | WebSocket JSON message | `{"type": "event", "event": str, "payload": dict}` | Disconnected clients removed cleanly; ping/pong heartbeat keeps connections alive |
| **12. Dashboard** | React 18 + TypeScript | REST API (`/api/*`) + WebSocket (`/ws/alerts`) | Rendered DOM elements | TypeScript interfaces in `types/safety.ts` | Auto-reconnects on WebSocket drop; displays `NO DATA` if database is empty |

---

## 3. Data Flow Contracts & Schemas

### 3.1. Canonical Class IDs
```python
CANONICAL_CLASSES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}
```

### 3.2. Temporal Confirmation State Machine
- **Worker PPE Confirmation:** $N_{\text{confirm}} = 3$ consecutive frames required to confirm `PRESENT`.
- **Worker PPE Absence:** $N_{\text{tol}} = 5$ consecutive missing frames required to transition from `PRESENT` to `ABSENT`.
- **Worker PPE Occlusion / Boundary:** Bounding box boundary contact or low confidence immediately locks state to `UNKNOWN`.
- **Hazard Confirmation:** $N = 5$ consecutive frames required to transition from `SUSPECTED` to `CONFIRMED`.
- **Hazard Clearing:** $N = 10$ consecutive frames without detection required to transition from `CONFIRMED` to `CLEARED`.

### 3.3. Risk Scoring & Mapping
$$\text{Score} = \text{clamp}\Big(\big(\text{BaseSeverity} + \text{PersistenceWeight} + (\text{Workers} - 1) \times 5\big) \times \text{ZoneMultiplier}, 0, 100\Big)$$
- `0 - 29`: **LOW** (Informational / advisory)
- `30 - 59`: **MEDIUM** (Single missing PPE item)
- `60 - 84`: **HIGH** (Multiple missing PPE items or single smoke hazard)
- `85 - 100`: **CRITICAL** (Active fire, multiple hazards, or persistent safety breach)

---

## 4. Failure Mode Recovery Matrix

1. **Camera Stream Interrupted / RTSP Timeout:**
   - Ingestion logs warning: `"Camera feed CAM-01 disconnected. Reconnection attempt 1/5..."`
   - Active worker tracks for that camera are marked lost and expired after 30 frames.
   - Dashboard renders `CAMERA STANDBY / OFFLINE` indicator.
2. **Database Offline / Disk Full:**
   - Alerts engine intercepts database error: `"Database connection lost. Alert cached in memory."`
   - Real-time WebSocket broadcasting continues uninterrupted.
   - API endpoints return HTTP 503 Service Unavailable with clear detail.
3. **Corrupted / Invalid Input Frame:**
   - OpenCV decode failure: skips invalid frame, increments `dropped_frames` counter.
   - Main inference thread does not crash.
4. **WebSocket Client Drops:**
   - Client disconnects cleanly via `WebSocketDisconnect`.
   - `WebSocketManager` removes connection from subscriber pool.
   - Frontend auto-reconnects with exponential backoff.
