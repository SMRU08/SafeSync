# Installation & Quickstart Guide

This guide details the prerequisites, environment setup, dependency installation, and initial verification steps required to deploy SafeSync.

---

## 1. System Requirements

### Hardware Requirements
- **CPU:** Quad-core processor or better (x86_64 or ARM64)
- **RAM:** Minimum 8 GB (16 GB recommended for 4+ concurrent camera streams)
- **Disk:** 10 GB free space for models, virtual environment, and evidence store
- **GPU (Optional):** NVIDIA GPU with CUDA 11.8+ / 12.x for accelerated multi-stream inference

### Software Requirements
- **Operating System:** Linux (Ubuntu 22.04+ LTS recommended) or Windows 10/11
- **Python:** Version 3.10 to 3.13
- **Node.js:** Version 18.x or 20.x LTS with `npm`
- **Video Tools:** FFmpeg / GStreamer (optional, for advanced RTSP streams)

---

## 2. Installation Steps

### 2.1 Clone the Repository
```bash
git clone https://github.com/SMRU08/SafeSync.git
cd SafeSync
```

### 2.2 Environment Configuration
Copy the template configuration file:
```bash
# On Linux / macOS
cp .env.example .env

# On Windows PowerShell
Copy-Item .env.example .env
```

### 2.3 Backend Setup
Create and activate a dedicated Python virtual environment:

```bash
# Linux / macOS
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# Windows PowerShell
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

### 2.4 Verify Neural Network Checkpoint
Confirm that the production model weights are in place and match the cryptographic SHA-256 checksum:

```bash
# Verify model weight integrity
python -c "import hashlib; print(hashlib.sha256(open('models/detection/ppe_fire_smoke_v2/weights/best.pt', 'rb').read()).hexdigest())"
# Expected: 490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3
```

### 2.5 Frontend Setup
Install frontend packages and verify the build:

```bash
cd frontend
npm install
npm run build
cd ..
```

---

## 3. Verification & First Run

### 3.1 Run Automated Tests
Verify that all 160 unit and integration tests pass cleanly:

```bash
# From backend directory with venv activated
cd backend
pytest tests/ -v
cd ..
```

### 3.2 Launch Backend Service
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Probe: [http://localhost:8000/health/ready](http://localhost:8000/health/ready)

### 3.3 Launch Frontend Dashboard
In a separate terminal:
```bash
cd frontend
npm run dev
```

- SOC Dashboard: [http://localhost:5173](http://localhost:5173)
