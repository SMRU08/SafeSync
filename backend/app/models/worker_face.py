"""
worker_face.py — SafeSync
SQLAlchemy ORM models for facial recognition worker registry and attendance logging.
"""

from datetime import datetime, date, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from app.database.session import Base


class RegisteredWorker(Base):
    """Stores biometric enrollment data for each registered worker."""

    __tablename__ = "registered_workers"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    job_role = Column(String, nullable=False)
    origin = Column(String, nullable=False)

    # 128-d face embedding stored as a JSON-serialised list[float]
    face_embedding = Column(Text, nullable=True)

    # Optional path to the saved face image on disk
    face_image_path = Column(String, nullable=True)

    registered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    is_active = Column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<RegisteredWorker id={self.worker_id!r} name={self.name!r}>"


class AttendanceLog(Base):
    """Records daily check-in events detected by the facial recognition system."""

    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key references the business-level worker identifier
    worker_id = Column(
        String,
        ForeignKey("registered_workers.worker_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Calendar date of attendance (Date, not DateTime — one record per day per worker)
    date = Column(Date, nullable=False)

    # Exact UTC timestamp when the face was detected / check-in was processed
    check_in_time = Column(DateTime(timezone=True), nullable=False)

    camera_id = Column(String, nullable=False, default="unknown")
    camera_name = Column(String, nullable=False, default="Unknown Camera")

    # Unique constraint: a worker can only check in once per calendar day
    __table_args__ = (
        UniqueConstraint("worker_id", "date", name="uq_attendance_worker_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<AttendanceLog worker_id={self.worker_id!r} date={self.date!r}>"
        )
