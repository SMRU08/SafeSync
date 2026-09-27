"""
analytics.py — SafeSync Analytics & Real-Time Aggregation API
Calculates true incident distributions, severity metrics, and 7-day temporal trends from the database.
Integrates with EventBroadcaster to stream real-time metric updates to connected dashboards.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.risk_alert import Alert, Incident
from app.services.event_broadcaster import broadcaster

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Compliance Trends"])


def calculate_analytics_data(db: Session) -> Dict[str, Any]:
    """Calculates true aggregations from the persistence layer without fabricated stats."""
    now = datetime.now(timezone.utc)

    # 1. Total alerts and status breakdown
    all_alerts = db.query(Alert).all()
    total_alerts = len(all_alerts)

    critical_count = sum(1 for a in all_alerts if a.severity == "CRITICAL")
    high_count = sum(1 for a in all_alerts if a.severity == "HIGH")
    medium_count = sum(1 for a in all_alerts if a.severity == "MEDIUM")
    low_count = sum(1 for a in all_alerts if a.severity == "LOW")

    resolved_count = sum(1 for a in all_alerts if a.status in ("RESOLVED", "DISMISSED"))
    resolution_rate = round((resolved_count / total_alerts * 100), 1) if total_alerts > 0 else 100.0

    ppe_violations = sum(
        1 for a in all_alerts if any(k in a.event_type for k in ["HELMET", "VEST", "GLOVE", "FOOTWEAR", "PPE"])
    )
    fire_hazards = sum(1 for a in all_alerts if "FIRE" in a.event_type)
    smoke_hazards = sum(1 for a in all_alerts if "SMOKE" in a.event_type)

    # 2. 7-Day temporal trajectory
    days_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    trends_7d: List[Dict[str, Any]] = []

    for i in range(6, -1, -1):
        day_date = now - timedelta(days=i)
        day_start = datetime(day_date.year, day_date.month, day_date.day, 0, 0, 0, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        day_alerts = [
            a for a in all_alerts
            if a.created_at and (
                (a.created_at.tzinfo is not None and day_start <= a.created_at < day_end) or
                (a.created_at.tzinfo is None and day_start.replace(tzinfo=None) <= a.created_at < day_end.replace(tzinfo=None))
            )
        ]
        cnt = len(day_alerts)
        res = sum(1 for a in day_alerts if a.status in ("RESOLVED", "DISMISSED"))

        trends_7d.append({
            "label": days_labels[day_date.weekday()],
            "date": day_date.strftime("%b %d"),
            "value": cnt,
            "secondaryValue": res,
            "meta": {
                "critical": sum(1 for a in day_alerts if a.severity == "CRITICAL"),
                "high": sum(1 for a in day_alerts if a.severity == "HIGH"),
                "medium": sum(1 for a in day_alerts if a.severity == "MEDIUM"),
                "low": sum(1 for a in day_alerts if a.severity == "LOW"),
                "details": f"{cnt} recorded telemetry events",
            },
        })

    # 3. 24-hour diurnal distribution (3-hour windows)
    hourly_distribution: List[Dict[str, Any]] = []
    hour_bins = ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
    for idx, h_str in enumerate(hour_bins):
        start_h = idx * 3
        end_h = start_h + 3
        bin_count = sum(1 for a in all_alerts if a.created_at and start_h <= a.created_at.hour < end_h)
        hourly_distribution.append({
            "label": h_str,
            "value": bin_count,
        })

    return {
        "total_alerts": total_alerts,
        "critical_incidents": critical_count,
        "high_incidents": high_count,
        "medium_incidents": medium_count,
        "low_incidents": low_count,
        "ppe_infractions": ppe_violations,
        "fire_hazards": fire_hazards,
        "smoke_hazards": smoke_hazards,
        "resolution_rate": resolution_rate,
        "trends_7d": trends_7d,
        "diurnal_24h": hourly_distribution,
        "severity_breakdown": {
            "critical": {"count": critical_count, "percentage": round((critical_count / total_alerts * 100), 1) if total_alerts else 0},
            "high": {"count": high_count, "percentage": round((high_count / total_alerts * 100), 1) if total_alerts else 0},
            "medium": {"count": medium_count, "percentage": round((medium_count / total_alerts * 100), 1) if total_alerts else 0},
            "low": {"count": low_count, "percentage": round((low_count / total_alerts * 100), 1) if total_alerts else 0},
        },
        "hazard_breakdown": {
            "missing_helmet": sum(1 for a in all_alerts if "HELMET" in a.event_type),
            "missing_safety_vest": sum(1 for a in all_alerts if "VEST" in a.event_type),
            "missing_gloves": sum(1 for a in all_alerts if "GLOVE" in a.event_type),
            "missing_footwear": sum(1 for a in all_alerts if "FOOTWEAR" in a.event_type),
            "fire": fire_hazards,
            "smoke": smoke_hazards,
        },
        "timestamp_utc": now.isoformat(),
    }


@router.get("")
def get_analytics_metrics(db: Session = Depends(get_db)):
    """Returns aggregated real-time safety analytics and trends."""
    return calculate_analytics_data(db)


def broadcast_analytics_update(db: Session):
    """Dispatches real-time updated analytics payload over WebSocket to all connected clients."""
    try:
        data = calculate_analytics_data(db)
        broadcaster.broadcast("AnalyticsUpdated", data)
    except Exception:
        pass
