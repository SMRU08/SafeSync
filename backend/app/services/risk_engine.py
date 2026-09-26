"""
risk_engine.py — SafeSync Phase 7
Safety Risk Analysis Engine.
Computes explainable, deterministic numerical risk scores (0-100) and maps them to
categorical risk levels (LOW, MEDIUM, HIGH, CRITICAL) using configurable policy rules.
Strictly decoupled from model confidence.
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional

try:
    from app.ai.risk.schemas import EventType, RiskLevel, RiskScoreBreakdown, NormalizedSafetyEvent
except ImportError:
    from backend.app.ai.risk.schemas import EventType, RiskLevel, RiskScoreBreakdown, NormalizedSafetyEvent

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_RISK_POLICY = os.path.join(ROOT, "configs", "risk_policy.yaml")
log = logging.getLogger(__name__)


def load_risk_policy(policy_path: Optional[str] = None) -> Dict[str, Any]:
    path = policy_path or DEFAULT_RISK_POLICY
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    log.warning("Risk policy file not found at %s. Using default fallback.", path)
    return {}


class RiskEngine:
    """
    Evaluates safety risk deterministically with full factor explainability.
    """

    def __init__(self, policy_path: Optional[str] = None):
        self.policy_path = policy_path or DEFAULT_RISK_POLICY
        self.policy = load_risk_policy(self.policy_path)
        self._load_parameters()

    def _load_parameters(self):
        # Event severities
        ev_cfg = self.policy.get("events", {})
        self.base_severities: Dict[EventType, float] = {
            EventType.MISSING_HELMET: float(ev_cfg.get("missing_helmet", {}).get("base_severity", 50)),
            EventType.MISSING_SAFETY_VEST: float(ev_cfg.get("missing_safety_vest", {}).get("base_severity", 45)),
            EventType.MISSING_GLOVES: float(ev_cfg.get("missing_gloves", {}).get("base_severity", 25)),
            EventType.MISSING_SAFETY_FOOTWEAR: float(ev_cfg.get("missing_safety_footwear", {}).get("base_severity", 25)),
            EventType.SMOKE_DETECTED: float(ev_cfg.get("smoke", {}).get("base_severity", 60)),
            EventType.FIRE_DETECTED: float(ev_cfg.get("fire", {}).get("base_severity", 85)),
            EventType.PPE_VIOLATION: float(ev_cfg.get("missing_helmet", {}).get("base_severity", 50)),
            EventType.MULTIPLE_HAZARDS: 70.0,
            EventType.CAMERA_FAILURE: float(ev_cfg.get("camera_failure", {}).get("base_severity", 40)),
            EventType.SYSTEM_FAILURE: float(ev_cfg.get("system_failure", {}).get("base_severity", 45)),
        }
        self.multi_hazard_bonus = float(ev_cfg.get("multiple_hazards_bonus", 20))

        # Zone multipliers
        self.zone_multipliers = self.policy.get("zone_multipliers", {
            "electrical_room": 1.30,
            "production_floor": 1.15,
            "storage_area": 1.00,
            "loading_dock": 1.10,
            "UNKNOWN": 1.00,
        })

        # Scoring weights
        weights = self.policy.get("scoring_weights", {})
        self.points_per_persistence_sec = float(weights.get("persistence_points_per_second", 1.0))
        self.max_persistence_points = float(weights.get("max_persistence_points", 25.0))
        self.points_per_worker = float(weights.get("points_per_affected_worker", 5.0))
        self.max_worker_points = float(weights.get("max_worker_points", 20.0))
        self.points_per_repetition = float(weights.get("repetition_points_per_event", 4.0))
        self.max_repetition_points = float(weights.get("max_repetition_points", 15.0))

        # Thresholds
        levels = self.policy.get("risk_levels", {})
        self.low_max = int(levels.get("LOW", {}).get("score_max", 29))
        self.med_max = int(levels.get("MEDIUM", {}).get("score_max", 59))
        self.high_max = int(levels.get("HIGH", {}).get("score_max", 84))

    def evaluate(
        self,
        event_type: EventType,
        duration_seconds: float = 0.0,
        affected_workers_count: int = 1,
        repetition_count: int = 0,
        zone_id: str = "UNKNOWN",
        is_multi_hazard: bool = False,
    ) -> RiskScoreBreakdown:
        """
        Calculates an explainable risk score and categorical level.
        """
        # 1. Base event severity
        base_sev = self.base_severities.get(event_type, 30.0)

        # 2. Persistence factor
        persistence_pts = min(
            self.max_persistence_points,
            max(0.0, float(duration_seconds) * self.points_per_persistence_sec)
        )

        # 3. Affected worker factor (beyond 1st worker)
        extra_workers = max(0, affected_workers_count - 1)
        worker_pts = min(
            self.max_worker_points,
            float(extra_workers) * self.points_per_worker
        )

        # 4. Repetition factor
        repetition_pts = min(
            self.max_repetition_points,
            max(0.0, float(repetition_count) * self.points_per_repetition)
        )

        # 5. Multi-hazard factor
        multi_hazard_pts = self.multi_hazard_bonus if is_multi_hazard else 0.0

        # 6. Zone multiplier
        zone_mult = float(self.zone_multipliers.get(zone_id, 1.00))

        # Combine
        subtotal = base_sev + persistence_pts + worker_pts + repetition_pts + multi_hazard_pts
        raw_score = subtotal * zone_mult
        final_score = int(min(100, max(0, round(raw_score))))

        # Map to category
        if final_score <= self.low_max:
            level = RiskLevel.LOW
        elif final_score <= self.med_max:
            level = RiskLevel.MEDIUM
        elif final_score <= self.high_max:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL

        factors = {
            "base_severity": round(base_sev, 2),
            "persistence_factor": round(persistence_pts, 2),
            "affected_workers_factor": round(worker_pts, 2),
            "repetition_factor": round(repetition_pts, 2),
            "multi_hazard_factor": round(multi_hazard_pts, 2),
            "zone_multiplier": round(zone_mult, 2),
        }

        return RiskScoreBreakdown(
            risk_score=final_score,
            risk_level=level,
            factors=factors,
        )
