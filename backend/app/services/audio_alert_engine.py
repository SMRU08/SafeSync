"""
audio_alert_engine.py — RAKSHYA VISION Core AI Vision & Audio-Alert Engine
Real-time PPE compliance audio alert generation with camera-isolated speaker toggles,
personalized worker grammar formatting, and event broadcasting.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, Tuple
from pydantic import BaseModel, Field

try:
    from app.services.event_broadcaster import broadcaster
    from app.services.metrics import MetricsCollector
except ImportError:
    from backend.app.services.event_broadcaster import broadcaster
    try:
        from backend.app.services.metrics import MetricsCollector
    except ImportError:
        MetricsCollector = None

logger = logging.getLogger("audio_alert_engine")


class AudioAlertPayload(BaseModel):
    camera_id: str
    worker_id: Union[int, str]
    missing_ppe: List[str]
    present_ppe: List[str]
    speaker_enabled: bool
    action: str  # "AUDIO_TRIGGERED" | "AUDIO_SUPPRESSED" | "COMPLIANT"
    message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, Any] = Field(default_factory=dict)


def format_missing_ppe_list(missing_items: List[str]) -> str:
    """
    Formats the list of missing PPE items with natural English grammar and Oxford comma.
    Strictly follows required specifications:
      - 'helmet' -> 'a helmet'
      - 'safety_vest' / 'vest' -> 'safety vest'
      - 'gloves' -> 'gloves'
      - 'safety_footwear' / 'safety_shoes' / 'shoes' -> 'safety shoes'

    Examples:
      ['helmet', 'safety_vest', 'gloves'] -> 'a helmet, safety vest, and gloves'
      ['gloves'] -> 'gloves'
      ['safety_footwear'] -> 'safety shoes'
    """
    labels = []
    for item in missing_items:
        key = str(item).lower().strip()
        if "helmet" in key:
            labels.append("a helmet")
        elif "vest" in key:
            labels.append("safety vest")
        elif "glove" in key:
            labels.append("gloves")
        elif "footwear" in key or "shoe" in key:
            labels.append("safety shoes")
        else:
            labels.append(key.replace("_", " "))

    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"


def format_audio_alert_message(worker_id: Union[int, str], missing_items: List[str]) -> str:
    """
    Produces standard alert phrasing:
    "Worker [ID Number], you are not wearing [List only the missing PPE items]."
    """
    missing_str = format_missing_ppe_list(missing_items)
    return f"Worker {worker_id}, you are not wearing {missing_str}."


class AudioAlertEngine:
    """
    Singleton AI Vision and Audio-Alert Engine for multi-camera safety compliance.
    Evaluates worker compliance in real-time and dynamically triggers or suppresses
    personalized voice alerts based on camera-specific Speaker Status (ON / OFF).
    """

    _instance: Optional["AudioAlertEngine"] = None

    def __init__(self, default_cooldown_seconds: float = 10.0):
        self.default_cooldown_seconds = default_cooldown_seconds
        # Cooldown tracking: (camera_id, worker_id) -> last_alert_time
        self._last_alert_timestamps: Dict[Tuple[str, str], float] = {}
        self._alert_history: List[AudioAlertPayload] = []
        self._max_history = 100

    @classmethod
    def get_instance(cls, default_cooldown_seconds: float = 10.0) -> "AudioAlertEngine":
        if cls._instance is None:
            cls._instance = AudioAlertEngine(default_cooldown_seconds)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Resets singleton state (used in automated testing)."""
        cls._instance = None

    def clear_cooldowns(self):
        """Clears all debounce timestamps."""
        self._last_alert_timestamps.clear()

    def evaluate_worker(
        self,
        camera_id: str,
        speaker_enabled: bool,
        worker_id: Union[int, str],
        ppe_status: Dict[str, Any],
        cooldown_seconds: Optional[float] = None,
        force: bool = False,
    ) -> AudioAlertPayload:
        """
        Evaluates a single worker's PPE compliance and generates or suppresses an audio alert.

        Rules:
        - If 100% compliant: No alert required. Action: "COMPLIANT".
        - If missing PPE:
            - If Camera Speaker is OFF: Suppress audio alert. Action: "AUDIO_SUPPRESSED".
            - If Camera Speaker is ON: Trigger localized voice alert. Action: "AUDIO_TRIGGERED".
        """
        missing_items: List[str] = []
        present_items: List[str] = []

        standard_keys = [
            ("helmet", ["helmet", "hard_hat"]),
            ("safety_vest", ["safety_vest", "vest"]),
            ("gloves", ["gloves", "glove"]),
            ("safety_footwear", ["safety_footwear", "safety_shoes", "shoes", "boots"]),
        ]

        for std_key, aliases in standard_keys:
            raw_state = None
            for alias in aliases:
                if alias in ppe_status:
                    raw_state = ppe_status[alias]
                    break

            if raw_state is None:
                continue

            state_str = str(getattr(raw_state, "value", raw_state)).upper()
            if state_str in ("ABSENT", "NON_COMPLIANT", "MISSING", "FALSE"):
                missing_items.append(std_key)
            elif state_str in ("PRESENT", "COMPLIANT", "TRUE"):
                present_items.append(std_key)

        now = time.time()
        cd = self.default_cooldown_seconds if cooldown_seconds is None else cooldown_seconds
        w_key = (str(camera_id), str(worker_id))

        # Scenario D: Worker is 100% compliant
        if not missing_items:
            payload = AudioAlertPayload(
                camera_id=camera_id,
                worker_id=worker_id,
                missing_ppe=[],
                present_ppe=present_items,
                speaker_enabled=speaker_enabled,
                action="COMPLIANT",
                message=None,
                details={"compliant": True},
            )
            return payload

        # Missing equipment detected: Format exact targeted message
        alert_message = format_audio_alert_message(worker_id, missing_items)

        # Check speaker status
        if not speaker_enabled:
            # Scenario C: Speaker is OFF -> Suppress audio alert
            logger.info(
                "[AUDIO SUPPRESSED] Camera '%s' speaker is OFF. Worker #%s missing: %s. Message: '%s'",
                camera_id,
                worker_id,
                missing_items,
                alert_message,
            )
            payload = AudioAlertPayload(
                camera_id=camera_id,
                worker_id=worker_id,
                missing_ppe=missing_items,
                present_ppe=present_items,
                speaker_enabled=False,
                action="AUDIO_SUPPRESSED",
                message=alert_message,
                details={"reason": "camera_speaker_disabled", "audio_played": False},
            )
            self._record_history(payload)
            return payload

        # Speaker is ON: Check cooldown to prevent audio chatter/stutter
        last_alert_time = self._last_alert_timestamps.get(w_key, 0.0)
        time_since_last = now - last_alert_time

        if not force and time_since_last < cd:
            # Within debounce cooldown: keep audio quiet while worker rectifies gear
            payload = AudioAlertPayload(
                camera_id=camera_id,
                worker_id=worker_id,
                missing_ppe=missing_items,
                present_ppe=present_items,
                speaker_enabled=True,
                action="COOLDOWN",
                message=alert_message,
                details={
                    "reason": "debounce_cooldown",
                    "cooldown_remaining": round(cd - time_since_last, 1),
                    "audio_played": False,
                },
            )
            return payload

        # Update last alert timestamp
        self._last_alert_timestamps[w_key] = now

        # Scenario A & B: Speaker is ON -> Trigger voice alert
        logger.info(
            "[AUDIO TRIGGERED] Camera '%s' speaker is ON. Voice Alert: '%s'",
            camera_id,
            alert_message,
        )

        payload = AudioAlertPayload(
            camera_id=camera_id,
            worker_id=worker_id,
            missing_ppe=missing_items,
            present_ppe=present_items,
            speaker_enabled=True,
            action="AUDIO_TRIGGERED",
            message=alert_message,
            details={"audio_played": True},
        )

        # Broadcast WebSocket event to all connected dashboard instances and speakers
        try:
            broadcaster.broadcast("AudioAlert", payload.model_dump())
        except Exception as b_err:
            logger.warning("Failed to broadcast AudioAlert: %s", b_err)

        if MetricsCollector:
            try:
                MetricsCollector.get_instance().increment_counter(
                    "rakshya_audio_alerts_total",
                    labels={"camera_id": camera_id, "action": "TRIGGERED"},
                )
            except Exception:
                pass

        self._record_history(payload)
        return payload

    def evaluate_frame_workers(
        self,
        camera_id: str,
        speaker_enabled: bool,
        workers: List[Any],
    ) -> List[AudioAlertPayload]:
        """
        Evaluates all workers detected in a specific camera frame independently.
        Ensures multi-camera isolation: Camera 1 only references workers visible in Camera 1.
        """
        results = []
        for w in workers:
            try:
                wid = getattr(w, "track_id", None)
                if wid is None and isinstance(w, dict):
                    wid = w.get("track_id", "unknown")

                # Extract ppe_status
                ppe_stat = None
                if hasattr(w, "ppe_status"):
                    ppe_stat = getattr(w, "ppe_status")
                elif hasattr(w, "ppe"):
                    ppe_stat = getattr(w, "ppe")
                elif isinstance(w, dict):
                    ppe_stat = w.get("ppe_status") or w.get("ppe") or {}

                if not isinstance(ppe_stat, dict):
                    ppe_stat = {}

                payload = self.evaluate_worker(
                    camera_id=camera_id,
                    speaker_enabled=speaker_enabled,
                    worker_id=wid,
                    ppe_status=ppe_stat,
                )
                results.append(payload)
            except Exception as e:
                logger.error("Error evaluating worker for audio alert: %s", e)

        return results

    def _record_history(self, payload: AudioAlertPayload):
        """Appends alert payload to in-memory audit ring buffer."""
        self._alert_history.append(payload)
        if len(self._alert_history) > self._max_history:
            self._alert_history.pop(0)

    def get_recent_alerts(self, limit: int = 50, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns recent audio alert events for auditing and visual inspection."""
        items = list(self._alert_history)
        if camera_id:
            items = [a for a in items if a.camera_id == camera_id]
        return [a.model_dump() for a in items[-limit:]]
