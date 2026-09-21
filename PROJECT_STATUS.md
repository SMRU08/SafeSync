# RAKSHYA VISION — Project Status

## Project Overview
- **Project Name:** RAKSHYA VISION
- **Tagline:** AI Vision-Based Safety Monitoring
- **Current Phase:** Phase 5 — Worker Tracking + PPE Association + Compliance (COMPLETED & VERIFIED)

---

## 1. Phase 1 Foundation Status
- **Backend:** Operational (FastAPI + SQLAlchemy + SQLite, pytest suite integrated).
- **Frontend:** Built and operational (React 18 + TypeScript + Vite, live health connection).
- **Git:** Version control maintained with structured commits.

---

## 2. Phase 2 Dataset Pipeline Status
- **Raw Datasets Preserved (`datasets/raw/`):** 4 datasets preserved with verified SHA-256 checksums (22,453 raw images).
- **Processed Split (`datasets/processed/`):** 22,453 images (Train: 15,717, Val: 4,490, Test: 2,246), 51,195 verified clean bounding boxes across canonical classes `0..6`.
- **Zero Leakage:** No overlap between splits.

---

## 3. Phase 3 & 3.1 Model Status (`ppe_fire_smoke_v2`)
- **Architecture:** Ultralytics YOLOv8n (nano), PyTorch 2.14.0+cpu
- **Checkpoint:** [`models/detection/ppe_fire_smoke_v2/weights/best.pt`](./models/detection/ppe_fire_smoke_v2/weights/best.pt)
- **Checkpoint SHA-256:** `490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3`
- **Canonical Classes (7):** `0: person`, `1: helmet`, `2: safety_vest`, `3: gloves`, `4: safety_footwear`, `5: fire`, `6: smoke`
- **Test Set Performance (conf=0.25):** Precision: 37.60% | Recall: 37.44% | mAP@50: 25.23% (3.61× over V1)
- **CPU Inference Speed:** Median ~40.36 ms (24.8 FPS)

---

## 4. Phase 4 Real-Time & Video Detection Status (COMPLETED)
- **Inference Pipeline:** Single image, video files, local webcam, and simulated RTSP streams.
- **Strict Decoupling:** Bounding boxes draw only `[class_name] [conf]`; no compliance labels.
- **Endpoints:** `/api/detection/health`, `/api/detection/image`, `/api/detection/video`.

---

## 5. Phase 5 Worker Tracking + PPE Association + Compliance Status (COMPLETED)
- **Anonymous Tracking Engine:** Custom ByteTrack with 8-state Kalman Filter (`KalmanBoxTracker`) and two-stage Hungarian assignment (`scipy.optimize.linear_sum_assignment`).
- **Anatomy-Aware Spatial Association:** Relative body zones for helmet (head ROI: $[-0.05, 0.30] \times H$), safety vest (torso ROI: $[0.15, 0.70] \times H$), gloves (lateral arms: $[0.35, 0.90] \times H$), and footwear (lower feet: $[0.70, 1.05] \times H$).
- **Bipartite Assignment:** Hungarian matching prevents duplicate PPE allocation across adjacent workers.
- **Temporal State Machine:** $N_{\text{confirm}} = 3$ frames to confirm `PRESENT`, $N_{\text{tol}} = 5$ frames tolerance before transitioning to `ABSENT`.
- **False Alarm Prevention:** Image boundary truncation ($y_1 \le 10\text{px}$) and inter-worker occlusion ($> 25\%$ overlap) trigger `UNKNOWN` states instead of false violations.
- **Checklist HUD Visualization:** Compact non-destructive overlay above workers with track IDs (`Worker #1`), item status badges (`H:[+]`, `V:[-]`, etc.), and overall status banners.
- **Environmental Hazard Pass-Through:** Fire and smoke boxes rendered cleanly in warning colors without marking PPE violations.
- **API Endpoints:**
  - `GET /api/compliance/config`
  - `POST /api/compliance/analyze`
- **Database Schema:** SQLAlchemy models in `backend/app/models/compliance.py` (`WorkerTracking`, `PPEObservation`, `ComplianceObservation`).
- **Verification:**
  - Controlled Scenarios: 10/10 passed (`outputs/compliance/scenario_test_results.json`).
  - Pytest Suite: 37/37 passed across backend tests.
  - Video Pipeline Benchmark: Processed `datasets/test_safety_video.mp4` at 9.20 FPS with metrics exported to `outputs/tracking/tracking_metrics.json`.

---

## 6. Automated Test Suite
- Full test suite passing: `pytest backend/tests -v` (37/37 tests passed).
  - `test_compliance.py`: 14 tests passed.
  - `test_detection.py`: 19 tests passed.
  - `test_main.py`: 4 tests passed.

---

## 7. Next Steps — Phase 6
- Awaiting explicit user approval before beginning Phase 6 (Alert Engine & Notification Dispatch).