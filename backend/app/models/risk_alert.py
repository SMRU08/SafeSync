"""
risk_alert.py — RAKSHYA VISION Phase 7
SQLAlchemy Database Models for Safety Incidents, Smart Alerts, and Audit History.
Stores anonymized incident lifecycles without any PII.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

try:
    from app.database.session import Base
except ImportError:
    from backend.app.database.session import Base


def _utc_now():
    return datetime.now(timezone.utc)


class Incident(Base):
    """
    Represents an ongoing or historical safety incident encompassing one or more normalized events.
    """
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(64), unique=True, index=True, nullable=False, doc="Unique UUID for incident")
    status = Column(String(16), nullable=False, default="OPEN", index=True, doc="OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED")
    event_types = Column(String(256), nullable=False, doc="Comma-separated event types, e.g. MISSING_HELMET,SMOKE_DETECTED")
    camera_id = Column(String(32), index=True, nullable=False, default="camera_01")
    zone_id = Column(String(64), index=True, nullable=False, default="UNKNOWN")
    affected_tracks = Column(String(256), nullable=False, default="[]", doc="JSON list of anonymous track IDs")
    risk_score = Column(Integer, nullable=False, default=0, doc="Calculated score 0-100")
    risk_level = Column(String(16), nullable=False, default="LOW", index=True, doc="LOW, MEDIUM, HIGH, CRITICAL")
    factors_json = Column(Text, nullable=True, doc="JSON string of explainable risk factors")
    created_at = Column(DateTime, default=_utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=_utc_now, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    alerts = relationship("Alert", back_populates="incident", cascade="all, delete-orphan")
    evidence_items = relationship("EvidenceItem", back_populates="incident", cascade="all, delete-orphan")


class Alert(Base):
    """
    Actionable smart alert derived from an incident, governed by deduplication and cooldown policies.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(64), unique=True, index=True, nullable=False, doc="Unique UUID for alert")
    incident_id = Column(String(64), ForeignKey("incidents.incident_id"), index=True, nullable=False)
    severity = Column(String(16), nullable=False, default="LOW", index=True, doc="LOW, MEDIUM, HIGH, CRITICAL")
    title = Column(String(128), nullable=False)
    message = Column(String(512), nullable=False)
    camera_id = Column(String(32), index=True, nullable=False, default="camera_01")
    zone_id = Column(String(64), index=True, nullable=False, default="UNKNOWN")
    event_type = Column(String(64), nullable=False, index=True)
    status = Column(String(16), nullable=False, default="ACTIVE", index=True, doc="ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED")
    created_at = Column(DateTime, default=_utc_now, nullable=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    incident = relationship("Incident", back_populates="alerts")


class AlertHistory(Base):
    """
    Audit log record capturing alert lifecycle actions (creation, cooldown suppression, escalation, resolution).
    """
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(64), index=True, nullable=False)
    incident_id = Column(String(64), index=True, nullable=False)
    action = Column(String(32), nullable=False, doc="CREATED, DEDUPLICATED, COOLDOWN_SUPPRESSED, ESCALATED, ACKNOWLEDGED, RESOLVED, DISMISSED")
    previous_level = Column(String(16), nullable=True)
    new_level = Column(String(16), nullable=True)
    reason = Column(String(256), nullable=False)
    timestamp = Column(DateTime, default=_utc_now, nullable=False, index=True)
