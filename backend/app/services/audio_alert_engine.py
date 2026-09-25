"""
audio_alert_engine.py — RAKSHYA VISION Core AI Vision & Audio-Alert Engine
Real-time PPE compliance audio alert generation with camera-isolated speaker toggles,
personalized worker grammar formatting, and event broadcasting.
"""

import re
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
    camera_name: Optional[str] = None
    worker_id: Optional[Union[int, str]] = None
    missing_ppe: List[str] = Field(default_factory=list)
    present_ppe: List[str] = Field(default_factory=list)
    speaker_enabled: bool
    bypass_speaker: bool = False
    action: str  # "AUDIO_TRIGGERED" | "AUDIO_SUPPRESSED" | "COMPLIANT" | "CRITICAL_HAZARD_TRIGGERED" | "COOLDOWN"
    message: Optional[str] = None
    hindi_message: Optional[str] = None
    english_message: Optional[str] = None
    hazard_type: Optional[str] = None  # "fire" | "smoke" | "fire_and_smoke"
    priority: str = "NORMAL"  # "CRITICAL" | "HIGH" | "NORMAL"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, Any] = Field(default_factory=dict)


# ─── Hindi Translation & Formatting Maps ─────────────────────────────────────

HINDI_DIGITS_MAP: Dict[int, str] = {
    1: "एक", 2: "दो", 3: "तीन", 4: "चार", 5: "पांच",
    6: "छह", 7: "सात", 8: "आठ", 9: "नौ", 10: "दस",
    11: "ग्यारह", 12: "बारह", 13: "तेरह", 14: "चौदह", 15: "पंद्रह",
    16: "सोलह", 17: "सत्रह", 18: "अठारह", 19: "उन्नीस", 20: "बीस",
    21: "इक्कीस", 22: "बाईस", 23: "तेईस", 24: "चौबीस", 25: "पच्चीस",
    26: "छब्बीस", 27: "सत्ताईस", 28: "अट्ठाइस", 29: "उनतीस", 30: "तीस",
    31: "इकत्तीस", 32: "बत्तीस", 33: "तैंतीस", 34: "चौंतीस", 35: "पैंतीस",
    36: "छत्तीस", 37: "सैंतीस", 38: "अड़तीस", 39: "उनतालीस", 40: "चालीस",
    41: "इकतालीस", 42: "बयालीस", 43: "तैंतालीस", 44: "चवालीस", 45: "पैंतालीस",
    46: "छियालीस", 47: "सैंतालीस", 48: "अड़तालीस", 49: "उनचास", 50: "पचास",
    51: "इक्यावन", 52: "बावन", 53: "तिरपन", 54: "चौवन", 55: "पचपन",
    56: "छप्पन", 57: "सत्तावन", 58: "अट्ठावन", 59: "उनसठ", 60: "साठ",
    61: "इकसठ", 62: "बासठ", 63: "तिरसठ", 64: "चौंसठ", 65: "पैंसठ",
    66: "छियासठ", 67: "सरसठ", 68: "अड़सठ", 69: "उनहत्तर", 70: "सत्तर",
    71: "इकहत्तर", 72: "बहत्तर", 73: "तिहत्तर", 74: "चौहत्तर", 75: "पचहत्तर",
    76: "छहत्तर", 77: "सतहत्तर", 78: "अठहत्तर", 79: "उनासी", 80: "अस्सी",
    81: "इक्यासी", 82: "बयासी", 83: "तिरासी", 84: "चौरासी", 85: "पचासी",
    86: "छियासी", 87: "सत्तासी", 88: "अठासी", 89: "नवासी", 90: "नब्बे",
    91: "इक्यानवे", 92: "बानवे", 93: "तिरानवे", 94: "चौरानवे", 95: "पंचानवे",
    96: "छियानवे", 97: "सत्तानवे", 98: "अट्ठानवे", 99: "निन्यानवे", 100: "सौ",
}

HINDI_WORD_TRANSLATIONS: Dict[str, str] = {
    "camera": "कैमरा",
    "cam": "कैमरा",
    "production": "प्रोडक्शन",
    "floor": "फ्लोर",
    "south": "साउथ",
    "north": "नॉर्थ",
    "east": "ईस्ट",
    "west": "वेस्ट",
    "storage": "स्टोरेज",
    "area": "एरिया",
    "loading": "लोडिंग",
    "dock": "डॉक",
    "electrical": "इलेक्ट्रिकल",
    "room": "रूम",
    "1": "वन",
    "01": "वन",
    "2": "टू",
    "02": "टू",
    "3": "थ्री",
    "03": "थ्री",
    "4": "फोर",
    "04": "फोर",
    "5": "फाइव",
    "05": "फाइव",
    "a": "ए",
    "b": "बी",
    "c": "सी",
    "d": "डी",
}


