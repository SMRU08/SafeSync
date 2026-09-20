"""
model_loader.py — RAKSHYA VISION Phase 4
Thread-safe model loader for Ultralytics YOLO checkpoints.
Handles device detection, checkpoint integrity validation, and configuration.
"""

import os
import logging
from typing import Dict, Optional, Tuple, Any
import yaml

log = logging.getLogger(__name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DEFAULT_CONFIG_PATH = os.path.join(ROOT, "configs", "detection.yaml")

CANONICAL_CLASSES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}


class ModelLoader:
    """Manages loading, validating, and configuring the YOLO detection model."""

    _instance: Optional["ModelLoader"] = None
    _model: Any = None
    _loaded_path: Optional[str] = None
    _device: str = "cpu"
    _classes: Dict[int, str] = {}
    _config: Dict[str, Any] = {}

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.load_config()

    @classmethod
    def get_instance(cls, config_path: Optional[str] = None) -> "ModelLoader":
        """Singleton accessor to prevent reloading weights into memory repeatedly."""
        if cls._instance is None:
            cls._instance = cls(config_path)
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
                "model": {"path": "models/detection/ppe_fire_smoke_v1/weights/best.pt"},
                "inference": {"confidence_threshold": 0.25, "iou_threshold": 0.45, "image_size": 384, "device": "auto"},
            }
        return self._config

    def resolve_model_path(self, override_path: Optional[str] = None) -> str:
        """Resolves absolute path to model weights."""
        if override_path:
            raw_path = override_path
        else:
            raw_path = self._config.get("model", {}).get("path", "models/detection/ppe_fire_smoke_v1/weights/best.pt")

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
                log.info("Device 'auto' selected: CUDA not available. Executing on CPU.")
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

    def load_model(self, model_path: Optional[str] = None, device: Optional[str] = None) -> Any:
        """
        Loads the YOLO model checkpoint into memory.
        Validates model integrity and canonical class labels.
        """
        from ultralytics import YOLO

        resolved_path = self.resolve_model_path(model_path)
        resolved_device = self.resolve_device(device)

        # Check if already loaded with same parameters
        if self._model is not None and self._loaded_path == resolved_path and self._device == resolved_device:
            return self._model

        log.info(f"Loading YOLO detection model from: {resolved_path}")
        try:
            model = YOLO(resolved_path)
        except Exception as e:
            log.error(f"Failed to load YOLO model from {resolved_path}: {e}")
            raise RuntimeError(f"Failed to load detection model: {e}") from e

        # Validate classes
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
        """Gets or lazily loads the active model."""
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
