# RAKSHYA VISION

> **AI Vision-Based Safety Monitoring System**

**Current Phase:** Phase 1 — Foundation (Completed)

RAKSHYA VISION is an intelligent workplace and industrial safety monitoring platform engineered to detect compliance with Personal Protective Equipment (PPE) and environmental hazards:
- **Person**
- **Helmet** / Non-compliance
- **Safety Vest** / Non-compliance
- **Gloves** / Non-compliance
- **Safety Footwear** / Non-compliance
- **Fire**
- **Smoke**

> [!IMPORTANT]
> **AI model training has NOT started yet.** Phase 1 establishes the architectural foundation, environment isolation, database infrastructure, communication endpoints, and testing framework.

---

## Technology Stack

- **Backend:** Python 3.13, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy, OpenCV, NumPy
- **Frontend:** React 18, TypeScript, Vite
- **Database:** SQLite (`rakshya_vision.db`)
- **Testing:** Pytest, HTTPX

---

## Directory Layout

```
RAKSHYA-VISION/
├── backend/            # FastAPI application, database session, schemas, and tests
├── frontend/           # React + TypeScript Vite dashboard
├── models/             # Target directories for trained models (PPE, Fire/Smoke)
├── datasets/           # Raw and processed datasets (to be populated in Phase 2)
├── scripts/            # Automation and data processing scripts
├── docs/               # System and architecture documentation
├── .gitignore          # Version control ignore rules
├── PROJECT_STATUS.md   # Current environment and inspection log
└── README.md           # Project documentation
```

---

## Quick Start & Verification Commands

### 1. Backend Setup & Activation
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run Backend Server
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Root: `http://localhost:8000/`
- Health Endpoint: `http://localhost:8000/health`
- OpenAPI Swagger Docs: `http://localhost:8000/docs`

### 3. Run Backend Tests
```powershell
pytest -v
```

### 4. Frontend Installation & Startup
```powershell
cd ../frontend
npm install
npm run dev
```
- Dashboard Interface: `http://localhost:5173`

### 5. Frontend Production Build
```powershell
npm run build
```