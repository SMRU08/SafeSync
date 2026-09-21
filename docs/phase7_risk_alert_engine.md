# Phase 7 Technical Report — Risk Analysis + Smart Alert Engine

**Project:** RAKSHYA VISION — AI Vision-Based Safety Monitoring  
**Phase:** 7 (Risk Analysis + Smart Alert Engine)  
**Status:** COMPLETED & VERIFIED  
**Date:** September 2026  

---

## 1. Executive Summary & Architecture

Phase 7 completes the operational intelligence layer of RAKSHYA VISION. It ingests verified vision events from Phase 5 (Worker Tracking & PPE Compliance) and Phase 6 (Fire & Smoke Hazard Analysis), standardizes them into normalized safety events, evaluates transparent risk scores, manages persistent incidents, enforces alert deduplication and cooldown policies, supports automatic severity escalation, and exposes full alert lifecycle REST APIs.

### Core Architecture:
```
[ Phase 5: PPE Compliance ]     [ Phase 6: Environmental Hazards ]
  (WorkerTrack, PPEObservation)      (HazardEventDetail, Smoke/Fire)
                 │                                  │
                 └────────────────┬─────────────────┘
                                  │
                                  ▼
                     [1] Event Normalization Layer
                       (Enforces UNKNOWN != Violation)
                                  │
                                  ▼
                     [2] Rule-Based Risk Engine
                       (Base + Persist + Workers + Rep + Zone)
                                  │
                                  ▼
                     [3] Incident Manager (OPEN / ACK / RES)
                                  │
                                  ▼
                     [4] Smart Alert Engine
                       (Deduplication + Cooldown + Escalation)
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                 ▼
       [5] SQLite Persistence           [6] Event Broadcaster
     (Incidents, Alerts, History)       (WebSocket-Ready Pub/Sub)
                 │                                 │
                 ▼                                 ▼
       FastAPI REST Endpoints               Future Phase 8
      (/api/alerts, /api/risk/summary)        (Live Dashboard)
```

### Strict Scope Compliance:
* **No Frontend UI Built in Phase 7:** WebSocket-ready Pub/Sub broadcaster is ready for Phase 8.
* **No External Alert Dispatch:** No external SMS, email, WhatsApp, or webhook calls.
* **No Opaque ML Risk Scoring:** Deterministic, transparent, explainable formula.
* **Preservation of Previous Phases:** Zero regressions across Phase 4, 5, and 6.

---

## 2. Standardized Event Schema

Implemented in `backend/app/ai/risk/schemas.py`:
```json
{
  "event_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "event_type": "MISSING_HELMET",
  "timestamp": "2026-09-21T09:50:00.000Z",
  "camera_id": "camera_01",
  "zone_id": "production_floor",
  "track_id": 12,
  "hazard_event_id": null,
  "confidence": 0.88,
  "duration_seconds": 4.5,
  "details": {
    "item_type": "helmet",
    "consecutive_missed": 6,
    "worker_bbox": [100, 120, 250, 420]
  },
  "source": "compliance"
}
```

### Supported Event Types:
- `PPE_VIOLATION` / `MISSING_HELMET`
- `MISSING_SAFETY_VEST`
- `MISSING_GLOVES`
- `MISSING_SAFETY_FOOTWEAR`
- `FIRE_DETECTED`
- `SMOKE_DETECTED`
- `MULTIPLE_HAZARDS`
- `CAMERA_FAILURE`
- `SYSTEM_FAILURE`

---

## 3. Configurable Risk Policy (`configs/risk_policy.yaml`)

### Categorical Risk Levels:
| Risk Level | Score Range | Operational Meaning |
| :--- | :--- | :--- |
| **LOW** | $0 \le S \le 29$ | Non-critical PPE advisory or isolated minor deviation |
| **MEDIUM** | $30 \le S \le 59$ | Moderate safety non-compliance requiring supervisor follow-up |
| **HIGH** | $60 \le S \le 84$ | Severe PPE violation in high-hazard zone or active smoke plume |
| **CRITICAL** | $85 \le S \le 100$ | Active open flame, multi-hazard emergency, or long-persisting hazard |

### Base Event Severities:
- `fire`: **85**
- `smoke`: **60**
- `missing_helmet`: **50**
- `missing_safety_vest`: **45**
- `camera_failure`: **40**
- `missing_gloves`: **25**
- `missing_safety_footwear`: **25**
- `multiple_hazards_bonus`: **+20**

### Zone Multipliers:
- `electrical_room`: **1.30×** (high-voltage enclosure)
- `production_floor`: **1.15×** (heavy industrial machinery)
- `loading_dock`: **1.10×** (docking bays)
- `storage_area` / `UNKNOWN`: **1.00×**

---

## 4. Transparent Risk Score Calculation

The Risk Engine (`backend/app/services/risk_engine.py`) uses an explainable formula:

$$\text{Subtotal} = \text{Base} + \text{Persistence} + \text{Workers} + \text{Repetition} + \text{MultiHazard}$$

$$\text{Raw Score} = \text{Subtotal} \times \text{Zone Multiplier}$$

$$\text{Risk Score} = \min\left(100, \max\left(0, \operatorname{round}(\text{Raw Score})\right)\right)$$

### Factor Breakdown Rules:
1. **$\text{Persistence} = \min(25.0, \text{duration} \times 1.0\,\text{pt/s})$**
2. **$\text{Workers} = \min(20.0, (\text{affected workers} - 1) \times 5.0\,\text{pts})$**
3. **$\text{Repetition} = \min(15.0, \text{occurrences} \times 4.0\,\text{pts})$**
4. **$\text{MultiHazard} = +20.0$** if multiple simultaneous hazards are present.