def format_hindi_camera_name(camera_name: Optional[str] = None, camera_id: Optional[str] = None) -> str:
    """
    Translates camera name/ID into natural spoken Hindi for speech synthesis.
    Examples:
      - "Camera 1" or "camera_01" -> "कैमरा वन"
      - "Camera A" -> "कैमरा ए"
      - "Camera A Production Floor South" -> "कैमरा ए प्रोडक्शन फ्लोर साउथ"
    """
    raw = str(camera_name or camera_id or "Camera 1").strip()
    raw = raw.replace("_", " ")
    words = raw.split()
    translated = []
    for w in words:
        clean = w.lower().strip()
        translated.append(HINDI_WORD_TRANSLATIONS.get(clean, w))
    return " ".join(translated)


def format_hindi_worker_id(worker_id: Union[int, str]) -> str:
    """Formats worker ID into Hindi voice string like 'बाईस (22)' or 'इक्कीस (21)'."""
    try:
        val = int(str(worker_id).strip().lstrip("#"))
        if val in HINDI_DIGITS_MAP:
            return f"{HINDI_DIGITS_MAP[val]} ({val})"
        return f"{val}"
    except (ValueError, TypeError):
        return str(worker_id)


def format_hindi_missing_ppe_list(missing_items: List[str]) -> str:
    """
    Translates and joins missing PPE items into Hindi with natural grammar:
      - 'helmet' -> 'हेलमेट'
      - 'safety_vest' / 'vest' -> 'सेफ्टी वेस्ट'
      - 'gloves' -> 'ग्लव्स'
      - 'safety_footwear' / 'safety_shoes' / 'shoes' -> 'सेफ्टी जूते'
    """
    labels = []
    for item in missing_items:
        key = str(item).lower().strip()
        if "helmet" in key:
            labels.append("हेलमेट")
        elif "vest" in key:
            labels.append("सेफ्टी वेस्ट")
        elif "glove" in key:
            labels.append("ग्लव्स")
        elif "footwear" in key or "shoe" in key:
            labels.append("सेफ्टी जूते")
        else:
            labels.append(key.replace("_", " "))

    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} और {labels[1]}"
    return ", ".join(labels[:-1]) + f" और {labels[-1]}"


def format_hindi_ppe_alert_message(
    camera_name: Optional[str],
    worker_id: Union[int, str],
    missing_items: List[str],
) -> str:
    """
    Hindi Voice Format:
    "{Full Camera Name}, वर्कर {Worker ID}, आपने {Missing PPE items translated to Hindi} नहीं पहना है।"
    Example A: "कैमरा वन, वर्कर बाईस (22), आपने सेफ्टी वेस्ट और ग्लव्स नहीं पहना है।"
    Example B: "कैमरा ए, वर्कर इक्कीस (21), आपने हेलमेट नहीं पहना है।"
    """
    cam_str = format_hindi_camera_name(camera_name)
    w_str = format_hindi_worker_id(worker_id)
    missing_str = format_hindi_missing_ppe_list(missing_items)
    return f"{cam_str}, वर्कर {w_str}, आपने {missing_str} नहीं पहना है।"


def format_hindi_hazard_alert_message(
    camera_name: Optional[str],
    has_fire: bool,
    has_smoke: bool,
) -> str:
    """
    Hindi Voice Format for Critical Hazards (Fire & Smoke):
    "{Full Camera Name} में {आग / धुएं} का पता चला है, तुरंत जांच करें!"
    Example (Smoke): "कैमरा ए प्रोडक्शन फ्लोर साउथ में धुएं का पता चला है, तुरंत जांच करें!"
    Example (Fire): "कैमरा वन में आग का पता चला है, तुरंत जांच करें!"
    """
    cam_str = format_hindi_camera_name(camera_name)
    if has_fire and has_smoke:
        hazard_word = "आग और धुएं"
    elif has_fire:
        hazard_word = "आग"
    else:
        hazard_word = "धुएं"
    return f"{cam_str} में {hazard_word} का पता चला है, तुरंत जांच करें!"


