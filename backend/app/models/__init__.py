try:
    from app.models.compliance import (
        WorkerTracking,
        PPEObservation,
        ComplianceObservation,
    )
    from app.models.hazard import (
        HazardEvent,
        HazardObservation,
    )
    from app.models.risk_alert import (
        Incident,
        Alert,
        AlertHistory,
    )
    from app.models.evidence import EvidenceItem
    from app.models.camera import CameraModel
    from app.models.worker_face import RegisteredWorker, AttendanceLog
except ImportError:
    from backend.app.models.compliance import (
        WorkerTracking,
        PPEObservation,
        ComplianceObservation,
    )
    from backend.app.models.hazard import (
        HazardEvent,
        HazardObservation,
    )
    from backend.app.models.risk_alert import (
        Incident,
        Alert,
        AlertHistory,
    )
    from backend.app.models.evidence import EvidenceItem
    from backend.app.models.camera import CameraModel
    from backend.app.models.worker_face import RegisteredWorker, AttendanceLog

__all__ = [
    "WorkerTracking",
    "PPEObservation",
    "ComplianceObservation",
    "HazardEvent",
    "HazardObservation",
    "Incident",
    "Alert",
    "AlertHistory",
    "EvidenceItem",
    "CameraModel",
    "RegisteredWorker",
    "AttendanceLog",
]
