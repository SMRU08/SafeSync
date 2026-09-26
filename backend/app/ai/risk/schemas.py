"""
schemas.py — SafeSync Phase 7
Pydantic Schemas for Safety Risk Analysis and Smart Alerts.
Defines normalized safety events, transparent risk scores, incidents, and alert lifecycles.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class EventType(str, Enum):
    PPE_VIOLATION = "PPE_VIOLATION"
    MISSING_HELMET = "MISSING_HELMET"
    MISSING_SAFETY_VEST = "MISSING_SAFETY_VEST"
    MISSING_GLOVES = "MISSING_GLOVES"
    MISSING_SAFETY_FOOTWEAR = "MISSING_SAFETY_FOOTWEAR"
    FIRE_DETECTED = "FIRE_DETECTED"
    SMOKE_DETECTED = "SMOKE_DETECTED"
    MULTIPLE_HAZARDS = "MULTIPLE_HAZARDS"
    CAMERA_FAILURE = "CAMERA_FAILURE"
    SYSTEM_FAILURE = "SYSTEM_FAILURE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlarmPriority(str, Enum):
    P0 = "P0"  # CRITICAL: Emergency Fire/Smoke (immediate audible siren & broadcast)
    P1 = "P1"  # HIGH: Persistent Smoke / Escalated Hazard (audible siren)
    P2 = "P2"  # MEDIUM: Confirmed PPE Violation (visual UI alert only, NO siren)
    P3 = "P3"  # LOW: System Warning / Camera Offline / Advisory


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class NormalizedSafetyEvent(BaseModel):
    """
    Common internal safety event schema ingesting from compliance and hazard streams.
    """
    event_id: str = Field(..., description="Unique event UUID")
    event_type: EventType
    timestamp: str
    camera_id: str = "camera_01"
    zone_id: str = "UNKNOWN"
    track_id: Optional[int] = Field(None, description="Worker track ID if person-related")
    hazard_event_id: Optional[str] = Field(None, description="Hazard track ID if fire/smoke")
    confidence: float = 0.0
    duration_seconds: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)
    source: str = "vision"


class RiskScoreBreakdown(BaseModel):
    """
    Explainable factors detailing how the numerical risk score was calculated.
    """
    risk_score: int = Field(..., ge=0, le=100, description="Final clamped score 0-100")
    risk_level: RiskLevel
    factors: Dict[str, float] = Field(
        ...,
        description="Explainable breakdown: base_severity, persistence, affected_workers, repetition, zone_multiplier, multi_hazard"
    )


class IncidentSchema(BaseModel):
    """
    State container for an ongoing or resolved safety incident.
    """
    incident_id: str
    timestamp: str
    camera_id: str
    zone_id: str
    event_types: List[EventType]
    affected_tracks: List[int] = Field(default_factory=list)
    risk_score: int
    risk_level: RiskLevel
    status: IncidentStatus
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None


class AlertSchema(BaseModel):
    """
    Actionable alert produced from an active incident.
    """
    alert_id: str
    incident_id: str
    severity: RiskLevel
    priority: AlarmPriority = AlarmPriority.P2
    is_audible: bool = False
    title: str
    message: str
    camera_id: str
    zone_id: str
    event_type: EventType
    timestamp: str
    status: AlertStatus
    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None


class AlertHistorySchema(BaseModel):
    """
    Audit log record of alert state changes, deduplications, and escalations.
    """
    id: Optional[int] = None
    alert_id: str
    incident_id: str
    action: str = Field(..., description="CREATED, DEDUPLICATED, COOLDOWN_SUPPRESSED, ESCALATED, ACKNOWLEDGED, RESOLVED, DISMISSED")
    previous_level: Optional[RiskLevel] = None
    new_level: Optional[RiskLevel] = None
    reason: str
    timestamp: str


class RiskSummaryResponse(BaseModel):
    """
    High-level operational overview returned by /api/risk/summary.
    """
    active_alerts: int
    critical: int
    high: int
    medium: int
    low: int
    open_incidents: int
    timestamp_utc: str
