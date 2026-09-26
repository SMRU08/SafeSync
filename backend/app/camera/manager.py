"""
manager.py — SafeSync Phase 10 Step 5
Production Multi-Camera Manager orchestrating independent camera worker threads,
configuration loading, dynamic start/stop, state querying, and graceful shutdown.
"""

import os
import yaml
import logging
from typing import Dict, Optional, List, Tuple, Any
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

            # Also synchronize and load cameras from the SQLite database
            try:
                from app.database.session import SessionLocal
                from app.models.camera import CameraModel
                with SessionLocal() as db:
                    db_cameras = db.query(CameraModel).all()
                    for db_cam in db_cameras:
                        if db_cam.camera_id not in loaded_configs:
                            try:
                                cfg = CameraConfigModel(
                                    id=db_cam.camera_id,
                                    name=db_cam.name,
                                    location=db_cam.location or "",
                                    zone_id=db_cam.zone_id,
                                    source=db_cam.source,
                                    source_type=db_cam.source_type,
                                    enabled=db_cam.enabled,
                                    speaker_enabled=getattr(db_cam, "speaker_enabled", True),
                                    fps_target=db_cam.fps_target,
                                    resolution=db_cam.resolution,
                                    timeout_seconds=db_cam.timeout_seconds,
                                )
                                loaded_configs[cfg.id] = cfg
                            except Exception as cfg_err:
                                logger.error("Failed to parse DB camera %s: %s", db_cam.camera_id, cfg_err)
            except Exception as db_err:
                logger.debug("Database camera loading note: %s", db_err)

            self.configs = loaded_configs

            # Update or create workers
            for cid, cfg in self.configs.items():
                if cid not in self.workers:
                    self.workers[cid] = CameraWorker(cfg)
                else:
                    # Update config reference
                    self.workers[cid].config = cfg

            logger.info("CameraManager successfully loaded %d cameras from %s and database", len(self.configs), target_path)
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

    def get_worker(self, camera_id: str) -> Optional[CameraWorker]:
        """Returns the worker instance for a camera if registered."""
        return self.workers.get(camera_id)

    def get_camera_status(self, camera_id: str) -> Optional[CameraStatus]:
        """Gets current operational status and metrics for a camera."""
        if camera_id not in self.workers:
            return None
        return self.workers[camera_id].get_status()

    def get_all_statuses(self) -> List[CameraStatus]:
        """Returns operational statuses for all registered cameras."""
        return [worker.get_status() for worker in self.workers.values()]

    def get_latest_frame(self, camera_id: str, annotated: bool = True) -> Tuple[Optional[np.ndarray], Optional[float]]:
        """Retrieves the latest frame and timestamp from a camera worker."""
        if camera_id not in self.workers:
            return None, None
        return self.workers[camera_id].get_latest_frame(annotated=annotated)

    def wait_for_new_frame(
        self,
        camera_id: str,
        last_frame_id: int,
        annotated: bool = True,
        timeout: float = 0.06,
    ) -> Tuple[Optional[np.ndarray], int, Optional[float]]:
        """Retrieves a new frame as soon as captured, discarding stale frames."""
        worker = self.workers.get(camera_id)
        if not worker:
            return None, last_frame_id, None
        return worker.wait_for_new_frame(last_frame_id, annotated=annotated, timeout=timeout)

    def get_live_compliance(self, camera_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves the latest active worker tracking and compliance data.
        If camera_id is not specified, returns data from the first active camera worker.
        """
        if camera_id and camera_id in self.workers:
            return self.workers[camera_id].get_live_compliance()

        # Find first worker with active tracking data
        for cid, worker in self.workers.items():
            if worker.state == CameraState.CONNECTED:
                data = worker.get_live_compliance()
                if data.get("workers") or data.get("summary"):
                    return data

        # Fallback to first registered worker
        if self.workers:
            first_worker = next(iter(self.workers.values()))
            return first_worker.get_live_compliance()

        return {"camera_id": "none", "workers": [], "summary": None, "annotated_image_base64": None, "timestamp": None}

    def register_camera(self, config: CameraConfigModel, start_immediately: bool = False, persist_db: bool = True) -> bool:
        """Dynamically registers or updates a camera configuration with DB persistence."""
        self.configs[config.id] = config
        if config.id in self.workers:
            self.workers[config.id].stop()
        self.workers[config.id] = CameraWorker(config)
        if start_immediately and config.enabled:
            self.workers[config.id].start()

        # Persist to database
        if persist_db:
            try:
                from app.database.session import SessionLocal
                from app.models.camera import CameraModel
                with SessionLocal() as db:
                    existing = db.query(CameraModel).filter_by(camera_id=config.id).first()
                    if existing:
                        existing.name = config.name
                        existing.location = getattr(config, "location", "") or ""
                        existing.zone_id = config.zone_id
                        existing.source = config.source
                        existing.source_type = config.source_type.value
                        existing.enabled = config.enabled
                        existing.speaker_enabled = getattr(config, "speaker_enabled", True)
                        existing.fps_target = config.fps_target
                        existing.resolution = config.resolution
                    else:
                        new_entry = CameraModel(
                            camera_id=config.id,
                            name=config.name,
                            location=getattr(config, "location", "") or "",
                            zone_id=config.zone_id,
                            source=config.source,
                            source_type=config.source_type.value,
                            enabled=config.enabled,
                            speaker_enabled=getattr(config, "speaker_enabled", True),
                            fps_target=config.fps_target,
                            resolution=config.resolution,
                            timeout_seconds=config.timeout_seconds,
                        )
                        db.add(new_entry)
                    db.commit()
            except Exception as exc:
                logger.warning("Database persistence error for camera %s: %s", config.id, exc)

        return True

    def set_camera_speaker(self, camera_id: str, enabled: bool) -> bool:
        """Sets the speaker status for a camera worker and persists to database."""
        if camera_id in self.configs:
            self.configs[camera_id].speaker_enabled = enabled
        if camera_id in self.workers:
            self.workers[camera_id].set_speaker(enabled)

        try:
            from app.database.session import SessionLocal
            from app.models.camera import CameraModel
            with SessionLocal() as db:
                cam = db.query(CameraModel).filter_by(camera_id=camera_id).first()
                if cam:
                    cam.speaker_enabled = enabled
                    db.commit()
        except Exception as e:
            logger.warning("Failed to persist speaker status for %s: %s", camera_id, e)

        return True

    def unregister_camera(self, camera_id: str, delete_db: bool = True) -> bool:
        """Gracefully removes a camera and deletes it from database."""
        if camera_id in self.workers:
            self.workers[camera_id].stop()
            del self.workers[camera_id]
        if camera_id in self.configs:
            del self.configs[camera_id]

        if delete_db:
            try:
                from app.database.session import SessionLocal
                from app.models.camera import CameraModel
                with SessionLocal() as db:
                    row = db.query(CameraModel).filter_by(camera_id=camera_id).first()
                    if row:
                        db.delete(row)
                        db.commit()
            except Exception as exc:
                logger.warning("Database deletion error for camera %s: %s", camera_id, exc)

        return True

    def test_camera_source(self, source: str, source_type: str = "usb") -> Dict[str, Any]:
        """Validates if a camera source can be opened and probed."""
        import cv2
        st = source_type.lower()
        if st == "synthetic":
            return {"reachable": True, "details": "Synthetic stream generator available"}

        try:
            # Parse integer index for USB devices
            parsed_src = int(source) if source.isdigit() else source
            cap = cv2.VideoCapture(parsed_src)
            if not cap.isOpened():
                return {"reachable": False, "error": f"Failed to open video capture for: {source}"}

            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                return {"reachable": False, "error": "Source opened but failed to capture test frame."}

            h, w = frame.shape[:2]
            return {
                "reachable": True,
                "resolution": f"{w}x{h}",
                "fps": 30.0,
                "details": f"Camera source verified ({w}x{h})"
            }
        except Exception as e:
            return {"reachable": False, "error": str(e)}
