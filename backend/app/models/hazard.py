"""
hazard.py — RAKSHYA VISION Phase 6
SQLAlchemy Database Models for Fire and Smoke Hazard Analysis.
Stores persistent hazard events and individual frame observations.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

try:
    from app.database.session import Base
except ImportError:
    from backend.app.database.session import Base


def _utc_now():
    return datetime.now(timezone.utc)


class HazardEvent(Base):
    """
    Represents an aggregated, persistent hazard occurrence (e.g. HAZARD-0001)
    tracked over time across frames.
    """
    __tablename__ = "hazard_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(32), unique=True, index=True, nullable=False, doc="Anonymous hazard ID, e.g. HAZARD-0001")
    hazard_type = Column(String(16), nullable=False, doc="fire or smoke")
    state = Column(String(16), nullable=False, default="SUSPECTED", index=True, doc="NO_HAZARD, SUSPECTED, CONFIRMED, CLEARED")
    camera_id = Column(String(32), index=True, nullable=True, doc="Camera identifier, e.g. camera_01")
    zone_id = Column(String(64), index=True, nullable=False, default="UNKNOWN", doc="Zone identifier or UNKNOWN")
    first_seen = Column(DateTime, default=_utc_now, nullable=False)
    last_seen = Column(DateTime, default=_utc_now, nullable=False, index=True)
    duration_seconds = Column(Float, default=0.0, nullable=False)
    detection_count = Column(Integer, default=1, nullable=False)
    average_confidence = Column(Float, default=0.0, nullable=False)
    max_confidence = Column(Float, default=0.0, nullable=False)

    observations = relationship("HazardObservation", back_populates="event", cascade="all, delete-orphan")


class HazardObservation(Base):
    """
    Records an individual frame-level fire or smoke detection belonging to a hazard event.
    """
    __tablename__ = "hazard_observations"

    id = Column(Integer, primary_key=True, index=True)
    hazard_event_id = Column(Integer, ForeignKey("hazard_events.id"), nullable=False)
    event_id = Column(String(32), index=True, nullable=False, doc="Denormalized event_id for fast querying")
    frame_number = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=_utc_now, nullable=False, index=True)
    hazard_type = Column(String(16), nullable=False, doc="fire or smoke")
    confidence = Column(Float, nullable=False)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)

    event = relationship("HazardEvent", back_populates="observations")
