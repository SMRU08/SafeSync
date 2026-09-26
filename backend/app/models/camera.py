"""
camera.py — SafeSync
SQLAlchemy Database Model for Persistent Camera Configurations.
Enables dynamic addition, removal, and modification of surveillance cameras with persistent storage.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean

try:
    from app.database.session import Base
except ImportError:
    from backend.app.database.session import Base


class CameraModel(Base):
    """
    Persistent registry of cameras configured in SafeSync.
    """
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(64), unique=True, index=True, nullable=False, doc="Unique camera identifier, e.g. camera_01")
    name = Column(String(128), nullable=False, doc="Human-readable camera name")
    location = Column(String(128), nullable=True, default="", doc="Physical location/station description")
    zone_id = Column(String(64), nullable=False, default="production_floor", doc="Associated facility zone ID")
    source = Column(String(512), nullable=False, doc="RTSP URL, device index, or stream URL")
    source_type = Column(String(32), nullable=False, default="usb", doc="usb, rtsp, http, synthetic, file")
    enabled = Column(Boolean, default=True, nullable=False)
    fps_target = Column(Integer, default=30, nullable=False)
    resolution = Column(String(32), default="1280x720", nullable=True)
    timeout_seconds = Column(Float, default=5.0, nullable=False)
    speaker_enabled = Column(Boolean, default=True, nullable=False, doc="Camera speaker audio alert status (ON/OFF)")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
