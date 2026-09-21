# RAKSHYA VISION — Phase 8: Safety Dashboard & Live Monitoring

**Document ID:** DOC-PHASE-8  
**System:** RAKSHYA VISION (AI Vision-Based Safety Monitoring)  
**Status:** COMPLETED & VERIFIED  
**Date:** 2026-09-21  

---

## 1. Executive Summary

Phase 8 completes the production-grade, human-in-the-loop **Safety Operations Center (SOC) Dashboard** for RAKSHYA VISION. It directly interfaces with all underlying subsystems:
- **Phase 4:** Real-Time YOLO Video/Image Inference Engine
- **Phase 5:** Multi-Object Worker Tracking + Spatial PPE Association + Temporal Validation State Machine
- **Phase 6:** Fire & Smoke Hazard Analysis + Spatial Geofencing
- **Phase 7:** Risk Assessment Engine + Incident Lifecycle + Smart Alert Deduplication & Escalation
- **Phase 8 Backend:** Live WebSocket Event Dispatcher (`/ws/alerts` and `/ws/events`)

The dashboard conforms to the strict project guideline: **ZERO FABRICATED METRICS**. All numbers, charts, statuses, and indicators are computed directly from live backend states or historical SQLite database records. When no cameras are actively streaming or no incidents are logged, explicit empty states (`NO DATA`, `STANDBY`, `NO HISTORICAL DATA AVAILABLE`) are rendered.

---

## 2. System Architecture

```
                                 ┌─────────────────────────────────────────┐
                                 │     RAKSHYA VISION SOC Dashboard        │
                                 │       (React 18 + TypeScript)           │
                                 └───────┬─────────────────────────▲───────┘
                                         │                         │
                      REST HTTP (JSON)   │                         │  WebSocket (JSON)
           (Health, Alerts, Config, POST)│                         │  (/ws/alerts)
                                         ▼                         │
                                 ┌─────────────────────────────────┴───────┐
                                 │             FastAPI Backend             │
                                 │               (Port 8000)               │
                                 └───────┬─────────────────────────▲───────┘
                                         │                         │
                                         ▼                         │
                             ┌───────────────────────┐  ┌──────────┴──────────┐
                             │    AlertEngine        │  │  EventBroadcaster   │
                             │ (Deduplication, Cooldown,│  │   (Pub/Sub Hub)     │
                             │   Escalation, SQLite) │  └─────────────────────┘
                             └───────────┬───────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
      ┌───────────────────────────┐               ┌───────────────────────────┐
      │     WorkerTracker &       │               │      HazardTracker &      │
      │  PPE Compliance (Phase 5) │               │   Fire/Smoke (Phase 6)    │
      └───────────────────────────┘               └───────────────────────────┘
```

---

## 3. Real-Time WebSocket Channel (`/ws/alerts`)

- **Location:** `backend/app/api/websocket.py`
- **Protocol:** WebSocket (RFC 6455)
- **Endpoints:** `ws://localhost:8000/ws/alerts` and `ws://localhost:8000/ws/events`
- **Handshake Response:**
  ```json
  {
    "type": "connected",
    "message": "Connected to RAKSHYA VISION Live Event Stream",
    "active_connections": 1,
    "timestamp": "2026-09-21T04:40:00.000000+00:00"
  }
  ```
- **Bi-Directional Heartbeat:** Clients send `{"type": "ping"}`; server responds with `{"type": "pong", "timestamp": "..."}`.
- **Broadcast Events:**
  - `AlertCreated`
  - `AlertUpdated`
  - `AlertEscalated`
  - `IncidentCreated`
  - `IncidentResolved`

---

## 4. Frontend Component Breakdown

| Component / Page | File Path | Function & Scope |
| :--- | :--- | :--- |
| **App Shell** | `src/App.tsx` | View routing, global toast banners, modal integration |
| **SOC Header** | `src/components/Header.tsx` | Branding, live telemetry pills (API, AI, DB, WS), UTC clock, nav tabs |
| **Metric Card** | `src/components/MetricCard.tsx` | High-visibility KPI cards with cyber-industrial styling |
| **Alerts Table** | `src/components/AlertsTable.tsx` | Search, severity & status filtering, instant action buttons |
| **Alert Detail Modal** | `src/components/AlertDetailModal.tsx` | Plain-English message, metadata, escalation audit trail |
| **Incident Detail Modal** | `src/components/IncidentDetailModal.tsx` | Risk score factor breakdown (base, persistence, workers, zone) |
| **Worker Card** | `src/components/WorkerComplianceCard.tsx` | Anonymous track card with strictly separated `UNKNOWN` vs `ABSENT` PPE |
| **Hazard Status Panel** | `src/components/HazardStatusPanel.tsx` | Zone threat matrix with thermal and smoke signatures |
| **Overview View** | `src/pages/OverviewView.tsx` | High-level executive SOC dashboard with active KPI counters |
| **Cameras View** | `src/pages/CamerasView.tsx` | 4-camera grid, zone geofence inspection, live test frame analyzer |
| **Workers View** | `src/pages/WorkersView.tsx` | PPE compliance tracking, filter toolbar, test frame runner |
| **Hazards View** | `src/pages/HazardsView.tsx` | Fire/smoke hazard state machine, spatial relationship banner |
| **Alerts View** | `src/pages/AlertsView.tsx` | Centralized alert and incident management center |
| **Analytics View** | `src/pages/AnalyticsView.tsx` | Severity, event type, and camera distribution charts (No fake data) |
| **Settings View** | `src/pages/SettingsView.tsx` | Read-only inspection of active neural network and policy parameters |

---

## 5. Verification & Quality Gates

1. **Automated Backend Pytest:**
   - Command: `pytest backend/tests -v`
   - Result: **75 passed in 9.96s** (including new `test_websocket.py`).
2. **Frontend Build:**
   - Command: `npm run build` in `frontend/`
   - Result: Built production bundle (`tsc -b && vite build`) in 3.59s with **0 errors**.
3. **No-Fake-Data Enforcement:**
   - Worker cards render `NO ACTIVE WORKERS DETECTED` when no stream is present.
   - Compliance rate renders `NO DATA` when 0 workers are present.
   - Analytics renders `NO HISTORICAL DATA AVAILABLE` when SQLite contains 0 records.
4. **PPE UNKNOWN Safety Rule:**
   - Visualized with amber badge labeled `UNKNOWN / OCCLUDED` and tooltip explanation.
   - Never counted as a safety violation.
