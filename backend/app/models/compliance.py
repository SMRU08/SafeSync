"""
compliance.py — RAKSHYA VISION Phase 5
SQLAlchemy Database Models for Worker Tracking and Anonymous Compliance Observations.
Strictly stores temporary anonymous track IDs without any Personally Identifiable Information (PII).
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

try:
    from app.database.session import Base
except ImportError:
    from backend.app.database.session import Base


class WorkerTracking(Base):
    """
    Records temporary anonymous track IDs generated during active camera or video sessions.
    """
    __tablename__ = "worker_tracking"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, index=True, nullable=False, doc="Temporary anonymous worker track ID")
    session_id = Column(String(64), index=True, nullable=True, doc="Session or stream identifier")
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_frames = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    observations = relationship("ComplianceObservation", back_populates="worker", cascade="all, delete-orphan")


class PPEObservation(Base):
    """
    Records spatial PPE detections associated with anonymous workers.
    """
    __tablename__ = "ppe_observations"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, index=True, nullable=False)
    frame_id = Column(Integer, nullable=True)
    item_type = Column(String(32), nullable=False, doc="helmet, safety_vest, gloves, safety_footwear")
    state = Column(String(16), nullable=False, doc="PRESENT, ABSENT, UNKNOWN")
    confidence = Column(Float, nullable=True)
    is_occluded = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ComplianceObservation(Base):
    """
    Records overall temporal compliance status evaluated for anonymous workers.
    """
    __tablename__ = "compliance_observations"

    id = Column(Integer, primary_key=True, index=True)
    worker_tracking_id = Column(Integer, ForeignKey("worker_tracking.id"), nullable=True)
    track_id = Column(Integer, index=True, nullable=False)
    frame_id = Column(Integer, nullable=True)
    overall_status = Column(String(16), nullable=False, doc="COMPLIANT, NON_COMPLIANT, UNKNOWN")
    helmet_status = Column(String(16), nullable=False)
    vest_status = Column(String(16), nullable=False)
    gloves_status = Column(String(16), nullable=False)
    footwear_status = Column(String(16), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    worker = relationship("WorkerTracking", back_populates="observations")
