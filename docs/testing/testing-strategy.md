# Testing Strategy

SafeSync maintains a rigorous, multi-layered automated testing regime spanning unit tests, integration test matrices, latency benchmarks, memory leak evaluations, and security penetration audits.

---

## 1. Testing Pyramid

```
                ▲
               / \
              /   \     End-to-End System Tests (39 Scenarios)
             / E2E \    (scripts/testing/run_integration_tests.py)
            /───────\
           /         \   Integration Tests & Security Audits
          / Integrat. \  (Camera isolation, DB WAL, WebSocket, Auth)
         /─────────────\
        /               \ Automated Unit Tests (160 Test Cases)
       /   Unit Tests    \ (Detection, ByteTrack, PPE Spatial, Alerts)
      /───────────────────\
```

---

## 2. Test Suites Overview

### 2.1 Backend Unit & Subsystem Tests (`backend/tests/`)
Contains 160 unit tests covering individual algorithms and API routers:
- `test_detection.py`: YOLO forward pass, class mapping, letterbox resizing.
- `test_compliance.py`: ByteTrack Kalman updates, anatomical zones, temporal thresholds.
- `test_hazards.py`: Spatial hazard tracking, flame/smoke co-occurrence, clearing timer.
- `test_risk_alerts.py`: Risk formula scoring, alert deduplication, cooldown suppression.
- `test_websocket.py`: Connection lifecycle, heartbeat ping/pong, broadcast reception.
- `test_camera_manager_phase10.py`: Worker thread isolation, backoff, URL masking.
- `test_auth_rbac_phase10.py`: Password hashing, JWT issuance, role permissions.
- `test_evidence_phase10.py`: SHA-256 evidence hashing, storage quota pruning.
- `test_observability_phase10.py`: Prometheus metrics, liveness/readiness probes.
- `test_live_camera_pipeline.py`: Real-time AI pipeline execution inside camera workers.

**Execution Command:**
```bash
cd backend
pytest tests/ -v
```

### 2.2 End-to-End Integration Suite (`scripts/testing/run_integration_tests.py`)
Executes 39 real-world scenarios across the entire connected pipeline:
- Section 1: Model provenance, checksum, and 7-class ontology verification.
- Section 2: Video pipeline, webcam hardware check, RTSP simulated ingestion.
- Section 3: 10 PPE compliance scenarios (compliant, missing helmet, missing vest, occlusion, entry/exit).
- Section 4: 7 Fire & Smoke hazard scenarios (fire only, smoke only, multi-hazard, transient sparks).
- Section 5: Risk scoring & alert lifecycle (cooldown, acknowledgment, resolution).
- Section 6: Database resilience and WebSocket streaming.
- Section 7: Pipeline latency budget (< 100 ms) and memory stability benchmarks.
- Section 8: Security and input validation (zero-byte, path traversal, file type).

**Execution Command:**
```bash
python scripts/testing/run_integration_tests.py
```

### 2.3 Frontend Build Verification
Verifies TypeScript compilation and bundle packaging:

```bash
cd frontend
npm run build
```
- Passes with 0 TypeScript or packaging errors (`tsc -b && vite build`).
