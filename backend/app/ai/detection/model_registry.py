"""
model_registry.py — RAKSHYA VISION
Central registry and lifecycle manager for decoupled AI models:
- Dedicated PPE models (Person, Helmet, Safety Vest, Gloves, Safety Footwear)
- Dedicated Hazard models (Fire, Smoke)
- Checksum validation, version rollback, and metadata introspection.
"""

import os
import json
import hashlib
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("model_registry")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
REGISTRY_JSON = os.path.join(ROOT, "models", "MODEL_REGISTRY.json")


class ModelRegistry:
    """Manages versioned models, integrity checks, and runtime resolution."""

    _instance: Optional["ModelRegistry"] = None

    def __init__(self, registry_file: str = REGISTRY_JSON):
        self.registry_file = registry_file
        self.data: Dict[str, Any] = self._load()

    @classmethod
    def get_instance(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self) -> Dict[str, Any]:
        if os.path.isfile(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Failed to read MODEL_REGISTRY.json: %s", e)
        return {"models": {}}

    def get_model_info(self, model_type: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Returns metadata for a model type ('ppe' or 'hazards')."""
        group = self.data.get("models", {}).get(model_type)
        if not group:
            return None
        ver_key = version or group.get("active_version")
        return group.get("versions", {}).get(ver_key)

    def verify_checksum(self, model_type: str, version: Optional[str] = None) -> bool:
        """Computes SHA-256 and validates against registry entry."""
        info = self.get_model_info(model_type, version)
        if not info:
            return False
        rel_path = info.get("path")
        expected_sha = info.get("sha256")
        if not rel_path or not expected_sha:
            return False

        full_path = os.path.join(ROOT, rel_path)
        if not os.path.isfile(full_path):
            logger.warning("Checkpoint file not found: %s", full_path)
            return False

        hasher = hashlib.sha256()
        with open(full_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        actual_sha = hasher.hexdigest()
        is_match = (actual_sha.lower() == expected_sha.lower())
        if not is_match:
            logger.error("Checksum mismatch for %s/%s! Expected: %s, got: %s", model_type, version, expected_sha, actual_sha)
        return is_match

    def get_model_path(self, model_type: str, version: Optional[str] = None) -> Optional[str]:
        """Resolves absolute path to active checkpoint."""
        info = self.get_model_info(model_type, version)
        if not info:
            return None
        rel_path = info.get("path")
        if rel_path:
            full_path = os.path.join(ROOT, rel_path)
            if os.path.isfile(full_path):
                return full_path
        return None
