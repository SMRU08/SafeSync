"""
ppe_policy.py — RAKSHYA VISION PS06 Compliance
Zone-Specific PPE Policy Engine.

Implements PS06 Requirement: "gloves where applicable"

Provides per-zone, per-camera configurable PPE policy:
  - required_ppe:  ABSENT state generates a P2 violation alert
  - optional_ppe:  Monitored and displayed but ABSENT does NOT generate violation
  - disabled_ppe:  Not monitored in this zone (UNKNOWN by policy)

Usage:
    policy = ZonePPEPolicyEngine.get_instance()
    ppe_requirements = policy.get_requirements_for_zone("production_floor")
    # Returns: {"helmet": "required", "safety_vest": "required",
    #           "gloves": "required", "safety_footwear": "required"}

    is_required = policy.is_ppe_required("gloves", "storage_area")
    # Returns: False (gloves are optional in storage_area)
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger("ppe_policy")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DEFAULT_PPE_ZONES_CONFIG = os.path.join(ROOT, "configs", "ppe_zones.yaml")

# Policy levels for each PPE item
PPE_POLICY_REQUIRED = "required"
PPE_POLICY_OPTIONAL = "optional"
PPE_POLICY_DISABLED = "disabled"

# All canonical PPE items
ALL_PPE_ITEMS = ["helmet", "safety_vest", "gloves", "safety_footwear"]


def _load_ppe_zones_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Loads the ppe_zones.yaml configuration file."""
    target = path or DEFAULT_PPE_ZONES_CONFIG
    if not os.path.isfile(target):
        logger.warning("ppe_zones.yaml not found at %s. Using default (all required).", target)
        return {}
    try:
        with open(target, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error("Failed to load ppe_zones.yaml: %s. Using default policy.", e)
        return {}


class ZonePPEPolicy:
    """
    Represents the resolved PPE policy for a single zone.
    Each PPE item maps to: "required", "optional", or "disabled".
    """

    def __init__(
        self,
        zone_id: str,
        zone_name: str,
        required: List[str],
        optional: List[str],
        disabled: List[str],
        notes: str = "",
    ):
        self.zone_id = zone_id
        self.zone_name = zone_name
        self.notes = notes

        # Build lookup maps
        self._policy: Dict[str, str] = {}
        for item in ALL_PPE_ITEMS:
            if item in disabled:
                self._policy[item] = PPE_POLICY_DISABLED
            elif item in optional:
                self._policy[item] = PPE_POLICY_OPTIONAL
            elif required and item in required:
                self._policy[item] = PPE_POLICY_REQUIRED
            else:
                # Default: required unless explicitly marked otherwise
                self._policy[item] = PPE_POLICY_REQUIRED

    def get_policy(self, ppe_item: str) -> str:
        """Returns 'required', 'optional', or 'disabled' for a PPE item."""
        return self._policy.get(ppe_item.lower(), PPE_POLICY_REQUIRED)

    def is_required(self, ppe_item: str) -> bool:
        """True if missing this PPE should generate a violation alert."""
        return self.get_policy(ppe_item) == PPE_POLICY_REQUIRED

    def is_optional(self, ppe_item: str) -> bool:
        """True if this PPE is monitored but not violation-generating."""
        return self.get_policy(ppe_item) == PPE_POLICY_OPTIONAL

    def is_disabled(self, ppe_item: str) -> bool:
        """True if this PPE is not monitored in this zone."""
        return self.get_policy(ppe_item) == PPE_POLICY_DISABLED

    def get_required_items(self) -> List[str]:
        """Returns list of PPE items that are required in this zone."""
        return [item for item, p in self._policy.items() if p == PPE_POLICY_REQUIRED]

    def get_optional_items(self) -> List[str]:
        """Returns list of PPE items that are optional in this zone."""
        return [item for item, p in self._policy.items() if p == PPE_POLICY_OPTIONAL]

    def get_disabled_items(self) -> List[str]:
        """Returns list of PPE items that are disabled (not monitored) in this zone."""
        return [item for item, p in self._policy.items() if p == PPE_POLICY_DISABLED]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes zone policy to a dict for API responses."""
        return {
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "policy": dict(self._policy),
            "required": self.get_required_items(),
            "optional": self.get_optional_items(),
            "disabled": self.get_disabled_items(),
            "notes": self.notes,
        }


class ZonePPEPolicyEngine:
    """
    Singleton engine that resolves per-zone PPE requirements from ppe_zones.yaml.

    PS06 Section 7 — "Where Applicable" PPE Rules:
        Zone A: Helmet=required, Vest=required, Footwear=required, Gloves=required
        Zone B: Helmet=required, Vest=required, Footwear=required, Gloves=optional
        ...

    The compliance engine uses this to determine whether ABSENT state generates
    a violation or is silently tolerated.
    """

    _instance: Optional["ZonePPEPolicyEngine"] = None

    def __init__(self, config_path: Optional[str] = None):
        self._config_path = config_path or DEFAULT_PPE_ZONES_CONFIG
        self._zone_policies: Dict[str, ZonePPEPolicy] = {}
        self._default_policy: Optional[ZonePPEPolicy] = None
        self._load()

    @classmethod
    def get_instance(cls, config_path: Optional[str] = None) -> "ZonePPEPolicyEngine":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = cls(config_path)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Resets singleton (for testing)."""
        cls._instance = None

    def _load(self):
        """Loads and parses ppe_zones.yaml into ZonePPEPolicy objects."""
        raw = _load_ppe_zones_config(self._config_path)
        zones_raw = raw.get("zones", {})

        for zone_id, zone_data in zones_raw.items():
            if not isinstance(zone_data, dict):
                continue

            req_map = zone_data.get("required_ppe", {})
            opt_list = zone_data.get("optional_ppe", [])
            dis_list = zone_data.get("disabled_ppe", [])

            # Resolve required items from the required_ppe map (True = required)
            required_items = [k for k, v in req_map.items() if v is True]
            # Ensure optional_ppe items are NOT in required
            required_items = [item for item in required_items if item not in opt_list and item not in dis_list]

            policy = ZonePPEPolicy(
                zone_id=zone_id,
                zone_name=zone_data.get("zone_name", zone_id),
                required=required_items,
                optional=opt_list,
                disabled=dis_list,
                notes=zone_data.get("notes", ""),
            )
            self._zone_policies[zone_id] = policy
            logger.debug(
                "Loaded PPE policy for zone '%s': required=%s optional=%s disabled=%s",
                zone_id,
                policy.get_required_items(),
                policy.get_optional_items(),
                policy.get_disabled_items(),
            )

        # Default policy
        default_raw = raw.get("default_policy", {})
        if default_raw:
            req_map = default_raw.get("required_ppe", {})
            required_items = [k for k, v in req_map.items() if v is True]
            self._default_policy = ZonePPEPolicy(
                zone_id="default",
                zone_name="Default Policy",
                required=required_items,
                optional=default_raw.get("optional_ppe", []),
                disabled=default_raw.get("disabled_ppe", []),
                notes=default_raw.get("notes", ""),
            )
        else:
            # Hard fallback: all PPE required
            self._default_policy = ZonePPEPolicy(
                zone_id="default",
                zone_name="Default (All Required)",
                required=ALL_PPE_ITEMS,
                optional=[],
                disabled=[],
                notes="Fallback: all PPE required",
            )

        logger.info(
            "ZonePPEPolicyEngine loaded: %d zone policies + default",
            len(self._zone_policies),
        )

    def get_policy_for_zone(self, zone_id: str) -> ZonePPEPolicy:
        """
        Returns the ZonePPEPolicy for a given zone_id.
        Falls back to the default policy if zone is not configured.
        """
        if zone_id and zone_id.lower() in self._zone_policies:
            return self._zone_policies[zone_id.lower()]
        return self._default_policy  # type: ignore

    def is_ppe_required(self, ppe_item: str, zone_id: str) -> bool:
        """
        Returns True if missing this PPE in this zone should generate a violation.
        Returns False for optional or disabled PPE items.
        """
        policy = self.get_policy_for_zone(zone_id)
        return policy.is_required(ppe_item)

    def get_required_ppe_for_zone(self, zone_id: str) -> List[str]:
        """Returns list of PPE items that are violation-generating in this zone."""
        return self.get_policy_for_zone(zone_id).get_required_items()

    def list_all_zones(self) -> List[Dict[str, Any]]:
        """Returns all configured zone policies as a list of dicts."""
        zones = [p.to_dict() for p in self._zone_policies.values()]
        zones.append({"zone_id": "default", **self._default_policy.to_dict()})  # type: ignore
        return zones
