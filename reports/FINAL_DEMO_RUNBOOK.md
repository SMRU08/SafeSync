# SafeSync Final Prototype — Phase D: Live Demo Runbook

**Document:** `reports/FINAL_DEMO_RUNBOOK.md`  
**Date:** 2026-10-11  
**Project:** SafeSync Industrial Safety Operations Center  
**Target:** Hackathon Jury & Live Evaluation Demo  

---

## 1. Environment Prerequisites

- **Operating System:** Windows 10 / 11 (or Linux / macOS)
- **Python Version:** Python 3.10+ (Current: Python 3.13.15 in `backend/.venv`)
- **Node.js:** v18+ (Current: Node v20+ / npm v10+)
- **Physical Hardware:** USB Webcam or integrated laptop webcam (Index 0)
- **Model Checkpoint:** `models/detection/ppe_fire_smoke_v3/weights/best.pt`

---

## 2. Step-by-Step Server Startup Sequence

### Step 2.1 — Start the Backend Server (Terminal 1)
Open a PowerShell terminal and run:
```powershell
cd D:\Additional\PROJECT\SafeSync\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
**Expected Verification:**
- Output displays:
  ```
  [DATABASE] Connected to sqlite:///./safesync.db
  [AI ENGINE] Model 'ppe_fire_smoke_v3' loaded on device 'cpu' (classes: 7)
  [WEBSOCKET] Ready for connections on /ws/events and /ws/alerts
  [API] Started on 0.0.0.0:8000
  Camera cam_live_webcam successfully connected.
  Uvicorn running on http://0.0.0.0:8000
  ```
- Fast verification in browser: Open `http://127.0.0.1:8000/api/health` $\to$ Returns `{"status": "healthy"}`.

### Step 2.2 — Start the Frontend SOC Dashboard (Terminal 2)
Open a second PowerShell terminal and run:
```powershell
cd D:\Additional\PROJECT\SafeSync\frontend
npm run dev -- --host 0.0.0.0 --port 5173
```
**Expected Verification:**
- Output displays:
  ```
  VITE v6.4.3 ready in ... ms
  ➜  Local:   http://localhost:5173/
  ```

---

## 3. Live Demonstration Script for Judges

### Phase 1 — Overview & High-Level Operations (1 Minute)
1. Open Chrome/Edge at **`http://localhost:5173/`**.
2. **Explain the Architecture:**
   - SafeSync is an enterprise SOC monitoring live edge video feeds.
   - Show the **Active Camera Feed** on the Overview screen — points immediately to `CAM-LIVE • Physical Live Webcam`.
   - Point out the **Safety KPI Ribbon:** Live compliance score, total active workers, verified violations, and decoupled environmental hazards.

### Phase 2 — Real-Time Live Monitoring & PPE Inspection (2 Minutes)
1. Click **`Live Monitoring`** in the left navigation sidebar.
2. The large-format surveillance viewport immediately renders the live webcam stream.
3. **Step into the Camera View:**
   - Point to the **Green/Amber/Red Bounding Box** tracking your body with a persistent **ByteTrack Worker ID** (e.g. `C1-W1`).
   - Show the **Itemized PPE Inspection Card** on the top-right of your bounding box:
     - **Helmet:** `ABSENT` (or `PRESENT` if wearing a hard hat/cap).
     - **Safety Vest:** `ABSENT` (or `PRESENT` if wearing a vest).
     - **Gloves:** `UNKNOWN (occluded)` if hands are out of the frame.
     - **Safety Footwear:** `UNKNOWN (occluded)` if lower body is below desk.
4. **Explain the Tri-State Safety Logic:**
   - Emphasize that SafeSync **never treats UNKNOWN as ABSENT**. Because the webcam does not see your feet, it honestly labels them `UNKNOWN`, preventing false-alarm penalty fines.
   - Point out the **Temporal Validation Filter:** Brief flickers or occlusions do not trigger violations; violations require consistent temporal confirmation over 15 frames.

### Phase 3 — Independent P0 Environmental Hazard Demonstration (1 Minute)
1. Explain that SafeSync decouples environmental hazards from workers.
2. **Showcase Optical Fire/Smoke Defense:**
   - If wearing high-visibility orange or yellow clothing, point out that SafeSync's **torso-exclusion mask** ensures civilian hi-vis clothing is **never misclassified as an open flame**.
   - Show the P0 Environmental Hazard banner at the top of the viewport.

### Phase 4 — Incident Ledger & System Health (1 Minute)
1. Click **`Alerts & Incidents`** in the sidebar.
   - Show real incident logs populated via WebSocket.
   - Demonstrate the **Acknowledge** and **Resolve** workflow buttons.
2. Click **`System Health`** in the sidebar.
   - Show live CPU, memory, database connection, and WebSocket status.

---

## 4. Emergency Recovery Procedures

### If the Webcam Feed Disconnects or Freezes:
1. In the **Live Monitoring** viewport, click the **`Retry Stream Connection`** button.
2. Or use the quick API trigger:
   ```powershell
   curl -X POST http://127.0.0.1:8000/api/cameras/cam_live_webcam/start
   ```
   *The CameraWorker will immediately re-acquire the DirectShow hardware handle without needing to restart the backend.*

---

## 5. Safe System Shutdown

When the evaluation is concluded:
1. In Terminal 2 (Frontend): Press `Ctrl + C` $\to$ Press `y` $\to$ Enter.
2. In Terminal 1 (Backend): Press `Ctrl + C`.
   *The lifespan handler will gracefully call `CameraManager.stop_all()`, releasing all OpenCV camera handles.*
