"""
evidence.py — RAKSHYA VISION Phase 10 Step 9
SQLAlchemy Database Model for Tamper-Evident Safety Incident Evidence.
Stores cryptographically verified snapshot records, SHA-256 integrity hashes,
and metadata without any PII.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

try:
    from app.database.session import Base
except ImportError:
    from backend.app.database.session import Base


def _utc_now():
    return datetime.now(timezone.utc)


class EvidenceItem(Base):
    """
    Represents an archived visual evidence artifact (raw or annotated snapshot)
    linked to a safety incident, secured with SHA-256 tamper verification.
    """
    __tablename__ = "evidence_items"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String(64), unique=True, index=True, nullable=False, doc="Unique UUID for evidence artifact")
    incident_id = Column(String(64), ForeignKey("incidents.incident_id"), index=True, nullable=False)
    camera_id = Column(String(32), index=True, nullable=False, default="camera_01")
    evidence_type = Column(String(32), nullable=False, default="SNAPSHOT", doc="SNAPSHOT, ANNOTATED_SNAPSHOT, CLIP")
    file_path = Column(String(512), nullable=False, doc="Relative filesystem path from project root")
    file_size_bytes = Column(Integer, nullable=False, default=0)
    sha256_checksum = Column(String(64), nullable=False, index=True, doc="Cryptographic SHA-256 digest of on-disk file")
    metadata_json = Column(Text, nullable=True, doc="JSON string containing detection boxes, scores, and event triggers")
    created_at = Column(DateTime, default=_utc_now, nullable=False, index=True)

    incident = relationship("Incident", back_populates="evidence_items")
