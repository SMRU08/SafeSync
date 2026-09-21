"""
event_normalizer.py — RAKSHYA VISION Phase 7
Normalizes raw vision outputs from Phase 5 (Compliance) and Phase 6 (Hazards)
into standardized NormalizedSafetyEvent envelopes.
Enforces the strict rule: UNKNOWN state NEVER generates a violation.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

try:
    from app.ai.risk.schemas import EventType, NormalizedSafetyEvent
    from app.ai.compliance.schemas import ComplianceAnalysisResponse, WorkerTrack, PPEState, PPEItemType
    from app.ai.hazards.schemas import HazardAnalysisResponse, HazardEventDetail, HazardState, HazardType
except ImportError:
    from backend.app.ai.risk.schemas import EventType, NormalizedSafetyEvent
    from backend.app.ai.compliance.schemas import ComplianceAnalysisResponse, WorkerTrack, PPEState, PPEItemType
    from backend.app.ai.hazards.schemas import HazardAnalysisResponse, HazardEventDetail, HazardState, HazardType


class EventNormalizer:
    """
    Translates verified compliance and hazard states into normalized safety events.
    """

    @staticmethod
    def from_compliance_response(
        response: ComplianceAnalysisResponse,
        camera_id: str = "camera_01",
        zone_id: str = "UNKNOWN",
    ) -> List[NormalizedSafetyEvent]:
        """
        Extracts confirmed PPE violations from Phase 5 workers.
        STRICT RULE: UNKNOWN or PRESENT states NEVER generate violations.
        Only confirmed ABSENT triggers MISSING_* events.
        """
        events: List[NormalizedSafetyEvent] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for worker in response.workers:
            track_id = worker.track_id
            for item_name, obs in worker.ppe_details.items():
                # Enforce: UNKNOWN must NOT become MISSING_*
                if obs.state != PPEState.ABSENT:
                    continue

                # Map to specific event type
                ev_type = EventType.PPE_VIOLATION
                if obs.item_type == PPEItemType.HELMET:
                    ev_type = EventType.MISSING_HELMET
                elif obs.item_type == PPEItemType.SAFETY_VEST:
                    ev_type = EventType.MISSING_SAFETY_VEST
                elif obs.item_type == PPEItemType.GLOVES:
                    ev_type = EventType.MISSING_GLOVES
                elif obs.item_type == PPEItemType.SAFETY_FOOTWEAR:
                    ev_type = EventType.MISSING_SAFETY_FOOTWEAR

                # Estimate duration from history length (assuming ~15 FPS)
                est_duration = max(0.0, float(worker.history_length) / 15.0)

                ev = NormalizedSafetyEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=ev_type,
                    timestamp=now_iso,
                    camera_id=camera_id,
                    zone_id=zone_id,
                    track_id=track_id,
                    confidence=obs.confidence or worker.confidence,
                    duration_seconds=est_duration,
                    details={
                        "item_type": obs.item_type.value,
                        "consecutive_missed": obs.consecutive_missed,
                        "worker_bbox": [worker.bbox.x1, worker.bbox.y1, worker.bbox.x2, worker.bbox.y2],
                    },
                    source="compliance",
                )
                events.append(ev)

        return events

    @staticmethod
    def from_hazard_response(
        response: HazardAnalysisResponse,
    ) -> List[NormalizedSafetyEvent]:
        """
        Extracts confirmed environmental hazards from Phase 6.
        STRICT RULE: Only CONFIRMED hazards generate active events.
        SUSPECTED or CLEARED do not trigger active confirmed hazard events.
        """
        events: List[NormalizedSafetyEvent] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        confirmed_hazards = [h for h in response.hazards if h.state == HazardState.CONFIRMED]

        # Multi-hazard check
        has_fire = any(h.hazard_type == HazardType.FIRE for h in confirmed_hazards)
        has_smoke = any(h.hazard_type == HazardType.SMOKE for h in confirmed_hazards)

        if has_fire and has_smoke:
            # Generate multi-hazard umbrella event
            ev_multi = NormalizedSafetyEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.MULTIPLE_HAZARDS,
                timestamp=now_iso,
                camera_id=response.camera_id,
                zone_id=response.zone_id,
                confidence=max((h.confidence for h in confirmed_hazards), default=0.8),
                duration_seconds=max((h.duration_seconds for h in confirmed_hazards), default=0.0),
                details={"hazards_count": len(confirmed_hazards), "types": ["fire", "smoke"]},
                source="hazard",
            )
            events.append(ev_multi)

        # Generate individual hazard events
        for h in confirmed_hazards:
            ev_type = EventType.FIRE_DETECTED if h.hazard_type == HazardType.FIRE else EventType.SMOKE_DETECTED
            ev = NormalizedSafetyEvent(
                event_id=str(uuid.uuid4()),
                event_type=ev_type,
                timestamp=now_iso,
                camera_id=h.camera_id,
                zone_id=h.zone_id,
                hazard_event_id=h.event_id,
                confidence=h.confidence,
                duration_seconds=h.duration_seconds,
                details={
                    "event_id": h.event_id,
                    "hazard_type": h.hazard_type.value,
                    "persistence_ratio": h.persistence_ratio,
                    "bbox": [h.bbox.x1, h.bbox.y1, h.bbox.x2, h.bbox.y2],
                },
                source="hazard",
            )
            events.append(ev)

        return events
