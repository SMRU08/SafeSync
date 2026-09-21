# RAKSHYA VISION — Testing & Integration Suite

## Overview
This directory contains end-to-end integration and verification scripts for RAKSHYA VISION.
The test suite exercises the full system pipeline:

```
Camera / Video Ingestion
      ↓
YOLOv8 Detection (V2 Checkpoint: 7 canonical classes)
      ↓
Worker Tracking (ByteTrack) & Hazard Tracking (Decoupled IoU)
      ↓
Anatomical PPE Association
      ↓
Temporal Compliance & Hazard State Machines
      ↓
Risk Evaluation & Smart Alert Engine (Deduplication + Cooldown)
      ↓
FastAPI WebSocket Broadcaster & REST Endpoints
      ↓
React 18 / Vite Safety Operations Center (SOC) Dashboard
```

---

## Running the Integration Tests

### 1. Standalone Integration Script
Executes 39 end-to-end verification cases covering all scenarios, outputs structured JSON reports to `outputs/integration/`:

```powershell
# From project root:
.\backend\.venv\Scripts\python.exe scripts/testing/run_integration_tests.py
```

Outputs generated:
- `outputs/integration/performance_report.json` (Latency benchmarks, breakdown, and memory delta)
- `outputs/integration/risk_test_results.json` (Calculated explainable risk matrices)

### 2. Pytest Integration Suite
Executes the integration suite alongside all system unit tests (81 tests total):

```powershell
# From project root:
.\backend\.venv\Scripts\pytest.exe backend/tests -v
```

---

## Test Coverage Matrix
- **Section 1: Model Integration:** Checkpoint existence, SHA-256 integrity, canonical 7-class ontology, synthetic inference.
- **Section 2: Video Ingestion:** Synthetic MP4 file processing, hardware fallback handling.
- **Section 3: PPE Compliance (10 Scenarios):** Full compliance, missing helmet/vest/gloves/boots, multi-worker, occlusion preservation (`UNKNOWN`), track entry/exit, temporal miss tolerance, close-proximity spatial isolation.
- **Section 4: Fire & Smoke Hazards (7 Scenarios):** Confirmed fire, confirmed smoke, multi-hazard simultaneous, clear scene, confidence floor filtering, 1-frame transient suppression (`SUSPECTED`).
- **Section 5: Risk & Alert Engine:** LOW/MED/HIGH/CRITICAL scoring formulas, alert creation, duplicate suppression via cooldown, acknowledge, and resolve lifecycles.
- **Section 6: Database & Live Streaming:** SQLite persistence, WebSocket `/ws/alerts` handshake, bi-directional ping/pong heartbeat, real-time alert broadcasts.
- **Section 7: Performance & Stability:** Subsystem latency budget (<100ms on CPU), FPS benchmarking, memory stability over repeated cycles.
- **Section 8: Security & Validation:** 0-byte upload rejection (HTTP 400), invalid MIME/extension rejection (HTTP 400/415), path traversal attack prevention (HTTP 404/422).
