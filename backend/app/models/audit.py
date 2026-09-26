"""
audit.py — SafeSync Phase 10 Step 7
SQLAlchemy Model for Security and Operational Audit Logs.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime

try:
    from app.database.session import Base
except ImportError:
    from backend.app.database.session import Base


def _utc_now():
    return datetime.now(timezone.utc)


class AuditLog(Base):
    """
    Immutable audit log recording security and operational actions:
    - Logins and authentication failures
    - Camera worker operations (start/stop/register)
    - Incident actions (acknowledge/resolve/dismiss)
    - User management actions
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=_utc_now, nullable=False, index=True)
    username = Column(String(64), index=True, nullable=True)
    action = Column(String(64), index=True, nullable=False)
    resource = Column(String(128), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True)
