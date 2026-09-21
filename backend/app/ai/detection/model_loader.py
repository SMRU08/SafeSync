"""
model_loader.py — RAKSHYA VISION Phase 10
Production Model Loader with Model Registry & Immutable SHA-256 Checksum Enforcement.
Supports 'production', 'candidate', and 'archived' model states.
"""

import os
import hashlib
import logging
from typing import Dict, Optional, Tuple, Any
import yaml

log = logging.getLogger(__name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DEFAULT_CONFIG_PATH = os.path.join(ROOT, "configs", "detection.yaml")
DEFAULT_REGISTRY_PATH = os.path.join(ROOT, "models", "registry", "model_registry.yaml")

CANONICAL_CLASSES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}


def load_model_registry(registry_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads and validates the model registry YAML file.
    Raises FileNotFoundError if missing.
    Raises ValueError if malformed.
    """
    path = registry_path or DEFAULT_REGISTRY_PATH
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Model registry not found at: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Malformed model registry at {path}: YAML parse error: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Malformed model registry at {path}: Root must be a dictionary.")

    if "models" not in data or not isinstance(data["models"], dict):
        raise ValueError(f"Malformed model registry at {path}: Missing 'models' mapping.")

    return data


def get_model_entry_from_registry(
    model_identifier: str = "production",
    registry_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves a model entry from the registry by status ('production', 'candidate', 'archived')
    or by exact model_name key.
    """
    registry = load_model_registry(registry_path)
    models = registry.get("models", {})

    target = model_identifier.strip().lower()

    # 1. Match by lifecycle status
    if target in ("production", "candidate", "archived"):
        # For production, check active_production_model preference first
        if target == "production":
            active_name = registry.get("active_production_model")
            if active_name and active_name in models and models[active_name].get("status") == "production":
                return models[active_name]

        for entry in models.values():
            if str(entry.get("status", "")).strip().lower() == target:
                return entry

        raise KeyError(f"No model with status '{target}' found in registry.")

    # 2. Match by exact model key or model_name field
    if model_identifier in models:
        return models[model_identifier]

    for entry in models.values():
        if entry.get("model_name") == model_identifier:
            return entry

    raise KeyError(f"Model '{model_identifier}' not found in registry.")


class ModelLoader:
    """Manages loading, validating, and configuring the YOLO detection model."""

    _instance: Optional["ModelLoader"] = None
    _model: Any = None
    _loaded_path: Optional[str] = None
    _device: str = "cpu"
    _classes: Dict[int, str] = {}
    _config: Dict[str, Any] = {}

    def __init__(self, config_path: Optional[str] = None, registry_path: Optional[str] = None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.registry_path = registry_path or DEFAULT_REGISTRY_PATH
        self.load_config()

    @classmethod
    def get_instance(cls, config_path: Optional[str] = None, registry_path: Optional[str] = None) -> "ModelLoader":
        """Singleton accessor to prevent reloading weights into memory repeatedly."""
        if cls._instance is None:
            cls._instance = cls(config_path, registry_path)
        return cls._instance

    def load_config(self) -> Dict[str, Any]:
        """Loads configuration from YAML file or defaults."""
        if os.path.isfile(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
            log.info(f"Loaded detection config from {self.config_path}")
        else:
            log.warning(f"Detection config not found at {self.config_path}, using defaults")
            self._config = {
                "model": {"path": "models/detection/ppe_fire_smoke_v2/weights/best.pt"},
                "inference": {"confidence_threshold": 0.25, "iou_threshold": 0.45, "image_size": 384, "device": "auto"},
            }
        return self._config

    def resolve_model_path(self, override_path: Optional[str] = None, target_status: str = "production") -> str:
        """
        Resolves absolute path to model weights.
        If override_path is given, uses it directly (or resolves relative to ROOT).
        Otherwise resolves the production model registered in the registry.
        """
        if override_path:
            raw_path = override_path
        else:
            try:
                entry = get_model_entry_from_registry(target_status, self.registry_path)
                raw_path = entry.get("model_path") or entry.get("file", "models/detection/ppe_fire_smoke_v2/weights/best.pt")
            except Exception as e:
                log.warning(f"Registry lookup failed ({e}), falling back to detection config path.")
                raw_path = self._config.get("model", {}).get("path", "models/detection/ppe_fire_smoke_v2/weights/best.pt")

        if os.path.isabs(raw_path):
            abs_path = raw_path
        else:
            abs_path = os.path.normpath(os.path.join(ROOT, raw_path))

        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"Detection model weights file not found at: {abs_path}")

        return abs_path

    def resolve_device(self, requested_device: Optional[str] = None) -> str:
        """
        Resolves execution device.
        - 'auto': chooses CUDA if available, else CPU (logged clearly).
        - 'cuda' or '0': validates CUDA availability. Fails clearly if unavailable.
        - 'cpu': explicitly CPU.
        """
        import torch

        req = (requested_device or self._config.get("inference", {}).get("device", "auto")).strip().lower()
        cuda_available = torch.cuda.is_available()

        if req == "auto":
            if cuda_available:
                gpu_name = torch.cuda.get_device_properties(0).name
                log.info(f"Device 'auto' selected: CUDA available. Using GPU: {gpu_name}")
                return "0"
            else:
                log.info(f"Device 'auto' selected: CUDA not available. Executing on CPU.")
                return "cpu"
        elif req in ("cuda", "0", "cuda:0"):
            if not cuda_available:
                raise RuntimeError(
                    f"Explicit device '{req}' requested, but CUDA is not available on this machine. "
                    "Cannot silently switch when explicit GPU was requested."
                )
            gpu_name = torch.cuda.get_device_properties(0).name
            log.info(f"Explicit device '{req}' confirmed. GPU: {gpu_name}")
            return "0"
        elif req == "cpu":
            log.info("Explicit device 'cpu' configured.")
            return "cpu"
        else:
            log.warning(f"Unrecognized device '{req}', defaulting to cpu.")
            return "cpu"

    def verify_checkpoint_integrity(
        self,
        resolved_path: str,
        expected_sha: Optional[str] = None,
        registry_path: Optional[str] = None,
    ) -> str:
        """
        Validates the SHA-256 checksum of the model checkpoint against model_registry.yaml
        or companion .sha256 file.
        STOPS MODEL LOADING and raises ValueError with 'MODEL CHECKSUM VERIFICATION FAILED' if mismatched.
        """
        reg_path = registry_path or self.registry_path

        if expected_sha is None:
            # Look up from registry
            if os.path.isfile(reg_path):
                try:
                    reg = load_model_registry(reg_path)
                    norm_target = os.path.normpath(resolved_path)
                    for entry in reg.get("models", {}).values():
                        entry_file = entry.get("model_path") or entry.get("file", "")
                        entry_path = os.path.normpath(os.path.join(ROOT, entry_file))
                        if entry_path == norm_target:
                            expected_sha = entry.get("sha256")
                            break
                except Exception as e:
                    log.warning(f"Error parsing registry for integrity check: {e}")

            # Fallback to companion .sha256 file
            if not expected_sha:
                companion_sha = resolved_path + ".sha256"
                sha_in_dir = os.path.join(os.path.dirname(os.path.dirname(resolved_path)), "model.sha256")
                for candidate in [companion_sha, sha_in_dir]:
                    if os.path.isfile(candidate):
                        with open(candidate, "r", encoding="utf-8") as f:
                            expected_sha = f.read().strip()
                            break

        if not expected_sha:
            raise ValueError(
                f"MODEL CHECKSUM VERIFICATION FAILED: No trusted SHA-256 reference found in registry or companion file for '{resolved_path}'."
            )

        # Compute actual SHA-256
        hasher = hashlib.sha256()
        with open(resolved_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        actual_sha = hasher.hexdigest().lower()

        if actual_sha != expected_sha.lower():
            err_msg = (
                f"MODEL CHECKSUM VERIFICATION FAILED: Checksum mismatch for checkpoint at {resolved_path}.\n"
                f"Expected SHA-256: {expected_sha.lower()}\n"
                f"Actual SHA-256:   {actual_sha}\n"
                "Model weights may be corrupted or tampered with. Stopping model load."
            )
            log.critical(err_msg)
            raise ValueError(err_msg)

        log.info(f"Model checkpoint integrity verified: {actual_sha[:16]}... (SHA-256 match)")
        return actual_sha

    def load_model(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        registry_path: Optional[str] = None,
        target_status: str = "production",
        expected_sha: Optional[str] = None,
    ) -> Any:
        """
        Loads the YOLO model checkpoint into memory.
        Enforces registry lookup and SHA-256 checksum verification before loading.
        """
        from ultralytics import YOLO

        if registry_path:
            self.registry_path = registry_path

        resolved_path = self.resolve_model_path(model_path, target_status=target_status)
        resolved_device = self.resolve_device(device)

        # Check if already loaded with identical parameters
        if self._model is not None and self._loaded_path == resolved_path and self._device == resolved_device:
            return self._model

        # 1. Enforce SHA-256 Checksum Verification
        self.verify_checkpoint_integrity(resolved_path, expected_sha=expected_sha, registry_path=self.registry_path)

        # 2. Instantiate YOLO only after checksum verification passes
        log.info(f"Loading YOLO detection model from: {resolved_path}")
        try:
            model = YOLO(resolved_path)
        except Exception as e:
            log.error(f"Failed to load YOLO model from {resolved_path}: {e}")
            raise RuntimeError(f"Failed to load detection model: {e}") from e

        # 3. Validate canonical classes
        classes = model.names
        log.info(f"Loaded model classes ({len(classes)}): {classes}")
        for idx, expected_name in CANONICAL_CLASSES.items():
            actual = classes.get(idx)
            if actual != expected_name:
                log.warning(
                    f"Model class mismatch at index {idx}: expected '{expected_name}', got '{actual}'"
                )

        self._model = model
        self._loaded_path = resolved_path
        self._device = resolved_device
        self._classes = classes

        log.info(
            f"Successfully initialized YOLO model: path='{resolved_path}', device='{resolved_device}', classes={len(classes)}"
        )
        return self._model

    @property
    def model(self) -> Any:
        """Gets or lazily loads the active production model."""
        if self._model is None:
            self.load_model()
        return self._model

    @property
    def classes(self) -> Dict[int, str]:
        if not self._classes:
            self.load_model()
        return self._classes

    @property
    def device(self) -> str:
        return self._device

    @property
    def model_path(self) -> Optional[str]:
        return self._loaded_path

    @property
    def config(self) -> Dict[str, Any]:
        return self._config

    def is_loaded(self) -> bool:
        return self._model is not None