def format_short_worker_label(camera_id_or_name: Optional[str], worker_id: Union[int, str]) -> str:
    """
    Shortened Visual Bounding Box Label:
    Format: [Camera Initial]-[W][Worker_Number] (e.g. C1-W22 or CA-W21).
    Keeps visual UI distinct from detailed Hindi voice output.
    """
    raw = str(camera_id_or_name or "1").strip()
    m = re.search(r'(?i)camera[_\s]*([0-9a-zA-Z]+)', raw)
    if m:
        cid = m.group(1).lstrip("0") or "1"
        cam_tag = f"C{cid.upper()}"
    elif raw.isdigit():
        cam_tag = f"C{int(raw)}"
    elif len(raw) == 1 and raw.isalpha():
        cam_tag = f"C{raw.upper()}"
    else:
        c_char = "".join([c for c in raw if c.isalnum()])[:1].upper() or "1"
        cam_tag = f"C{c_char}"

    w_num = str(worker_id).strip().lstrip("#")
    return f"{cam_tag}-W{w_num}"


# ─── English Fallback Formatters (Backwards Compatibility) ───────────────────

def format_missing_ppe_list(missing_items: List[str]) -> str:
    """
    Formats the list of missing PPE items with natural English grammar and Oxford comma.
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
    """Produces standard English alert phrasing for backwards compatibility."""
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
        camera_name: Optional[str] = None,
        cooldown_seconds: Optional[float] = None,
        force: bool = False,
        lang: str = "hi",
    ) -> AudioAlertPayload:
        """
        Evaluates a single worker's PPE compliance and generates or suppresses an audio alert.

        Rules:
        - If 100% compliant: No alert required. Action: "COMPLIANT".
        - If missing PPE:
            - If Camera Speaker is OFF: Suppress audio alert. Action: "AUDIO_SUPPRESSED".
            - If Camera Speaker is ON: Trigger localized Hindi voice alert. Action: "AUDIO_TRIGGERED".
              Format: "{Full Camera Name}, वर्कर {Worker ID}, आपने {Missing PPE items in Hindi} नहीं पहना है।"
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
        resolved_cam_name = camera_name or camera_id

        # Scenario D: Worker is 100% compliant
        if not missing_items:
            payload = AudioAlertPayload(
                camera_id=camera_id,
                camera_name=resolved_cam_name,
                worker_id=worker_id,
                missing_ppe=[],
                present_ppe=present_items,
                speaker_enabled=speaker_enabled,
                bypass_speaker=False,
                action="COMPLIANT",
                message=None,
                hindi_message=None,
                english_message=None,
                details={"compliant": True},
            )
            return payload

        # Format both Hindi and English alert messages
        hindi_msg = format_hindi_ppe_alert_message(resolved_cam_name, worker_id, missing_items)
        english_msg = format_audio_alert_message(worker_id, missing_items)
        alert_message = hindi_msg if lang == "hi" else english_msg

        # Check speaker status
        if not speaker_enabled:
            # Scenario C: Speaker is OFF -> Suppress audio alert
            logger.info(
                "[AUDIO SUPPRESSED] Camera '%s' speaker is OFF. Worker #%s missing: %s. Hindi: '%s'",
                camera_id,
                worker_id,
                missing_items,
                hindi_msg,
            )
            payload = AudioAlertPayload(
                camera_id=camera_id,
                camera_name=resolved_cam_name,
                worker_id=worker_id,
                missing_ppe=missing_items,
                present_ppe=present_items,
                speaker_enabled=False,
                bypass_speaker=False,
                action="AUDIO_SUPPRESSED",
                message=alert_message,
                hindi_message=hindi_msg,
                english_message=english_msg,
                details={"reason": "camera_speaker_disabled", "audio_played": False, "language": lang},
            )
            self._record_history(payload)
            return payload

        # Speaker is ON: Check cooldown to prevent audio chatter/stutter
        last_alert_time = self._last_alert_timestamps.get(w_key, 0.0)
        time_since_last = now - last_alert_time

        if not force and time_since_last < cd:
            payload = AudioAlertPayload(
                camera_id=camera_id,
                camera_name=resolved_cam_name,
                worker_id=worker_id,
                missing_ppe=missing_items,
                present_ppe=present_items,
                speaker_enabled=True,
                bypass_speaker=False,
                action="COOLDOWN",
                message=alert_message,
                hindi_message=hindi_msg,
                english_message=english_msg,
                details={
                    "reason": "debounce_cooldown",
                    "cooldown_remaining": round(cd - time_since_last, 1),
                    "audio_played": False,
                    "language": lang,
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
            camera_name=resolved_cam_name,
            worker_id=worker_id,
            missing_ppe=missing_items,
            present_ppe=present_items,
            speaker_enabled=True,
            bypass_speaker=False,
            action="AUDIO_TRIGGERED",
            message=alert_message,
            hindi_message=hindi_msg,
            english_message=english_msg,
            details={"audio_played": True, "language": lang},
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

    def evaluate_hazard(
        self,
        camera_id: str,
        speaker_enabled: bool,
        hazards: List[Any],
        camera_name: Optional[str] = None,
        cooldown_seconds: Optional[float] = 6.0,
        force: bool = False,
    ) -> Optional[AudioAlertPayload]:
        """
        CRITICAL HAZARD: Fire & Smoke (Mandatory Speaker Bypass).
        Absolute Override: If Fire or Smoke is detected, an immediate, high-priority audio alert
        is triggered. Completely bypasses the Speaker Status. Even if speaker is toggled OFF,
        the fire/smoke alert sounds!
        Hindi Voice Format: "{Full Camera Name} में {आग / धुएं} का पता चला है, तुरंत जांच करें!"
        """
        if not hazards:
            return None

        has_fire = False
        has_smoke = False
        for h in hazards:
            cname = ""
            if isinstance(h, dict):
                cname = str(h.get("class_name") or h.get("type") or "").lower()
            else:
                cname = str(getattr(h, "class_name", getattr(h, "type", ""))).lower()

            if "fire" in cname:
                has_fire = True
            if "smoke" in cname:
                has_smoke = True

        if not has_fire and not has_smoke:
            return None

        resolved_cam_name = camera_name or camera_id
        hindi_msg = format_hindi_hazard_alert_message(resolved_cam_name, has_fire, has_smoke)
        hazard_type = "fire_and_smoke" if has_fire and has_smoke else ("fire" if has_fire else "smoke")

        now = time.time()
        cd = 6.0 if cooldown_seconds is None else cooldown_seconds
        h_key = (str(camera_id), f"hazard_{hazard_type}")

        last_alert_time = self._last_alert_timestamps.get(h_key, 0.0)
        time_since_last = now - last_alert_time

        if not force and time_since_last < cd:
            payload = AudioAlertPayload(
                camera_id=camera_id,
                camera_name=resolved_cam_name,
                worker_id=None,
                speaker_enabled=speaker_enabled,
                bypass_speaker=True,
                action="COOLDOWN",
                message=hindi_msg,
                hindi_message=hindi_msg,
                hazard_type=hazard_type,
                priority="CRITICAL",
                details={
                    "reason": "hazard_debounce_cooldown",
                    "cooldown_remaining": round(cd - time_since_last, 1),
                    "audio_played": False,
                    "bypassed_speaker": True,
                },
            )
            return payload

        self._last_alert_timestamps[h_key] = now

        logger.critical(
            "[CRITICAL HAZARD AUDIO TRIGGERED] Camera '%s' (Speaker %s). Speaker Bypassed! Voice Alert: '%s'",
            camera_id,
            "ON" if speaker_enabled else "OFF",
            hindi_msg,
        )

        payload = AudioAlertPayload(
            camera_id=camera_id,
            camera_name=resolved_cam_name,
            worker_id=None,
            speaker_enabled=speaker_enabled,
            bypass_speaker=True,
            action="CRITICAL_HAZARD_TRIGGERED",
            message=hindi_msg,
            hindi_message=hindi_msg,
            hazard_type=hazard_type,
            priority="CRITICAL",
            details={
                "audio_played": True,
                "bypassed_speaker": True,
                "hazard": hazard_type,
                "language": "hi",
            },
        )

        # Broadcast WebSocket event immediately
        try:
            broadcaster.broadcast("AudioAlert", payload.model_dump())
        except Exception as b_err:
            logger.warning("Failed to broadcast Critical Hazard AudioAlert: %s", b_err)

        if MetricsCollector:
            try:
                MetricsCollector.get_instance().increment_counter(
                    "rakshya_hazard_audio_alerts_total",
                    labels={"camera_id": camera_id, "hazard": hazard_type},
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
        camera_name: Optional[str] = None,
        lang: str = "hi",
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
                    camera_name=camera_name,
                    lang=lang,
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
