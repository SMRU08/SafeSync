import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.session import check_database_connection, engine, Base
from app.schemas.health import RootResponse, HealthResponse

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("rakshya_vision")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing application: %s in %s environment", settings.APP_NAME, settings.APP_ENV)
    # Ensure database tables/schema can connect
    Base.metadata.create_all(bind=engine)
    db_ok = check_database_connection()
    if db_ok:
        logger.info("Database connectivity established successfully at %s", settings.DATABASE_URL)
    else:
        logger.warning("Database connectivity check failed.")
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
from app.ai.detection.model_loader import ModelLoader
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


@app.get("/", response_model=RootResponse, status_code=status.HTTP_200_OK)
def read_root():
    return {
        "project": "RAKSHYA VISION",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health_check():
    db_ok = check_database_connection()
    try:
        loader = ModelLoader.get_instance()
        ai_status = "Connected" if loader.is_loaded() else "Ready"
    except Exception:
        ai_status = "Unavailable"

    return {
        "status": "healthy",
        "database": "connected" if db_ok else "disconnected",
        "ai_engine": ai_status
    }


@app.get("/health/database", status_code=status.HTTP_200_OK)
def database_health_check():
    """Returns detailed database health, connectivity, tables, and SQLite PRAGMA status."""
    return check_database_health()

