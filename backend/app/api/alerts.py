"""
alerts.py — SafeSync Phase 7
FastAPI Router for Safety Risk Assessment, Incidents, and Smart Alerts.
Provides REST endpoints for alert lifecycle management, history, and real-time risk summaries.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Query, Path, HTTPException, Depends, status
from sqlalchemy.orm import Session

try:
    from app.database.session import get_db
    from app.models.risk_alert import Incident, Alert, AlertHistory
    from app.ai.risk.schemas import (
        AlertSchema,
        IncidentSchema,
        AlertHistorySchema,
        RiskSummaryResponse,
        RiskLevel,
        AlertStatus,
        IncidentStatus,
        EventType,
    )
    from app.services.alert_engine import AlertEngine
    from app.security.auth import require_role
except ImportError:
    from backend.app.database.session import get_db
    from backend.app.models.risk_alert import Incident, Alert, AlertHistory
    from backend.app.ai.risk.schemas import (
        AlertSchema,
        IncidentSchema,
        AlertHistorySchema,
        RiskSummaryResponse,
        RiskLevel,
        AlertStatus,
        IncidentStatus,
        EventType,
    )
    from backend.app.services.alert_engine import AlertEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Risk Analysis & Smart Alerts"])

_alert_engine_instance: Optional[AlertEngine] = None


def get_alert_engine() -> AlertEngine:
    global _alert_engine_instance
    if _alert_engine_instance is None:
        _alert_engine_instance = AlertEngine()
    return _alert_engine_instance


# ─── Risk Summary ─────────────────────────────────────────────────────────────

@router.get("/risk/summary", response_model=RiskSummaryResponse)
def get_risk_summary(
    db: Session = Depends(get_db),
    engine: AlertEngine = Depends(get_alert_engine),
):
    """
    Returns real-time risk summary statistics directly from the database.
    Never returns fabricated values.
    """
    return engine.get_risk_summary(db)


# ─── Alerts Endpoints ─────────────────────────────────────────────────────────

@router.get("/alerts", response_model=List[dict])
def list_alerts(
    status: Optional[str] = Query(None, description="Filter: ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED"),
    risk_level: Optional[str] = Query(None, description="Filter: LOW, MEDIUM, HIGH, CRITICAL"),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    zone_id: Optional[str] = Query(None, description="Filter by zone ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Lists alerts with configurable filtering by status, severity, camera, or zone.
    """
    query = db.query(Alert)

    if status:
        query = query.filter(Alert.status == status.upper())
    if risk_level:
        query = query.filter(Alert.severity == risk_level.upper())
    if camera_id:
        query = query.filter(Alert.camera_id == camera_id)
    if zone_id:
        query = query.filter(Alert.zone_id == zone_id)
    if event_type:
        query = query.filter(Alert.event_type == event_type.upper())

    records = query.order_by(Alert.id.desc()).limit(limit).all()
    results = []
    for r in records:
        ev_upper = str(r.event_type).upper()
        if "FIRE" in ev_upper or "MULTIPLE" in ev_upper:
            p = "P0"
            aud = True
        elif "SMOKE" in ev_upper:
            p = "P0" if r.severity == "CRITICAL" else "P1"
            aud = True
        elif any(k in ev_upper for k in ["HELMET", "VEST", "GLOVE", "FOOTWEAR", "PPE"]):
            p = "P2"
            aud = False
        else:
            p = "P3"
            aud = False

        results.append({
            "alert_id": r.alert_id,
            "incident_id": r.incident_id,
            "severity": r.severity,
            "priority": p,
            "is_audible": aud,
            "title": r.title,
            "message": r.message,
            "camera_id": r.camera_id,
            "zone_id": r.zone_id,
            "event_type": r.event_type,
            "status": r.status,
            "timestamp": r.created_at.isoformat(),
            "acknowledged_at": r.acknowledged_at.isoformat() if r.acknowledged_at else None,
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        })
    return results


@router.get("/alerts/{alert_id}")
def get_alert_detail(
    alert_id: str = Path(..., description="Alert UUID"),
    db: Session = Depends(get_db),
):
    """
    Retrieves full details and history audit trail for an alert.
    """
    db_alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not db_alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert '{alert_id}' not found.")

    history_records = db.query(AlertHistory).filter(AlertHistory.alert_id == alert_id).order_by(AlertHistory.id.asc()).all()

    return {
        "alert_id": db_alert.alert_id,
        "incident_id": db_alert.incident_id,
        "severity": db_alert.severity,
        "title": db_alert.title,
        "message": db_alert.message,
        "camera_id": db_alert.camera_id,
        "zone_id": db_alert.zone_id,
        "event_type": db_alert.event_type,
        "status": db_alert.status,
        "created_at": db_alert.created_at.isoformat(),
        "acknowledged_at": db_alert.acknowledged_at.isoformat() if db_alert.acknowledged_at else None,
        "resolved_at": db_alert.resolved_at.isoformat() if db_alert.resolved_at else None,
        "history": [
            {
                "action": h.action,
                "previous_level": h.previous_level,
                "new_level": h.new_level,
                "reason": h.reason,
                "timestamp": h.timestamp.isoformat(),
            }
            for h in history_records
        ],
    }


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertSchema)
def acknowledge_alert(
    alert_id: str = Path(..., description="Alert UUID"),
    db: Session = Depends(get_db),
    engine: AlertEngine = Depends(get_alert_engine),
    current_user=Depends(require_role(["ADMIN", "OPERATOR"])),
):
    """
    Acknowledges an active alert, updating both the alert and its linked incident.
    Requires ADMIN or OPERATOR role.
    """
    try:
        return engine.acknowledge_alert(alert_id, db)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.post("/alerts/{alert_id}/resolve", response_model=AlertSchema)
