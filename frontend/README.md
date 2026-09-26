# SafeSync — Frontend

React + TypeScript dashboard placeholder for SafeSync ("AI Vision-Based Safety Monitoring").

## Features (Phase 1)
- React 18 + TypeScript + Vite build setup
- Clean modular structure: `components`, `pages`, `services`, `hooks`, `types`, `utils`
- Real-time polling health check against FastAPI backend (`GET /health`)
- Responsive system status card layout:
  - Backend: Live connection status
  - AI Engine: Static "Not Connected" indicator (Phase 1 foundation)
  - Database: Live database status from backend health probe
- Error boundary handling and connection retry

## Commands

### 1. Install Dependencies
```powershell
npm install
```

### 2. Run Development Server
```powershell
npm run dev
```
Local address: `http://localhost:5173`

### 3. Build for Production
```powershell
npm run build
```