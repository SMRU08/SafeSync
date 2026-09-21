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

__all__ = [
    "WorkerTracking",
    "PPEObservation",
    "ComplianceObservation",
    "HazardEvent",
    "HazardObservation",
    "Incident",
    "Alert",
    "AlertHistory",
]
