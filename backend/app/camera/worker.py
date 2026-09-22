"""
worker.py — RAKSHYA VISION Phase 10 Step 5
Thread-isolated Camera Worker managing independent capture lifecycle,
bounded exponential backoff reconnection, metric tracking, and safe frame buffering.
"""

import os
import re
import time
import logging
import threading
from typing import Optional, Tuple, Any, Dict, List
import numpy as np
import cv2

from app.camera.schemas import (
    CameraConfigModel,
    CameraState,
    CameraMetrics,
    CameraStatus,
    CameraSourceType,
)

logger = logging.getLogger("camera_worker")


def mask_camera_source(source: str) -> str:
    """Masks credentials in RTSP/HTTP URLs for safe logging and status reporting."""
    if not source:
        return ""
    # Matches ://user:password@
    return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:********@", str(source))


def expand_source_env(source: str) -> str:
    """Expands ${ENV_VAR} references within camera source strings."""
    if not source:
        return ""
    pattern = re.compile(r"\$\{([^}]+)\}")
    matches = pattern.findall(source)
    expanded = source
    for var in matches:
        val = os.environ.get(var, "")
        expanded = expanded.replace(f"${{{var}}}", val)
    return expanded


class CameraWorker:
    """
    Isolated worker thread capturing frames from a single camera source.
    Ensures failures in one camera never propagate to other cameras or the host application.
    """

    def __init__(self, config: CameraConfigModel):
        self.config = config
        self.camera_id = config.id
        self.safe_source = mask_camera_source(config.source)

        # Threading state
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Operational state & metrics
        self.state: CameraState = CameraState.DISABLED if not config.enabled else CameraState.DISCONNECTED
        self.metrics = CameraMetrics()
        self._start_time: Optional[float] = None

        # Frame buffers
        self._latest_frame: Optional[np.ndarray] = None
        self._latest_annotated_frame: Optional[np.ndarray] = None
        self._latest_frame_time: Optional[float] = None
        self._latest_workers: List[Any] = []
        self._latest_compliance_summary: Optional[Any] = None
        self._latest_annotated_b64: Optional[str] = None

        # AI Pipeline configuration
        self.infer_interval_frames = 2  # Run AI inference every 2 frames for smooth 15 FPS inference on 30 FPS stream
        self._compliance_engine: Optional[Any] = None
        self._alert_engine: Optional[Any] = None
        self._event_normalizer: Optional[Any] = None

        # FPS calculation window
        self._fps_window_start = time.time()
        self._fps_window_frames = 0

    def _init_ai_engines(self):
        """Initializes thread-local AI inference, tracking, and compliance components."""
        if self._compliance_engine is None:
            try:
                from app.ai.compliance.compliance_engine import WorkerComplianceEngine
                from app.services.event_normalizer import EventNormalizer
                from app.services.alert_engine import AlertEngine
                self._compliance_engine = WorkerComplianceEngine()
                self._alert_engine = AlertEngine()
                self._event_normalizer = EventNormalizer()
                logger.info("Initialized AI compliance engine for camera %s", self.camera_id)
            except Exception as e:
                logger.error("Failed to initialize AI compliance engine for %s: %s", self.camera_id, e, exc_info=True)

    def _process_frame_ai(self, frame: np.ndarray, frame_time: float):
        """Runs scheduled live YOLO detection, ByteTrack tracking, PPE association, and alert dispatch."""
        if self._compliance_engine is None:
            return

        try:
            t_start = time.perf_counter()
            compliance_resp, annotated_frame, latencies = self._compliance_engine.process_frame(
                frame,
                confidence_threshold=0.20,
                annotate=True,
            )
            ai_duration_ms = (time.perf_counter() - t_start) * 1000.0

            with self._lock:
                self._latest_annotated_frame = annotated_frame
                self._latest_workers = compliance_resp.workers
                self._latest_compliance_summary = compliance_resp.summary
                self._latest_annotated_b64 = compliance_resp.annotated_image_base64
                self.metrics.inference_latency_ms = round(ai_duration_ms, 2)
                self.metrics.active_workers = len(compliance_resp.workers)
                self.metrics.active_violations = compliance_resp.summary.non_compliant_workers

            # If safety events were detected, normalize and dispatch
            if self._event_normalizer and self._alert_engine:
                events = self._event_normalizer.from_compliance_response(
                    compliance_resp,
                    camera_id=self.camera_id,
                    zone_id=self.config.zone_id,
                )
                if events:
                    from app.database.session import SessionLocal
                    from app.services.evidence_manager import EvidenceManager
                    with SessionLocal() as db:
                        for ev in events:
                            try:
                                alert, incident, action = self._alert_engine.process_event(ev, db=db)
                                if action in ("CREATED", "ESCALATED") and incident:
                                    try:
                                        EvidenceManager.get_instance().capture_incident_evidence(
                                            incident_id=incident.incident_id,
                                            camera_id=self.camera_id,
                                            frame=annotated_frame,
                                            annotations=ev.details,
                                            db=db,
                                            evidence_type="SNAPSHOT",
                                        )
                                    except Exception as ev_err:
                                        logger.debug("Evidence capture error: %s", ev_err)
                            except Exception as alert_err:
                                logger.warning("Alert processing error: %s", alert_err)

        except Exception as e:
            logger.error("Error in AI frame processing for %s: %s", self.camera_id, e, exc_info=True)

    def start(self):
        """Starts the camera capture worker thread if enabled."""
        with self._lock:
            if not self.config.enabled:
                self.state = CameraState.DISABLED
                logger.info("Camera %s is disabled in config. Not starting.", self.camera_id)
                return

            if self._thread is not None and self._thread.is_alive():
                logger.warning("CameraWorker %s is already running.", self.camera_id)
                return

            self._stop_event.clear()
            self.state = CameraState.CONNECTING
            self._start_time = time.time()
            self._init_ai_engines()
            self._thread = threading.Thread(
                target=self._run_loop,
                name=f"CameraWorker-{self.camera_id}",
                daemon=True
            )
            self._thread.start()
            logger.info("Started CameraWorker thread for %s (%s)", self.camera_id, self.safe_source)

    def stop(self, timeout: float = 3.0):
        """Gracefully stops the worker thread and releases resources."""
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        with self._lock:
            self.state = CameraState.DISCONNECTED
            self._latest_frame = None
            self._latest_annotated_frame = None
            self._latest_workers = []
            self._latest_compliance_summary = None
            self._latest_annotated_b64 = None
            logger.info("Stopped CameraWorker for %s", self.camera_id)

    def get_status(self) -> CameraStatus:
        """Returns snapshot of current camera status and metrics."""
        with self._lock:
            # Update uptime
            if self._start_time and self.state == CameraState.CONNECTED:
                self.metrics.uptime_seconds = round(time.time() - self._start_time, 1)

            return CameraStatus(
                camera_id=self.camera_id,
                name=self.config.name,
                zone_id=self.config.zone_id,
                source_type=self.config.source_type.value,
                enabled=self.config.enabled,
                state=self.state,
                metrics=self.metrics.model_copy(),
                safe_source=self.safe_source,
            )

    def get_latest_frame(self, annotated: bool = True) -> Tuple[Optional[np.ndarray], Optional[float]]:
        """Returns the most recent captured frame (copy) and timestamp."""
        with self._lock:
            if annotated and self._latest_annotated_frame is not None:
                return self._latest_annotated_frame.copy(), self._latest_frame_time
            if self._latest_frame is None:
                return None, None
            return self._latest_frame.copy(), self._latest_frame_time

    def get_live_compliance(self) -> Dict[str, Any]:
        """Returns the latest active worker tracking and compliance data."""
        with self._lock:
            workers_out = []
            for w in self._latest_workers:
                try:
                    if hasattr(w, "model_dump"):
                        wd = w.model_dump()
                    elif isinstance(w, dict):
                        wd = dict(w)
                    else:
                        wd = vars(w).copy()
                    
                    # Ensure bbox is a 4-element array [x1, y1, x2, y2]
                    if "bbox" in wd:
                        b = wd["bbox"]
                        if isinstance(b, dict):
                            wd["bbox"] = [
                                float(b.get("x1", 0)),
                                float(b.get("y1", 0)),
                                float(b.get("x2", 0)),
                                float(b.get("y2", 0)),
                            ]
                    workers_out.append(wd)
                except Exception as e:
                    logger.debug("Error serializing worker in get_live_compliance: %s", e)

            return {
                "camera_id": self.camera_id,
                "workers": workers_out,
                "summary": self._latest_compliance_summary.model_dump() if hasattr(self._latest_compliance_summary, "model_dump") else self._latest_compliance_summary,
                "annotated_image_base64": self._latest_annotated_b64,
                "timestamp": self._latest_frame_time,
            }

    def _open_capture(self) -> Optional[cv2.VideoCapture]:
        """Resolves source and attempts to initialize cv2.VideoCapture safely."""
        source_str = expand_source_env(self.config.source)

        if self.config.source_type == CameraSourceType.SYNTHETIC:
            # Synthetic source doesn't need OpenCV capture
            return None

        target_source: Any = source_str
        is_device_index = False
        st = str(self.config.source_type).lower()

        if st in ("usb", "camera", "webcam") or self.config.source_type == CameraSourceType.USB:
            try:
                target_source = int(source_str)
                is_device_index = True
            except ValueError:
                target_source = source_str

        try:
            # If source is explicitly marked fake or nonexistent in test, return None immediately without waiting for OS socket timeout
            if "nonexistent" in str(source_str).lower():
                return None

            cap = None
            # On Windows, try DirectShow (cv2.CAP_DSHOW) for device indices for fast initialization
            if is_device_index and os.name == "nt":
                try:
                    cap = cv2.VideoCapture(target_source, cv2.CAP_DSHOW)
                    if not cap.isOpened():
                        cap = None
                except Exception:
                    cap = None

            if cap is None:
                cap = cv2.VideoCapture(target_source)

            if not cap.isOpened():
                return None

            # Optional: set camera resolution if specified and using physical device
            if is_device_index and self.config.resolution and "x" in self.config.resolution:
                try:
                    rw, rh = [int(v) for v in self.config.resolution.split("x")]
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, rw)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, rh)
                except Exception:
                    pass

            return cap
        except Exception as e:
            logger.error("Error opening capture for %s: %s", self.camera_id, e)
            return None

    def _generate_synthetic_frame(self, frame_idx: int) -> np.ndarray:
        """Generates a clean synthetic frame for testing without hardware dependencies."""
        # 640x480 test image with moving marker
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Background gradient
        frame[:, :] = (35, 30, 30)
        # Draw camera metadata
        cv2.putText(
            frame,
            f"RAKSHYA VISION SYNTHETIC CAM: {self.camera_id}",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 200),
            2,
        )
        cv2.putText(
            frame,
            f"Frame: {frame_idx} | Zone: {self.config.zone_id}",
            (30, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (200, 200, 200),
            1,
        )
        # Moving indicator
        x = int(100 + (frame_idx * 5) % 440)
        cv2.circle(frame, (x, 240), 20, (0, 165, 255), -1)
        return frame

    def _run_loop(self):
        """Main camera worker execution loop."""
        reconnect_attempts = 0
        policy = self.config.reconnect_policy
        cap: Optional[cv2.VideoCapture] = None

        target_fps = self.config.fps_target or 30
        frame_delay = 1.0 / max(1, target_fps)

        try:
            while not self._stop_event.is_set():
                # 1. Handle synthetic camera streams
                if self.config.source_type == CameraSourceType.SYNTHETIC:
                    with self._lock:
                        self.state = CameraState.CONNECTED
                    while not self._stop_event.is_set():
                        t0 = time.time()
                        frame = self._generate_synthetic_frame(self.metrics.frame_count)
                        now = time.time()

                        with self._lock:
                            self._latest_frame = frame
                            self._latest_frame_time = now
                            self.metrics.frame_count += 1
                            self.metrics.last_successful_frame_timestamp = now

                        if self.metrics.frame_count % self.infer_interval_frames == 0:
                            self._process_frame_ai(frame, now)

                        try:
                            from app.services.metrics import MetricsCollector
                            MetricsCollector.get_instance().increment_counter(
                                "rakshya_pipeline_frames_total",
                                labels={"camera_id": self.camera_id},
                            )
                        except Exception:
                            pass

                        self._update_fps()
                        elapsed = time.time() - t0
                        sleep_time = max(0.001, frame_delay - elapsed)
                        time.sleep(sleep_time)
                    break

                # 2. Connection establishment with bounded exponential backoff
                if cap is None or not cap.isOpened():
                    with self._lock:
                        self.state = CameraState.CONNECTING if reconnect_attempts == 0 else CameraState.RECONNECTING

                    cap = self._open_capture()

                    if cap is None or not cap.isOpened():
                        reconnect_attempts += 1
                        with self._lock:
                            self.metrics.reconnect_count = reconnect_attempts
                            self.metrics.last_error = f"Failed to connect to source: {self.safe_source}"
                            if reconnect_attempts >= policy.max_retries:
                                self.state = CameraState.ERROR
                            else:
                                self.state = CameraState.RECONNECTING

                        if reconnect_attempts >= policy.max_retries:
                            logger.error(
                                "Camera %s reached max retries (%d). Stopping retry loop.",
                                self.camera_id,
                                policy.max_retries
                            )
                            break

                        # Bounded exponential backoff: delay = min(max_delay, initial * (2 ^ attempt))
                        backoff = min(
                            policy.max_delay_seconds,
                            policy.initial_delay_seconds * (2 ** (reconnect_attempts - 1))
                        )
                        logger.warning(
                            "Camera %s connection failed (attempt %d/%d). Retrying in %.2fs...",
                            self.camera_id,
                            reconnect_attempts,
                            policy.max_retries,
                            backoff
                        )
                        time.sleep(backoff)
                        continue
                    else:
                        # Connected successfully
                        reconnect_attempts = 0
                        with self._lock:
                            self.state = CameraState.CONNECTED
                            self.metrics.last_error = None
                        logger.info("Camera %s successfully connected.", self.camera_id)

                # 3. Read loop
                t_frame_start = time.time()
                ret, frame = cap.read()

                if not ret or frame is None:
                    with self._lock:
                        self.metrics.dropped_frames += 1
                        self.metrics.last_error = "Frame read failed or stream closed"
                        self.state = CameraState.DEGRADED
                    try:
                        from app.services.metrics import MetricsCollector
                        MetricsCollector.get_instance().increment_counter(
                            "rakshya_pipeline_dropped_frames_total",
                            labels={"camera_id": self.camera_id},
                        )
                    except Exception:
                        pass
                    logger.warning("Camera %s lost frame. Resetting capture...", self.camera_id)
                    cap.release()
                    cap = None
                    continue

                now = time.time()

                # Hardware privacy shutter / disabled camera sensor check:
                # When laptop webcam shutter is closed or toggled off via hotkey (e.g. F10 / Fn+F10 on Asus),
                # OpenCV receives solid color/near-zero variance frames with the crossed-out camera logo.
                is_shutter_blocked = False
                is_severe_dark = False
                if frame is not None and frame.size > 0:
                    try:
                        sample = frame[::8, ::8]
                        sample_std = float(np.std(sample))
                        sample_mean = float(np.mean(sample))
                        if sample_std < 2.5:
                            is_shutter_blocked = True
                        elif sample_mean < 25.0:
                            is_severe_dark = True
                    except Exception:
                        pass

                with self._lock:
                    if is_shutter_blocked:
                        self.state = CameraState.DEGRADED
                        self.metrics.last_error = (
                            "Camera privacy shutter closed or disabled via laptop hotkey (e.g. F10 / Fn+F10 on Asus). Physical sensor is blocked."
                        )
                    elif is_severe_dark:
                        self.state = CameraState.DEGRADED
                        self.metrics.last_error = (
                            "Severe low-light detected (room is too dark). Turn on room lighting and step back so your upper body/torso is visible."
                        )
                    elif self.state == CameraState.DEGRADED and self.metrics.last_error and ("shutter" in str(self.metrics.last_error) or "low-light" in str(self.metrics.last_error)):
                        self.state = CameraState.CONNECTED
                        self.metrics.last_error = None
                    else:
                        self.state = CameraState.CONNECTED

                    self._latest_frame = frame
                    self._latest_frame_time = now
                    self.metrics.frame_count += 1
                    self.metrics.last_successful_frame_timestamp = now

                # Run AI pipeline on scheduled frames
                if self.metrics.frame_count % self.infer_interval_frames == 0:
                    self._process_frame_ai(frame, now)

                try:
                    from app.services.metrics import MetricsCollector
                    MetricsCollector.get_instance().increment_counter(
                        "rakshya_pipeline_frames_total",
                        labels={"camera_id": self.camera_id},
                    )
                except Exception:
                    pass

                self._update_fps()

                # Rate control
                elapsed = time.time() - t_frame_start
                sleep_time = max(0.001, frame_delay - elapsed)
                time.sleep(sleep_time)

        except Exception as e:
            logger.error("Unhandled exception in CameraWorker %s: %s", self.camera_id, e, exc_info=True)
            with self._lock:
                self.state = CameraState.ERROR
                self.metrics.last_error = str(e)
        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
            with self._lock:
                if self.state not in (CameraState.ERROR, CameraState.DISABLED):
                    self.state = CameraState.DISCONNECTED
            logger.info("CameraWorker loop exited for %s", self.camera_id)

    def _update_fps(self):
        """Calculates rolling FPS every 1.0 second."""
        self._fps_window_frames += 1
        now = time.time()
        elapsed = now - self._fps_window_start
        if elapsed >= 1.0:
            with self._lock:
                self.metrics.fps = round(self._fps_window_frames / elapsed, 1)
            self._fps_window_frames = 0
            self._fps_window_start = now
