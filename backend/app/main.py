import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.session import check_database_connection, check_database_health, engine, Base
from app.schemas.health import RootResponse, HealthResponse
from app.ai.detection.model_loader import ModelLoader

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("safesync")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing application: %s in %s environment", settings.APP_NAME, settings.APP_ENV)
    
    # 1. Database schema and connectivity check
    Base.metadata.create_all(bind=engine)
    db_ok = check_database_connection()
    if db_ok:
        logger.info("[DATABASE] Connected to %s", settings.DATABASE_URL)
    else:
        logger.error("[DATABASE] Connection failed to %s", settings.DATABASE_URL)

    # 2. AI Engine Model Loader initialization
    try:
        loader = ModelLoader.get_instance()
        loader.load_model()
        logger.info(
            "[AI ENGINE] Model '%s' loaded on device '%s' (classes: %d)",
            getattr(loader, "_loaded_path", "ppe_fire_smoke_v2"),
            loader.device,
            len(loader.classes),
        )
    except Exception as e:
        logger.warning("[AI ENGINE] Model loading error or deferred: %s", e)

    # 3. WebSocket Readiness
    logger.info("[WEBSOCKET] Ready for connections on /ws/events and /ws/alerts")

    # 4. API Confirmation
    logger.info("[API] Started on %s:%s (Environment: %s)", settings.HOST, settings.PORT, settings.APP_ENV)

    # Auto-start configured camera stream workers
    try:
        from app.camera.manager import CameraManager
        CameraManager.get_instance().start_all()
        logger.info("Auto-started enabled camera stream workers.")
    except Exception as e:
        logger.warning("Camera stream worker auto-start deferred: %s", e)

    yield
    logger.info("[API] Shutting down %s...", settings.APP_NAME)
    try:
        from app.camera.manager import CameraManager
        CameraManager.get_instance().stop_all()
    except Exception as e:
        logger.error("Error shutting down CameraManager: %s", e)


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Dynamic CORS Configuration for Production (Hugging Face, Vercel, Netlify, Render, Localhost)
cors_origins = [o for o in settings.CORS_ORIGINS if o]
if not cors_origins:
    cors_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "https://huggingface.co",
        "https://snsahil08-safesync-xerses.hf.space",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.hf\.space|https://.*\.huggingface\.co|https://huggingface\.co|https://.*\.vercel\.app|https://.*\.netlify\.app|https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure database schema is created on startup / import
Base.metadata.create_all(bind=engine)

from app.api.detection import router as detection_router
from app.api.compliance import router as compliance_router
from app.api.hazards import router as hazards_router
from app.api.alerts import router as alerts_router
from app.api.websocket import router as websocket_router
from app.api.cameras import router as cameras_router
from app.api.auth import router as auth_router
from app.api.evidence import router as evidence_router
from app.api.monitoring import router as monitoring_router
from app.api.workers import router as workers_router
from app.api.analytics import router as analytics_router
from app.config import setup_production_logging

setup_production_logging()

app.include_router(detection_router)
app.include_router(compliance_router)
app.include_router(hazards_router)
app.include_router(alerts_router)
app.include_router(websocket_router)
app.include_router(cameras_router)
app.include_router(auth_router)
app.include_router(evidence_router)
app.include_router(monitoring_router)
app.include_router(workers_router)
app.include_router(analytics_router)


import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Optional static frontend mount (for Hugging Face Spaces / all-in-one deployment)
static_candidates = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dist")),
    os.path.abspath(os.path.join(os.getcwd(), "frontend", "dist")),
    os.path.abspath(os.path.join(os.getcwd(), "dist")),
]
frontend_dist = next(
    (d for d in static_candidates if os.path.isdir(d) and os.path.isfile(os.path.join(d, "index.html"))),
    None,
)

@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    if frontend_dist and os.path.isfile(os.path.join(frontend_dist, "index.html")):
        return FileResponse(os.path.join(frontend_dist, "index.html"))
    return {
        "project": "SafeSync",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
@app.get("/api/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def unified_health_check():
    """
    Unified Real Health Check Endpoint (Phase 6).
    Checks real API, Database, AI Engine, and WebSocket statuses.
    """
    # 1. Real API status
    api_info = {
        "status": "online",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0",
    }

    # 2. Real Database probe (executes SELECT 1)
    db_ok = check_database_connection()
    database_info = {
        "status": "connected" if db_ok else "disconnected",
        "dialect": engine.dialect.name,
        "reachable": db_ok,
    }

    # 3. Real AI Engine check (ModelLoader)
    ai_status_val = "unavailable"
    device_str = "cpu"
    classes_count = 0
    model_name = "ppe_fire_smoke_v2"
    is_loaded = False
    try:
        loader = ModelLoader.get_instance()
        if not loader.is_loaded():
            try:
                loader.load_model()
            except Exception as load_err:
                logger.debug("Model lazy load during health check: %s", load_err)

        if loader.is_loaded():
            ai_status_val = "available"
            is_loaded = True
            device_str = loader.device
            classes_count = len(loader.classes)
        else:
            ai_status_val = "initializing"
    except Exception as exc:
        logger.warning("AI Engine health check error: %s", exc)
        ai_status_val = "unavailable"

    ai_engine_info = {
        "status": ai_status_val,
        "loaded": is_loaded,
        "device": device_str,
        "model": model_name,
        "classes": classes_count,
    }

    # 4. Real WebSocket connection manager probe
    try:
        from app.api.websocket import manager as ws_manager
        ws_count = ws_manager.active_count
        ws_info = {
            "status": "connected",
            "active_connections": ws_count,
        }
    except Exception as exc:
        ws_info = {
            "status": "unavailable",
            "error": str(exc),
        }

    overall_status = "healthy" if (db_ok and is_loaded) else ("degraded" if db_ok else "unhealthy")

    return {
        "status": overall_status,
        "api": api_info,
        "database": database_info,
        "database_connected": db_ok,
        "ai_engine": ai_engine_info,
        "ai_status": "Connected" if is_loaded else ("Ready" if ai_status_val == "initializing" else "Unavailable"),
        "model_loaded": is_loaded,
        "websocket": ws_info,
    }


@app.get("/health/database", status_code=status.HTTP_200_OK)
def database_health_check():
    """Returns detailed database health, connectivity, tables, and SQLite PRAGMA status."""
    return check_database_health()


# Mount frontend static assets and SPA fallback if dist is present
if frontend_dist:
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa_frontend(full_path: str):
        if full_path.startswith(("api", "ws", "docs", "redoc", "openapi.json", "health")):
            return None
        target_file = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(target_file):
            return FileResponse(target_file)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


