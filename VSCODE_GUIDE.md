# RAKSHYA VISION — Complete VS Code Developer & Run Guide

A step-by-step guide on how to set up, run, debug, and monitor **RAKSHYA VISION** using Visual Studio Code on Windows.

---

## 1. Quick Start: The 2-Terminal Workflow (30 Seconds)

Open the project in VS Code (`File -> Open Folder -> D:\Additional\PROJECT\RAKSHYA-VISION`).

Open two terminal tabs side-by-side (`Ctrl + ~` to open terminal, then click the **Split Terminal** icon `Ctrl + Shift + 5`):

### Terminal 1 — Backend (Python / FastAPI / YOLO AI)
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*You will see:* `INFO: Uvicorn running on http://0.0.0.0:8000`

### Terminal 2 — Frontend (React 18 / Vite / TypeScript)
```powershell
cd frontend
npm run dev
```
*You will see:* `➜ Local: http://localhost:5173/`

### Open Your Browser
Go to **[http://localhost:5173](http://localhost:5173)** to access the live Safety Operations Dashboard!

---

## 2. Recommended VS Code Extensions

For the best developer experience, install these recommended extensions from the VS Code Extensions Marketplace (`Ctrl + Shift + X`):

1. **Python** (`ms-python.python`) — IntelliSense, linting, and virtual environment support.
2. **Pylance** (`ms-python.vscode-pylance`) — Fast type checking and auto-completion.
3. **ESLint** (`dbaeumer.vscode-eslint`) — Real-time TypeScript/React linting.
4. **Prettier - Code formatter** (`esbenp.prettier-vscode`) — Automatic code formatting on save.
5. **Thunder Client** or **Postman** — Testing REST API endpoints directly inside VS Code.

---

## 3. Selecting the Python Interpreter in VS Code

To make sure VS Code recognizes all installed libraries (`fastapi`, `torch`, `ultralytics`, `cv2`) without yellow squiggle warnings:

1. Press `Ctrl + Shift + P` to open the Command Palette.
2. Type: **`Python: Select Interpreter`** and hit `Enter`.
3. Choose the virtual environment:
   ```
   .\backend\.venv\Scripts\python.exe
   ```
*(This is already pre-configured in your `.vscode/settings.json`)*.

---

## 4. One-Click Run via VS Code Tasks

We have preconfigured native VS Code tasks in [`.vscode/tasks.json`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/.vscode/tasks.json).

1. Press `Ctrl + Shift + P` (or `F1`).
2. Type: **`Tasks: Run Task`** and press `Enter`.
3. Select **`Run Full System (Backend + Frontend)`**.
4. VS Code will automatically start both the backend API and frontend Vite server in managed background terminal panels.

To run them individually:
- `Tasks: Run Task` -> `Run Backend (FastAPI)`
- `Tasks: Run Task` -> `Run Frontend (Vite)`

---

## 5. Step-by-Step Debugging in VS Code (F5)

You can place breakpoints in any Python file (such as `app/camera/worker.py` or `app/ai/compliance/compliance_engine.py`) and inspect live execution:

1. Open the **Run and Debug** view (`Ctrl + Shift + D`).
2. In the top dropdown, select **`Debug Backend (FastAPI)`**.
3. Press **`F5`** (or click the green Play arrow).
4. VS Code starts the server in debug mode with breakpoints enabled.
5. In a terminal, run `cd frontend && npm run dev` to launch the UI.
6. Trigger an event (upload an image or stand in front of the camera). VS Code will pause execution at your breakpoint, allowing you to inspect variables, call stacks, and tensor values!

---

## 6. Managing Cameras in VS Code

### A. Laptop Integrated Webcam
1. By default, `configs/cameras.yaml` has `camera_01` enabled with device index `"0"`.
2. **Important Asus/Laptop Tip:** If the dashboard feed shows dark gray with a crossed-out camera icon, press **`F10`** or **`Fn + F10`** on your keyboard (or open the physical plastic camera shutter slider above your laptop screen) to allow the physical sensor to capture real pixels.

### B. Android Mobile Camera (Over Wi-Fi)
1. Install **IP Webcam** (free on Google Play Store) or **DroidCam** on your Android phone.
2. Connect your phone to the same Wi-Fi as your computer.
3. Open the app on your phone and tap **Start Server** (it displays a URL like `http://192.168.1.105:8080`).
4. In VS Code, open [`configs/cameras.yaml`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/configs/cameras.yaml) and uncomment the Android camera:
   ```yaml
   - id: "camera_android_wifi"
     name: "Android Phone Cam (Wi-Fi Stream)"
     zone_id: "production_floor"
     source: "http://<YOUR_PHONE_IP>:8080/video"
     source_type: "http"
     enabled: true
     fps_target: 20
     resolution: "1280x720"
   ```
5. Save the file. The backend will automatically connect to your phone's camera!

---

## 7. Running Tests Inside VS Code

### Backend Automated Tests (160 Tests)
Open the backend terminal in VS Code:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest tests/ -v
```
All 160 unit, integration, and security tests should pass.

### Frontend TypeScript Verification
Open the frontend terminal in VS Code:
```powershell
cd frontend
npm run build
```
Verifies zero TypeScript errors and compiles the production bundle in ~8 seconds.

---

## 8. Troubleshooting & Frequently Asked Questions

### Q1: PowerShell says "Script execution is disabled on this system" when running `Activate.ps1`
**Fix:** In VS Code terminal, run this once:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then rerun `.\.venv\Scripts\Activate.ps1`.

---

### Q2: "Port 8000 is already in use"
**Fix:** If an old Uvicorn process is still running in the background, terminate it using PowerShell:
```powershell
Get-Process python* | Stop-Process -Force
```
Then restart the backend.

---

### Q3: How do I access the interactive API docs?
While the backend is running, open:
- Swagger UI: **[http://localhost:8000/docs](http://localhost:8000/docs)**
- ReDoc: **[http://localhost:8000/redoc](http://localhost:8000/redoc)**
- System Health: **[http://localhost:8000/health](http://localhost:8000/health)**
- Live Compliance JSON: **[http://localhost:8000/api/compliance/live](http://localhost:8000/api/compliance/live)**
