"""
user.py — SafeSync Phase 10 Step 7
SQLAlchemy Model for Users and Role-Based Access Control (RBAC).
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from enum import Enum

try:
    from app.database.session import Base
except ImportError:
    from backend.app.database.session import Base


def _utc_now():
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class User(Base):
    """
    Authenticated user model with Role-Based Access Control.
    Never stores plaintext passwords.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(128), nullable=True)
    role = Column(String(16), nullable=False, default=UserRole.VIEWER.value, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False)
    updated_at = Column(DateTime, default=_utc_now, nullable=False)
