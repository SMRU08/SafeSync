# SafeSync — Backend

FastAPI backend service for SafeSync ("AI Vision-Based Safety Monitoring").

## Features (Phase 1)
- FastAPI application with lifespan structured logging
- SQLite database layer using SQLAlchemy
- Environment-based configuration using `pydantic-settings`
- Restricted CORS for local frontend integration
- Health check and root status endpoints
- Pytest automated test suite

## Directory Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   ├── ai/
│   ├── services/
│   ├── database/
│   │   ├── __init__.py
│   │   └── session.py
│   └── schemas/
│       ├── __init__.py
│       └── health.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── .env.example
├── requirements.txt
└── README.md
```

## Setup & Running

### 1. Create Virtual Environment
```powershell
python -m venv .venv
```

### 2. Activate Virtual Environment
**Windows PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run Development Server
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API Root: `http://localhost:8000/`
Health Check: `http://localhost:8000/health`
Interactive Docs: `http://localhost:8000/docs`

### 5. Run Tests
```powershell
pytest -v
```
