# Data Flow & System Contracts

This document formalizes the internal data schemas, interface boundaries, and data flow contracts between all subsystems of RAKSHYA VISION.

---

## 1. Subsystem Integration Matrix

| Stage | Subsystem / Module | Input Interface | Output Interface | Primary Schema Model | Fault Isolation / Recovery |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Ingestion** | `CameraWorker`, `CameraManager` | Video file, RTSP URI, USB index | Decoded BGR frame (`np.ndarray`) | Frame dimensions (W, H, C), timestamp | Bounded exponential backoff; skips dropped frame without crashing worker thread. |
| **2. Detection** | `ModelLoader`, `Detector` | 384x384 RGB normalized tensor | Raw bounding boxes & classes | `[class_id: 0..6, conf: float, bbox: [x1,y1,x2,y2]]` | If checkpoint fails SHA-256 check, loads fallback; invalid frames return empty lists. |
| **3. Tracking** | `ByteTrack` (`tracker.py`) | Detections where `class_id == 0` | List of active tracks | `WorkerTrack [track_id, bbox, conf]` | Drops stale tracks after 30 lost frames; assigns new track ID upon re-entry. |
| **4. PPE Association** | `SpatialPPEAssociator` | Detections where `class_id in [1..4]` + worker tracks | Anatomical association per worker | `ppe_details: Dict[str, PPEObservation]` | Unassociated PPE discarded; does not corrupt worker state. |
| **5. Compliance** | `TemporalComplianceTracker` | Associated PPE observations | Confirmed worker compliance | `ppe: Dict[str, PPEState]` (`PRESENT`, `ABSENT`, `UNKNOWN`) | Partial occlusions locked to `UNKNOWN`; `UNKNOWN` strictly never triggers violations. |
| **6. Hazards** | `HazardTracker`, `ZoneManager` | Detections where `class_id in [5, 6]` | Spatial hazard events | `HazardEventDetail [state: SUSPECTED\|CONFIRMED\|CLEARED]` | Stays `SUSPECTED` until $N \ge 5$ frames; clears after 10 consecutive missed frames. |
| **7. Normalization** | `EventNormalizer` | Compliance responses & Hazard events | Normalized event envelope | `NormalizedSafetyEvent` | Malformed events safely ignored; logs validation warning. |
| **8. Risk Engine** | `RiskEngine` | `NormalizedSafetyEvent` | Quantitative risk evaluation | `RiskScoreBreakdown [score: 0..100, level: str]` | Score clamped to $[0, 100]$; falls back to `LOW` if factors are missing. |
| **9. Alert Engine** | `AlertEngine` | `NormalizedSafetyEvent`, DB Session | Relational records & dispatches | `Incident`, `Alert`, `AlertHistory` | In-memory cache suppresses duplicate alerts during cooldown window. |
| **10. Persistence** | `SQLAlchemy` (SQLite WAL) | ORM entities | Relational rows on disk | Tables: `incidents`, `alerts`, `hazard_events`, `evidence_items` | Database locked errors mitigated via 5000ms busy timeout and WAL mode. |
| **11. Broadcast** | `EventBroadcaster`, `WebSocketManager` | `broadcast(event_name, payload)` | WebSocket JSON message | `{"type": "event", "event": str, "payload": dict}` | Disconnected clients cleanly pruned; keep-alive ping/pong prevents dead sockets. |
| **12. Dashboard** | React 18 + TypeScript | REST APIs + WebSocket | Real-time DOM elements | TypeScript interfaces in `src/types/` | Automatic reconnect with exponential backoff on connection drops. |

---

## 2. Core Data Models & Schemas

### 2.1 Canonical Safety Classes
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

### 2.2 Worker Tracking & PPE State
```python
class PPEState(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    UNKNOWN = "UNKNOWN"

class WorkerTrack(BaseModel):
    track_id: int
    bbox: WorkerBoundingBox  # [x1, y1, x2, y2]
    confidence: float
    ppe: Dict[str, PPEState]  # {"helmet": "ABSENT", "safety_vest": "PRESENT"}
    ppe_details: Dict[str, PPEObservation]
    overall_status: OverallComplianceState  # COMPLIANT, NON_COMPLIANT, UNKNOWN
    history_length: int
    is_partially_occluded: bool
```

### 2.3 Normalized Safety Event Envelope
Every safety violation or environmental hazard is normalized into a common envelope before ingestion by the risk and alert engines:

```python
class NormalizedSafetyEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType  # MISSING_HELMET, MISSING_SAFETY_VEST, FIRE_DETECTED, SMOKE_DETECTED
    timestamp: str  # ISO 8601 UTC
    camera_id: str
    zone_id: str
    track_id: Optional[int] = None
    confidence: float
    duration_seconds: float = 0.0
    affected_workers_count: int = 1
    details: Dict[str, Any] = Field(default_factory=dict)
```

### 2.4 WebSocket Event Payload
Live events dispatched to the frontend Security Operations Center dashboard adhere to this envelope:

```json
{
  "type": "event",
  "event": "AlertCreated",
  "payload": {
    "alert_id": "ALT-c8d9e2a1",
    "incident_id": "INC-00124",
    "event_type": "MISSING_HELMET",
    "severity": "HIGH",
    "title": "Missing Helmet Violation",
    "message": "Worker #104 detected without required helmet in Zone A (Turbine Deck).",
    "camera_id": "camera_01",
    "zone_id": "zone_a",
    "risk_score": 72,
    "timestamp": "2026-09-21T18:30:15.123Z",
    "evidence_reference": "outputs/evidence/2026/09/21/camera_01/INC-00124_snap.jpg"
  }
}
```

---

## 3. Failure Mode Recovery Matrix

1. **Camera Feed Interruption / RTSP Drop:**
   - Worker transitions from `CONNECTED` to `RECONNECTING`.
   - Executes bounded exponential backoff ($0.5\text{s} \rightarrow 1.0\text{s} \rightarrow 2.0\text{s} \dots$ up to `max_delay_seconds`).
   - Active worker tracks associated with the camera are gracefully expired after 30 lost frames.
   - Frontend displays `RECONNECTING` badge without stalling other camera feeds.

2. **Database Locked / Disk Full:**
   - Database operations use a 5,000 ms busy timeout before raising errors.
   - In-memory alert caching preserves live alerts if SQLite write locks occur.
   - Real-time WebSocket streaming continues unaffected because it operates in-memory.

3. **Malformed Frame or Decode Error:**
   - Invalid frame packets are discarded immediately.
   - Metrics counter `dropped_frames` increments; inference cycle proceeds to next valid frame.

4. **External Notification Failure (Webhook/Email):**
   - Dispatches run asynchronously on a background `ThreadPoolExecutor`.
   - Timeout bounded to 3.0s (Webhooks) or 5.0s (SMTP).
   - Core video inference and database transactions are never blocked by external network timeouts.
