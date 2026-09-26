"""
Risk Analysis & Smart Alert Engine Package — SafeSync Phase 7
"""

try:
    from app.ai.risk.schemas import (
        EventType,
        RiskLevel,
        IncidentStatus,
        AlertStatus,
        NormalizedSafetyEvent,
        RiskScoreBreakdown,
        IncidentSchema,
        AlertSchema,
        AlertHistorySchema,
        RiskSummaryResponse,
    )
except ImportError:
    from backend.app.ai.risk.schemas import (
        EventType,
        RiskLevel,
        IncidentStatus,
        AlertStatus,
        NormalizedSafetyEvent,
        RiskScoreBreakdown,
        IncidentSchema,
        AlertSchema,
        AlertHistorySchema,
        RiskSummaryResponse,
    )

__all__ = [
    "EventType",
    "RiskLevel",
    "IncidentStatus",
    "AlertStatus",
    "NormalizedSafetyEvent",
    "RiskScoreBreakdown",
    "IncidentSchema",
    "AlertSchema",
    "AlertHistorySchema",
    "RiskSummaryResponse",
]
