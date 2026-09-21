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

__all__ = [
    "WorkerTracking",
    "PPEObservation",
    "ComplianceObservation",
    "HazardEvent",
    "HazardObservation",
]
