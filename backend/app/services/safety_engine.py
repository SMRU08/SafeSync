"""
safety_engine.py — SafeSync Safety Intelligence Pipeline
Centralized Safety Engine orchestrating decoupled PPE, Hazard, and System Health observations.

Enforces 7 Core Safety Rules:
- Rule 1 (Confirmed Fire): Escalates immediately to CRITICAL (P0 Emergency, Audible Siren).
- Rule 2 (Confirmed Smoke): Escalates to HIGH/CRITICAL (P0/P1 Hazard, Audible Siren).
- Rule 3 (Multi-Hazard Escalation): Escalates to highest emergency tier on dual/multi-hazards.
- Rule 4 (Confirmed PPE Violation): Generates visual SAFETY_VIOLATION (P2, Visual Alert only, NO siren).
- Rule 5 (Unknown PPE State): Strictly NO violation generated for UNKNOWN state (UNKNOWN != ABSENT).
- Rule 6 (Camera Offline): Dispatches SYSTEM_WARNING (P3 Advisory).
- Rule 7 (AI Engine Unavailable): Dispatches SYSTEM_WARNING (P3 Advisory).
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

try:
    from app.ai.risk.schemas import (
        EventType,
        RiskLevel,
        AlarmPriority,
        NormalizedSafetyEvent,
        RiskScoreBreakdown,
        AlertSchema,
        IncidentSchema,
    )
    from app.ai.compliance.schemas import (
        ComplianceAnalysisResponse,
        WorkerTrack,
        PPEState,
        PPEItemType,
    )
    from app.ai.hazards.schemas import (
        HazardAnalysisResponse,
        HazardEventDetail,
        HazardState,
        HazardType,
    )
    from app.services.risk_engine import RiskEngine
    from app.services.alert_engine import AlertEngine
    from app.services.event_normalizer import EventNormalizer
    from app.services.event_broadcaster import broadcaster
    from app.ai.compliance.ppe_policy import ZonePPEPolicyEngine
except ImportError:
    from backend.app.ai.risk.schemas import (
        EventType,
        RiskLevel,
        AlarmPriority,
        NormalizedSafetyEvent,
        RiskScoreBreakdown,
        AlertSchema,
        IncidentSchema,
    )
    from backend.app.ai.compliance.schemas import (
        ComplianceAnalysisResponse,
        WorkerTrack,
        PPEState,
        PPEItemType,
    )
    from backend.app.ai.hazards.schemas import (
        HazardAnalysisResponse,
        HazardEventDetail,
        HazardState,
        HazardType,
    )
    from backend.app.services.risk_engine import RiskEngine
    from backend.app.services.alert_engine import AlertEngine
    from backend.app.services.event_normalizer import EventNormalizer
    from backend.app.services.event_broadcaster import broadcaster
    from backend.app.ai.compliance.ppe_policy import ZonePPEPolicyEngine

logger = logging.getLogger("safety_engine")


@dataclass
class SafetyAssessment:
    """Consolidated safety assessment across a camera frame or site zone."""
    camera_id: str
    zone_id: str
    overall_risk_score: int
    overall_risk_level: RiskLevel
    highest_priority: Optional[AlarmPriority]
    active_violations_count: int
    active_hazards_count: int
    workers_count: int
    requires_audible_siren: bool
    events: List[NormalizedSafetyEvent] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SafetyEngine:
    """
    Central Safety Intelligence Engine for SafeSync.
    Combines verified worker PPE compliance and fire/smoke hazards into actionable safety evaluations.
    """

    def __init__(
        self,
        risk_engine: Optional[RiskEngine] = None,
        alert_engine: Optional[AlertEngine] = None,
    ):
        self.risk_engine = risk_engine or RiskEngine()
        self.alert_engine = alert_engine or AlertEngine(risk_engine=self.risk_engine)
        self.normalizer = EventNormalizer()

    # =========================================================================
    # RULE ENFORCEMENT METHODS
    # =========================================================================

    def enforce_rule_1_fire(self, hazard: HazardEventDetail) -> Optional[NormalizedSafetyEvent]:
        """
        Rule 1: Confirmed Fire -> CRITICAL (P0 Emergency, Audible Siren).
        """
        if hazard.hazard_type == HazardType.FIRE and hazard.state == HazardState.CONFIRMED:
            return NormalizedSafetyEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.FIRE_DETECTED,
                timestamp=datetime.now(timezone.utc).isoformat(),
                camera_id=hazard.camera_id,
                zone_id=hazard.zone_id,
                hazard_event_id=hazard.event_id,
                confidence=hazard.confidence,
                duration_seconds=hazard.duration_seconds,
                details={
                    "hazard_type": "fire",
                    "state": hazard.state.value if hasattr(hazard.state, "value") else str(hazard.state),
                    "rule": "RULE_1_FIRE",
                    "priority": AlarmPriority.P0.value,
                    "audible": True,
                },
                source="safety_engine_rule_1",
            )
        return None

    def enforce_rule_2_smoke(self, hazard: HazardEventDetail) -> Optional[NormalizedSafetyEvent]:
        """
        Rule 2: Confirmed Smoke -> HIGH / CRITICAL (P0/P1 Hazard, Audible Siren).
        """
        if hazard.hazard_type == HazardType.SMOKE and hazard.state == HazardState.CONFIRMED:
            # Escalate persistent smoke (> 10s) to P0, otherwise P1
            priority = AlarmPriority.P0 if hazard.duration_seconds >= 10.0 else AlarmPriority.P1
            return NormalizedSafetyEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.SMOKE_DETECTED,
                timestamp=datetime.now(timezone.utc).isoformat(),
                camera_id=hazard.camera_id,
                zone_id=hazard.zone_id,
                hazard_event_id=hazard.event_id,
                confidence=hazard.confidence,
                duration_seconds=hazard.duration_seconds,
                details={
                    "hazard_type": "smoke",
                    "state": hazard.state.value if hasattr(hazard.state, "value") else str(hazard.state),
                    "rule": "RULE_2_SMOKE",
                    "priority": priority.value,
                    "audible": True,
                },
                source="safety_engine_rule_2",
            )
        return None

    def enforce_rule_3_multi_hazard(
        self,
        hazards: List[HazardEventDetail],
        camera_id: str,
        zone_id: str,
    ) -> Optional[NormalizedSafetyEvent]:
        """
        Rule 3: Multi-Hazard Escalation -> Dual fire/smoke or multiple concurrent hazards escalate to P0 CRITICAL.
        """
        active_hazards = [
            h for h in hazards
            if h.state == HazardState.CONFIRMED
        ]
        has_fire = any(h.hazard_type == HazardType.FIRE for h in active_hazards)
        has_smoke = any(h.hazard_type == HazardType.SMOKE for h in active_hazards)

        if (has_fire and has_smoke) or len(active_hazards) >= 2:
            max_duration = max((h.duration_seconds for h in active_hazards), default=0.0)
            max_conf = max((h.confidence for h in active_hazards), default=0.9)
            return NormalizedSafetyEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.MULTIPLE_HAZARDS,
                timestamp=datetime.now(timezone.utc).isoformat(),
                camera_id=camera_id,
                zone_id=zone_id,
                confidence=max_conf,
                duration_seconds=max_duration,
                details={
                    "rule": "RULE_3_MULTI_HAZARD",
                    "priority": AlarmPriority.P0.value,
                    "audible": True,
                    "active_hazards_count": len(active_hazards),
                    "types": list(set(h.hazard_type.value for h in active_hazards)),
                },
                source="safety_engine_rule_3",
            )
        return None

    def enforce_rule_4_and_5_ppe(
        self,
        workers: List[WorkerTrack],
        camera_id: str,
        zone_id: str,
    ) -> List[NormalizedSafetyEvent]:
        """
        Rule 4: Confirmed PPE Violation → SAFETY_VIOLATION (P2, Visual Dashboard Alert, NO Audible Siren).
        Rule 5: Unknown PPE State → Strictly NO violation generated for UNKNOWN state (UNKNOWN != ABSENT).

        Zone-aware: Only PPE items that are REQUIRED in the worker's zone generate violations.
        Optional PPE (e.g., gloves in storage_area) are monitored but do NOT generate violations.
        Disabled PPE items are silently ignored.
        """
        events: List[NormalizedSafetyEvent] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # Resolve zone-specific PPE policy (PS06: "gloves where applicable")
        try:
            zone_policy = ZonePPEPolicyEngine.get_instance().get_policy_for_zone(zone_id)
        except Exception:
            zone_policy = None

        for worker in workers:
            for item_name, obs in worker.ppe_details.items():
                # Rule 5: UNKNOWN state NEVER generates a violation
                if obs.state == PPEState.UNKNOWN:
                    logger.debug("Rule 5: Worker %s item %s is UNKNOWN → No violation.", worker.track_id, item_name)
                    continue

                # Present state never generates a violation
                if obs.state == PPEState.PRESENT:
                    continue

                # Rule 4: Confirmed ABSENT state — check zone policy before generating violation
                if obs.state == PPEState.ABSENT:
                    # Zone-aware policy check (PS06 §7: "gloves where applicable")
                    if zone_policy is not None and not zone_policy.is_required(item_name):
                        logger.debug(
                            "Rule 4 Zone-Policy: Worker %s item %s is ABSENT in zone '%s' "
                            "but policy=%s → No violation generated.",
                            worker.track_id, item_name, zone_id, zone_policy.get_policy(item_name)
                        )
                        continue  # Optional or disabled PPE: no violation

                    ev_type = EventType.PPE_VIOLATION
                    if obs.item_type == PPEItemType.HELMET:
                        ev_type = EventType.MISSING_HELMET
                    elif obs.item_type == PPEItemType.SAFETY_VEST:
                        ev_type = EventType.MISSING_SAFETY_VEST
                    elif obs.item_type == PPEItemType.GLOVES:
                        ev_type = EventType.MISSING_GLOVES
                    elif obs.item_type == PPEItemType.SAFETY_FOOTWEAR:
                        ev_type = EventType.MISSING_SAFETY_FOOTWEAR

                    est_duration = max(0.0, float(worker.history_length) / 15.0)

                    ev = NormalizedSafetyEvent(
                        event_id=str(uuid.uuid4()),
                        event_type=ev_type,
                        timestamp=now_iso,
                        camera_id=camera_id,
                        zone_id=zone_id,
                        track_id=worker.track_id,
                        confidence=obs.confidence or worker.confidence,
                        duration_seconds=est_duration,
                        details={
                            "item_type": obs.item_type.value,
                            "rule": "RULE_4_PPE_VIOLATION",
                            "priority": AlarmPriority.P2.value,
                            "audible": False,  # Visual alert only, avoiding siren fatigue
                            "consecutive_missed": obs.consecutive_missed,
                            "worker_bbox": [worker.bbox.x1, worker.bbox.y1, worker.bbox.x2, worker.bbox.y2],
                            "zone_policy": zone_policy.get_policy(item_name) if zone_policy else "required",
                        },
                        source="safety_engine_rule_4",
                    )
                    events.append(ev)

        return events


    def enforce_rule_6_camera_offline(
        self,
        camera_id: str,
        zone_id: str,
        is_connected: bool,
    ) -> Optional[NormalizedSafetyEvent]:
        """
        Rule 6: Camera Offline -> SYSTEM_WARNING (P3 Advisory, NO Audible Siren).
        """
        if not is_connected:
            return NormalizedSafetyEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.CAMERA_FAILURE,
                timestamp=datetime.now(timezone.utc).isoformat(),
                camera_id=camera_id,
                zone_id=zone_id,
                confidence=1.0,
                duration_seconds=0.0,
                details={
                    "rule": "RULE_6_CAMERA_OFFLINE",
                    "priority": AlarmPriority.P3.value,
                    "audible": False,
                    "message": f"Camera {camera_id} capture stream is disconnected.",
                },
                source="safety_engine_rule_6",
            )
        return None

    def enforce_rule_7_ai_unavailable(
        self,
        camera_id: str,
        zone_id: str,
        ai_available: bool,
    ) -> Optional[NormalizedSafetyEvent]:
        """
        Rule 7: AI Engine Unavailable -> SYSTEM_WARNING (P3 Advisory, NO Audible Siren).
        """
        if not ai_available:
            return NormalizedSafetyEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.SYSTEM_FAILURE,
                timestamp=datetime.now(timezone.utc).isoformat(),
                camera_id=camera_id,
                zone_id=zone_id,
                confidence=1.0,
                duration_seconds=0.0,
                details={
                    "rule": "RULE_7_AI_UNAVAILABLE",
                    "priority": AlarmPriority.P3.value,
                    "audible": False,
                    "message": "AI Inference engine is offline or encountering unrecoverable errors.",
                },
                source="safety_engine_rule_7",
            )
        return None

    # =========================================================================
    # MASTER SCENE ASSESSMENT
    # =========================================================================

    def assess_scene(
        self,
        camera_id: str,
        zone_id: str = "UNKNOWN",
        compliance_response: Optional[ComplianceAnalysisResponse] = None,
        hazard_response: Optional[HazardAnalysisResponse] = None,
        camera_connected: bool = True,
        ai_available: bool = True,
    ) -> SafetyAssessment:
        """
        Orchestrates all safety rules across PPE, hazard, and connectivity inputs.
        Returns a consolidated SafetyAssessment.
        """
        events: List[NormalizedSafetyEvent] = []

        # 1. System Health Checks (Rules 6 & 7)
        cam_err = self.enforce_rule_6_camera_offline(camera_id, zone_id, camera_connected)
        if cam_err:
            events.append(cam_err)

        ai_err = self.enforce_rule_7_ai_unavailable(camera_id, zone_id, ai_available)
        if ai_err:
            events.append(ai_err)

        # 2. PPE Compliance Evaluation (Rules 4 & 5)
        workers_count = 0
        active_violations_count = 0
        if compliance_response and ai_available and camera_connected:
            workers_count = len(compliance_response.workers)
            ppe_events = self.enforce_rule_4_and_5_ppe(
                compliance_response.workers,
                camera_id=camera_id,
                zone_id=zone_id,
            )
            events.extend(ppe_events)
            active_violations_count = len(ppe_events)

        # 3. Hazard Evaluation (Rules 1, 2 & 3)
        active_hazards_count = 0
        if hazard_response and ai_available and camera_connected:
            hazards_list = hazard_response.hazards or []
            # Multi-hazard check (Rule 3)
            multi_ev = self.enforce_rule_3_multi_hazard(hazards_list, camera_id, zone_id)
            if multi_ev:
                events.append(multi_ev)

            for h in hazards_list:
                # Rule 1: Fire
                f_ev = self.enforce_rule_1_fire(h)
                if f_ev:
                    events.append(f_ev)
                    active_hazards_count += 1

                # Rule 2: Smoke
                s_ev = self.enforce_rule_2_smoke(h)
                if s_ev:
                    events.append(s_ev)
                    active_hazards_count += 1

        # 4. Synthesize Priorities & Aggregate Risk Score
        highest_priority = None
        requires_audible = False
        max_risk_score = 0
        max_risk_level = RiskLevel.LOW

        priority_order = {
            AlarmPriority.P0: 4,
            AlarmPriority.P1: 3,
            AlarmPriority.P2: 2,
            AlarmPriority.P3: 1,
        }

        for ev in events:
            # Score each event with RiskEngine
            r = self.risk_engine.evaluate(
                event_type=ev.event_type,
                duration_seconds=ev.duration_seconds,
                affected_workers_count=1 if ev.track_id is not None else 0,
                zone_id=zone_id,
                is_multi_hazard=(ev.event_type == EventType.MULTIPLE_HAZARDS),
            )
            if r.risk_score > max_risk_score:
                max_risk_score = r.risk_score
                max_risk_level = r.risk_level

            # Determine priority
            p_val = ev.details.get("priority")
            if p_val:
                try:
                    p_enum = AlarmPriority(p_val)
                    if highest_priority is None or priority_order[p_enum] > priority_order[highest_priority]:
                        highest_priority = p_enum
                except Exception:
                    pass

            if ev.details.get("audible", False):
                requires_audible = True

        return SafetyAssessment(
            camera_id=camera_id,
            zone_id=zone_id,
            overall_risk_score=max_risk_score,
            overall_risk_level=max_risk_level,
            highest_priority=highest_priority,
            active_violations_count=active_violations_count,
            active_hazards_count=active_hazards_count,
            workers_count=workers_count,
            requires_audible_siren=requires_audible,
            events=events,
        )
