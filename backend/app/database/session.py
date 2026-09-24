"""
session.py — RAKSHYA VISION Phase 10 Step 4
Hardened Database Session Management with SQLite Write-Ahead Logging (WAL),
Connection Pooling, Foreign Key Enforcement, and Health Diagnostics.
"""

import os
import logging
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text, event, inspect
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.config import settings

logger = logging.getLogger(__name__)

is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False, "timeout": 15} if is_sqlite else {}

engine_kwargs: Dict[str, Any] = {
    "connect_args": connect_args,
    "echo": False,
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    })

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)


@event.listens_for(engine, "connect")
def configure_sqlite_pragmas(dbapi_connection, connection_record):
    """
    Configures SQLite connection-level pragmas for production edge operations:
    - journal_mode=WAL: Enables Write-Ahead Logging for non-blocking concurrent readers.
    - synchronous=NORMAL: Safe durability without excessive fsync() calls in WAL mode.
    - foreign_keys=ON: Enforces relational integrity across tables.
    - busy_timeout=5000: Prevents 'database locked' errors by waiting up to 5s.
    """
    if is_sqlite:
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA busy_timeout=5000;")
            cursor.close()
        except Exception as e:
            logger.warning(f"Could not configure SQLite PRAGMAs: {e}")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    Dependency provider yielding thread-safe database sessions
    with automatic rollback on unhandled exceptions and guaranteed cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as exc:
        db.rollback()
        logger.error(f"Database session exception caught, rolled back transaction: {exc}")
        raise
    finally:
        db.close()


def get_sqlite_pragmas(engine_instance=None) -> Dict[str, Any]:
    """
    Queries and returns active SQLite PRAGMA configuration.
    """
    eng = engine_instance or engine
    if not str(eng.url).startswith("sqlite"):
        return {"status": "not_sqlite", "dialect": eng.dialect.name}

    try:
        with eng.connect() as conn:
            jm = conn.execute(text("PRAGMA journal_mode;")).scalar()
            fk = conn.execute(text("PRAGMA foreign_keys;")).scalar()
            bt = conn.execute(text("PRAGMA busy_timeout;")).scalar()
            sync = conn.execute(text("PRAGMA synchronous;")).scalar()

        sync_names = {0: "OFF", 1: "NORMAL", 2: "FULL", 3: "EXTRA"}
        sync_label = sync_names.get(sync, str(sync))

        return {
            "journal_mode": str(jm).lower() if jm else "unknown",
            "foreign_keys": int(fk) if fk is not None else 0,
            "busy_timeout": int(bt) if bt is not None else 0,
            "synchronous": sync_label,
        }
    except Exception as e:
        logger.error(f"Failed to query SQLite PRAGMAs: {e}")
        return {"error": str(e)}


def ensure_schema_migrations(engine_instance=None):
    """Safely adds missing columns to existing SQLite tables if not present."""
    eng = engine_instance or engine
    try:
        insp = inspect(eng)
        if "cameras" in insp.get_table_names():
            columns = [c["name"] for c in insp.get_columns("cameras")]
            if "speaker_enabled" not in columns:
                with eng.connect() as conn:
                    conn.execute(text("ALTER TABLE cameras ADD COLUMN speaker_enabled BOOLEAN DEFAULT 1;"))
                    conn.commit()
                logger.info("Migrated SQLite schema: added 'speaker_enabled' column to cameras table.")
    except Exception as exc:
        logger.debug("Schema migration notice: %s", exc)


def check_database_connection(engine_instance=None) -> bool:
    """Simple query probe checking basic database reachability."""
    eng = engine_instance or engine
    try:
        with eng.connect() as connection:
            connection.execute(text("SELECT 1;"))
        ensure_schema_migrations(eng)
        return True
    except Exception as exc:
        logger.error("Database connection check failed: %s", exc)
        return False


def check_database_health(engine_instance=None) -> Dict[str, Any]:
    """
    Comprehensive database health assessment verifying:
    - Reachability
    - Execution of basic queries
    - Availability of expected tables
    - Active SQLite PRAGMA configuration
    """
    eng = engine_instance or engine
    health: Dict[str, Any] = {
        "status": "healthy",
        "reachable": False,
        "query_ok": False,
        "dialect": eng.dialect.name,
        "database_url": str(eng.url).split("@")[-1],  # masks password if any
        "tables_available": [],
        "expected_tables_found": False,
        "pragmas": {},
    }

    try:
        with eng.connect() as conn:
            # 1. Query reachability
            res = conn.execute(text("SELECT 1;")).scalar()
            health["reachable"] = True
            health["query_ok"] = (res == 1)
            health["can_query"] = (res == 1)

            # 2. Table inspection
            insp = inspect(conn)
            table_names = insp.get_table_names()
            health["tables_available"] = table_names

            core_tables = {"incidents", "alerts", "alert_history", "hazard_events", "worker_tracking"}
            found = core_tables.intersection(set(table_names))
            health["expected_tables_found"] = len(found) >= 3

        # 3. Pragmas
        if str(eng.url).startswith("sqlite"):
            pragmas = get_sqlite_pragmas(eng)
            health["pragmas"] = pragmas
            if pragmas.get("journal_mode") != "wal" or pragmas.get("foreign_keys") != 1:
                health["status"] = "degraded"

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health["status"] = "unhealthy"
        health["error"] = str(e)

    return health
