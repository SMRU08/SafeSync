"""
manager.py — RAKSHYA VISION Phase 10 Step 5
Production Multi-Camera Manager orchestrating independent camera worker threads,
configuration loading, dynamic start/stop, state querying, and graceful shutdown.
"""

import os
import yaml
import logging
from typing import Dict, Optional, List, Tuple
import numpy as np

from app.camera.schemas import CameraConfigModel, CameraStatus, CameraState
from app.camera.worker import CameraWorker

logger = logging.getLogger("camera_manager")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_CAMERAS_CONFIG = os.path.join(ROOT, "configs", "cameras.yaml")


class CameraManager:
    """
    Singleton lifecycle manager for multiple concurrent camera workers.
    Ensures that each camera stream runs independently with complete fault isolation.
    """
    _instance: Optional["CameraManager"] = None

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or DEFAULT_CAMERAS_CONFIG
        self.workers: Dict[str, CameraWorker] = {}
        self.configs: Dict[str, CameraConfigModel] = {}
        self.load_config()

    @classmethod
    def get_instance(cls, config_path: Optional[str] = None) -> "CameraManager":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = CameraManager(config_path)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Resets singleton instance (primarily for testing)."""
        if cls._instance is not None:
            cls._instance.stop_all()
            cls._instance = None

    def load_config(self, path: Optional[str] = None):
        """Loads and validates camera configurations from YAML."""
        target_path = path or self.config_path
        if not os.path.isfile(target_path):
            logger.warning("Cameras configuration file not found at: %s", target_path)
            return

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            raw_cameras = data.get("cameras", [])
            loaded_configs = {}

            for item in raw_cameras:
                try:
                    cfg = CameraConfigModel(**item)
                    loaded_configs[cfg.id] = cfg
                except Exception as val_err:
                    logger.error("Failed to parse camera config for item %s: %s", item, val_err)

            self.configs = loaded_configs

            # Update or create workers
            for cid, cfg in self.configs.items():
                if cid not in self.workers:
                    self.workers[cid] = CameraWorker(cfg)
                else:
                    # Update config reference
                    self.workers[cid].config = cfg

            logger.info("CameraManager successfully loaded %d cameras from %s", len(self.configs), target_path)
        except Exception as e:
            logger.error("Error loading cameras config from %s: %s", target_path, e)

    def start_all(self):
        """Starts all enabled camera workers concurrently."""
        logger.info("Starting all enabled camera workers (%d registered)...", len(self.workers))
        for cid, worker in self.workers.items():
            if worker.config.enabled:
                worker.start()
            else:
                logger.info("Skipping disabled camera: %s", cid)

    def stop_all(self):
        """Gracefully shuts down all camera worker threads."""
        logger.info("Stopping all camera workers...")
        for cid, worker in self.workers.items():
            try:
                worker.stop()
            except Exception as e:
                logger.error("Error stopping camera worker %s: %s", cid, e)
        logger.info("All camera workers stopped.")

    def start_camera(self, camera_id: str) -> bool:
        """Starts a specific camera worker."""
        if camera_id not in self.workers:
            logger.warning("Cannot start unknown camera: %s", camera_id)
            return False
        self.workers[camera_id].start()
        return True

    def stop_camera(self, camera_id: str) -> bool:
        """Stops a specific camera worker."""
        if camera_id not in self.workers:
            logger.warning("Cannot stop unknown camera: %s", camera_id)
            return False
        self.workers[camera_id].stop()
        return True

    def get_camera_status(self, camera_id: str) -> Optional[CameraStatus]:
        """Gets current operational status and metrics for a camera."""
        if camera_id not in self.workers:
            return None
        return self.workers[camera_id].get_status()

    def get_all_statuses(self) -> List[CameraStatus]:
        """Returns operational statuses for all registered cameras."""
        return [worker.get_status() for worker in self.workers.values()]

    def get_latest_frame(self, camera_id: str) -> Tuple[Optional[np.ndarray], Optional[float]]:
        """Retrieves the latest frame and timestamp from a camera worker."""
        if camera_id not in self.workers:
            return None, None
        return self.workers[camera_id].get_latest_frame()

    def register_camera(self, config: CameraConfigModel, start_immediately: bool = False) -> bool:
        """Dynamically registers or updates a camera configuration."""
        self.configs[config.id] = config
        if config.id in self.workers:
            self.workers[config.id].stop()
        self.workers[config.id] = CameraWorker(config)
        if start_immediately and config.enabled:
            self.workers[config.id].start()
        return True