def resolve_alert(
    alert_id: str = Path(..., description="Alert UUID"),
    db: Session = Depends(get_db),
    engine: AlertEngine = Depends(get_alert_engine),
    current_user=Depends(require_role(["ADMIN", "OPERATOR"])),
):
    """
    Resolves an alert and marks its parent incident as RESOLVED.
    Requires ADMIN or OPERATOR role.
    """
    try:
        return engine.resolve_alert(alert_id, db)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.post("/alerts/{alert_id}/dismiss", response_model=AlertSchema)
def dismiss_alert(
    alert_id: str = Path(..., description="Alert UUID"),
    db: Session = Depends(get_db),
    engine: AlertEngine = Depends(get_alert_engine),
    current_user=Depends(require_role(["ADMIN", "OPERATOR"])),
):
    """
    Dismisses an alert as false alarm or non-actionable advisory.
    Requires ADMIN or OPERATOR role.
    """
    try:
        return engine.dismiss_alert(alert_id, db)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


# ─── Incidents Endpoints ──────────────────────────────────────────────────────

@router.get("/incidents", response_model=List[dict])
def list_incidents(
    status: Optional[str] = Query(None, description="Filter: OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Lists all safety incidents.
    """
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status.upper())

    records = query.order_by(Incident.id.desc()).limit(limit).all()
    return [
        {
            "incident_id": r.incident_id,
            "status": r.status,
            "event_types": r.event_types.split(","),
            "camera_id": r.camera_id,
            "zone_id": r.zone_id,
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        }
        for r in records
    ]


@router.get("/incidents/{incident_id}")
def get_incident_detail(
    incident_id: str = Path(..., description="Incident UUID"),
    db: Session = Depends(get_db),
):
    """
    Retrieves full incident details and its associated alerts.
    """
    db_incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")

    return {
        "incident_id": db_incident.incident_id,
        "status": db_incident.status,
        "event_types": db_incident.event_types.split(","),
        "camera_id": db_incident.camera_id,
        "zone_id": db_incident.zone_id,
        "affected_tracks": db_incident.affected_tracks,
        "risk_score": db_incident.risk_score,
        "risk_level": db_incident.risk_level,
        "factors": db_incident.factors_json,
        "created_at": db_incident.created_at.isoformat(),
        "updated_at": db_incident.updated_at.isoformat(),
        "resolved_at": db_incident.resolved_at.isoformat() if db_incident.resolved_at else None,
        "alerts": [
            {
                "alert_id": a.alert_id,
                "severity": a.severity,
                "title": a.title,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
            }
            for a in db_incident.alerts
        ],
    }


@router.post("/incidents/{incident_id}/acknowledge")
def acknowledge_incident(
    incident_id: str = Path(..., description="Incident UUID"),
    db: Session = Depends(get_db),
    engine: AlertEngine = Depends(get_alert_engine),
    current_user=Depends(require_role(["ADMIN", "OPERATOR"])),
):
    """
    Acknowledges an incident and all associated active alerts.
    Requires ADMIN or OPERATOR role.
    """
    try:
        return engine.acknowledge_incident(incident_id, db)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.post("/incidents/{incident_id}/resolve")
def resolve_incident(
    incident_id: str = Path(..., description="Incident UUID"),
    db: Session = Depends(get_db),
    engine: AlertEngine = Depends(get_alert_engine),
    current_user=Depends(require_role(["ADMIN", "OPERATOR"])),
):
    """
    Resolves an incident and all associated alerts.
    Requires ADMIN or OPERATOR role.
    """
    try:
        return engine.resolve_incident(incident_id, db)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))



@router.get("/alerts/providers/status")
def get_alert_providers_status():
    """
    Returns authentic operational statuses for all external notification channels (Webhook, Email, SMS).
    Never reports false success: shows ENABLED, DISABLED, NOT_CONFIGURED, or ERROR.
    """
    from app.services.alert_providers.registry import ProviderRegistry
    return ProviderRegistry.get_instance().get_all_statuses()


@router.get("/audio/alerts", response_model=List[dict])
def get_recent_audio_alerts(
    camera_id: Optional[str] = Query(None, description="Optional camera ID filter"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Returns recent dynamic audio compliance alerts triggered or suppressed per camera.
    """
    try:
        from app.services.audio_alert_engine import AudioAlertEngine
        return AudioAlertEngine.get_instance().get_recent_alerts(limit=limit, camera_id=camera_id)
    except Exception as e:
        logger.error("Error retrieving audio alerts: %s", e)
        return []