Every calculation returns explainable audit factors:
```json
{
  "base_severity": 50.0,
  "persistence_factor": 15.0,
  "affected_workers_factor": 5.0,
  "repetition_factor": 4.0,
  "multi_hazard_factor": 0.0,
  "zone_multiplier": 1.15
}
```

---

## 5. Strict PPE Rule: `UNKNOWN` State Protection

> [!IMPORTANT]
> When Phase 5 outputs `helmet = UNKNOWN` or `vest = UNKNOWN` (e.g. boundary truncation, camera edge clipping, or worker occlusion), **the Event Normalizer drops the event**. No violation is generated. Only confirmed `ABSENT` state yields `MISSING_*` events.

---

## 6. Environmental Hazard Integration

* **Fire Events:** Confirmed fire from Phase 6 creates `FIRE_DETECTED` (base severity 85 $\rightarrow$ `HIGH` or `CRITICAL`).
* **Smoke Events:** Confirmed smoke creates `SMOKE_DETECTED` (base severity 60 $\rightarrow$ `HIGH`).
* **Multi-Hazard:** Simultaneous fire and smoke or hazard with PPE violation creates `MULTIPLE_HAZARDS` (+20 bonus points).

---

## 7. Incident Lifecycle Management

Incidents represent persistent ongoing safety situations:
* **Statuses:** `OPEN` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `RESOLVED` / `DISMISSED`.
* **Deduplication:** Subsequent detections for the same worker or hazard update the active incident duration and affected tracks rather than spawning new incidents.

---

## 8. Smart Alerting, Deduplication, and Cooldown

Configured in `configs/alert_policy.yaml`:
* **Cooldown Suppression:** Once an alert is fired for Worker #12 missing a helmet, repeat detections within the 60-second cooldown window do **NOT** spawn new alerts. They are logged to `alert_history` as `COOLDOWN_SUPPRESSED`.
* **Escalation Trigger:** If an event persists beyond `persistence_threshold_seconds = 30.0s`, the alert severity automatically upgrades (e.g., `MEDIUM` $\rightarrow$ `HIGH` or `HIGH` $\rightarrow$ `CRITICAL`), logging an `ESCALATED` audit trail.

---

## 9. Human-Readable Message Synthesis

Alerts generate human-readable messages based on real tracking and zone data:
* `"Confirmed missing helmet detected for Worker #12 in production_floor on camera_01."`
* `"Confirmed active flame combustion detected on camera_01 in electrical_room."`
* `"[ESCALATED to CRITICAL] Confirmed active flame combustion detected on camera_01 in electrical_room. (Persisted for 42.0s)"`

---

## 10. Database Schema (`backend/app/models/risk_alert.py`)

* **`incidents` table:** `incident_id`, `status`, `event_types`, `camera_id`, `zone_id`, `affected_tracks`, `risk_score`, `risk_level`, `factors_json`, timestamps.
* **`alerts` table:** `alert_id`, `incident_id`, `severity`, `title`, `message`, `camera_id`, `zone_id`, `event_type`, `status`, timestamps.
* **`alert_history` table:** `alert_id`, `incident_id`, `action`, `previous_level`, `new_level`, `reason`, `timestamp`.

---

## 11. REST API Endpoints (`backend/app/api/alerts.py`)

* `GET /api/risk/summary`: Real database counts (`active_alerts`, `critical`, `high`, `medium`, `low`, `open_incidents`).
* `GET /api/alerts`: Lists alerts with query filters (`status`, `risk_level`, `camera_id`, `zone_id`, `event_type`, `limit`).
* `GET /api/alerts/{alert_id}`: Retrieves alert details and historical audit log.
* `POST /api/alerts/{alert_id}/acknowledge`: Acknowledges alert and incident.
* `POST /api/alerts/{alert_id}/resolve`: Resolves alert and marks incident as resolved.
* `POST /api/alerts/{alert_id}/dismiss`: Dismisses false alarms or non-actionable advisories.
* `GET /api/incidents`: Lists all safety incidents.
* `GET /api/incidents/{incident_id}`: Retrieves incident details and linked alerts.

---

## 12. Verification & Automated Testing

### 12.1 Test Suite Results (72 / 72 Passed)
Executed via `pytest backend/tests -v` in **10.23 seconds**:
* `test_risk_alerts.py`: **19 passed** (covers all 20 required behaviors)
* `test_hazards.py`: **16 passed** (Phase 6 intact)
* `test_compliance.py`: **14 passed** (Phase 5 intact)
* `test_detection.py`: **19 passed** (Phase 4 intact)
* `test_main.py`: **4 passed** (core endpoints intact)

### 12.2 Benchmark Results (`outputs/alerts/alert_benchmark.json`)
Measured over 200 iterations:
* **Mean Risk Evaluation Latency:** **0.028 ms**
* **Mean Alert Engine & DB Write Latency:** **5.667 ms**
* **Total Event Processing Latency:** **5.696 ms**
* **System Throughput:** **175.5 events / second**

---

## 13. Known Limitations

1. **In-Memory Cache on Process Restart:** In-memory cooldown cache resets upon backend server reboot; persisted state in SQLite remains intact.
2. **Camera Health Signaling:** Full `CAMERA_FAILURE` generation depends on RTSP/CCTV stream connection health flags from upstream camera ingestion.
3. **Phase 8 Readiness:** The event broadcaster (`EventBroadcaster`) provides pub/sub dispatch (`AlertCreated`, `AlertUpdated`, `AlertEscalated`, `IncidentCreated`, `IncidentResolved`) ready to stream directly to Phase 8 WebSockets.
