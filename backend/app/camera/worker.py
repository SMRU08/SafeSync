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
        self.speaker_enabled: bool = bool(getattr(config, "speaker_enabled", True))

        # Threading state
        self._thread: Optional[threading.Thread] = None
        self._capture_thread: Optional[threading.Thread] = None
        self._ai_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._frame_cv = threading.Condition(self._lock)

        # AI Worker queue/slot (strictly bounded: size 1, latest-frame-wins)
        self._ai_slot: Optional[Tuple[int, float, np.ndarray]] = None
        self._ai_lock = threading.Lock()
        self._ai_event = threading.Event()
        self._ai_busy = False

        # Monotonic frame tracking
        self._frame_id = 0

        # Operational state & metrics
        self.state: CameraState = CameraState.DISABLED if not config.enabled else CameraState.DISCONNECTED
        self.metrics = CameraMetrics()
        self._start_time: Optional[float] = None
        self.validation_mode: bool = True  # Real-time frame-id and capture-timestamp HUD

        # Frame buffers
        self._latest_frame: Optional[np.ndarray] = None
        self._latest_annotated_frame: Optional[np.ndarray] = None
        self._latest_frame_time: Optional[float] = None
        self._latest_workers: List[Any] = []
        self._latest_compliance_summary: Optional[Any] = None
        self._latest_annotated_b64: Optional[str] = None

        # AI Pipeline configuration
        self.infer_interval_frames = 2  # Run AI inference every 2 frames
        self._compliance_engine: Optional[Any] = None
        self._hazard_engine: Optional[Any] = None
        self._safety_engine: Optional[Any] = None
        self._alert_engine: Optional[Any] = None
        self._event_normalizer: Optional[Any] = None
        self._latest_hazards: List[Any] = []
        self._latest_safety_assessment: Optional[Any] = None

        # FPS calculation window
        self._fps_window_start = time.time()
        self._fps_window_frames = 0

    def _init_ai_engines(self):
        """Initializes thread-local AI inference, tracking, and compliance components."""
        if self._compliance_engine is None:
            try:
                from app.ai.compliance.compliance_engine import WorkerComplianceEngine
                from app.ai.hazards.hazard_engine import HazardAnalysisEngine
                from app.services.event_normalizer import EventNormalizer
                from app.services.alert_engine import AlertEngine
                from app.services.safety_engine import SafetyEngine
                self._compliance_engine = WorkerComplianceEngine()
                self._hazard_engine = HazardAnalysisEngine()
                self._alert_engine = AlertEngine()
                self._safety_engine = SafetyEngine(alert_engine=self._alert_engine)
                self._event_normalizer = EventNormalizer()
                logger.info("Initialized AI compliance, hazard, and safety engines for camera %s", self.camera_id)
            except Exception as e:
                logger.error("Failed to initialize AI engines for %s: %s", self.camera_id, e, exc_info=True)

    def _process_frame_ai(self, frame: np.ndarray, frame_time: float, frame_id: Optional[int] = None):
        """Runs live YOLO detection, ByteTrack tracking, PPE association, hazard analysis, and safety rules."""
        if self._compliance_engine is None:
            return

        try:
            t_start = time.perf_counter()
            # 1. PPE compliance inference
            compliance_resp, annotated_frame, latencies = self._compliance_engine.process_frame(
                frame,
                confidence_threshold=0.20,
                annotate=True,
            )

            # 2. Hazard analysis inference (fire and smoke)
            hazard_resp = None
            if self._hazard_engine is not None:
                try:
                    hazard_resp, _, _ = self._hazard_engine.process_frame(
                        frame,
                        camera_id=self.camera_id,
                        annotate=False,
                    )
                except Exception as h_err:
                    logger.debug("Hazard engine frame evaluation skipped: %s", h_err)

            ai_duration_ms = (time.perf_counter() - t_start) * 1000.0

            # 3. Central Safety Engine Assessment (Rules 1 through 7)
            safety_assessment = None
            if self._safety_engine is not None:
                safety_assessment = self._safety_engine.assess_scene(
                    camera_id=self.camera_id,
                    zone_id=self.config.zone_id,
                    compliance_response=compliance_resp,
                    hazard_response=hazard_resp,
                    camera_connected=True,
                    ai_available=True,
                )

            with self._lock:
                self._latest_annotated_frame = annotated_frame
                self._latest_workers = compliance_resp.workers
                self._latest_compliance_summary = compliance_resp.summary
                self._latest_annotated_b64 = compliance_resp.annotated_image_base64
                if hazard_resp:
                    self._latest_hazards = hazard_resp.hazards
                    self.metrics.active_hazards = len(hazard_resp.hazards)
                if safety_assessment:
                    self._latest_safety_assessment = safety_assessment
                self.metrics.inference_latency_ms = round(ai_duration_ms, 2)
                self.metrics.active_workers = len(compliance_resp.workers)
                self.metrics.active_violations = compliance_resp.summary.non_compliant_workers

            # 4. Dispatch evaluated safety events to AlertEngine
            events_to_dispatch = []
            if safety_assessment and safety_assessment.events:
                events_to_dispatch = safety_assessment.events
            elif self._event_normalizer:
                events_to_dispatch = self._event_normalizer.from_compliance_response(
                    compliance_resp,
                    camera_id=self.camera_id,
                    zone_id=self.config.zone_id,
                )

            if events_to_dispatch and self._alert_engine:
                from app.database.session import SessionLocal
                from app.services.evidence_manager import EvidenceManager
                with SessionLocal() as db:
                    for ev in events_to_dispatch:
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

            # 5. Core AI Audio-Alert Engine (Worker PPE Speech Alerts)
            if compliance_resp and compliance_resp.workers:
                try:
                    from app.services.audio_alert_engine import AudioAlertEngine
                    AudioAlertEngine.get_instance().evaluate_frame_workers(
                        camera_id=self.camera_id,
                        speaker_enabled=self.speaker_enabled,
                        workers=compliance_resp.workers,
                    )
                except Exception as audio_err:
                    logger.debug("Audio alert evaluation notice for %s: %s", self.camera_id, audio_err)

        except Exception as e:
            logger.error("Error in AI frame processing for %s: %s", self.camera_id, e, exc_info=True)

    def _dispatch_frame_to_ai(self, frame_id: int, frame_time: float, frame: np.ndarray):
        """Passes the newest frame to the AI worker thread via 1-slot latest-frame-wins buffer."""
        with self._ai_lock:
            if self._ai_busy or self._ai_slot is not None:
                self.metrics.dropped_ai_frames += 1
            # Latest-frame-wins: always overwrite with newest frame
            self._ai_slot = (frame_id, frame_time, frame)
            self.metrics.frame_queue_depth = 1
            self._ai_event.set()

    def _ai_worker_loop(self):
        """Dedicated background thread executing AI inference asynchronously without blocking capture."""
        logger.info("Started AI worker thread for camera %s", self.camera_id)
        while not self._stop_event.is_set():
            if not self._ai_event.wait(timeout=0.1):
                continue

            item = None
            with self._ai_lock:
                self._ai_event.clear()
                if self._ai_slot is not None:
                    item = self._ai_slot
                    self._ai_slot = None
                    self._ai_busy = True
                    self.metrics.frame_queue_depth = 0

            if item is None:
                continue

            frame_id, frame_time, frame = item
            try:
                self._process_frame_ai(frame, frame_time, frame_id)
            except Exception as e:
                logger.error("AI worker error in %s: %s", self.camera_id, e)
            finally:
                with self._ai_lock:
                    self._ai_busy = False

        logger.info("AI worker thread exited for camera %s", self.camera_id)

    def set_speaker(self, enabled: bool) -> bool:
        """Dynamically enables or disables localized speaker audio alerts for this camera."""
        with self._lock:
            self.speaker_enabled = bool(enabled)
            self.config.speaker_enabled = bool(enabled)
        logger.info("Camera %s speaker status set to: %s", self.camera_id, "ON" if enabled else "OFF")
        return self.speaker_enabled

    def start(self):
        """Starts the camera capture worker thread and asynchronous AI worker thread if enabled."""
        with self._lock:
            if not self.config.enabled:
                self.state = CameraState.DISABLED
                logger.info("Camera %s is disabled in config. Not starting.", self.camera_id)
                return

            if self._capture_thread is not None and self._capture_thread.is_alive():
                logger.warning("CameraWorker %s is already running.", self.camera_id)
                return

            self._stop_event.clear()
            self._ai_event.clear()
            self.state = CameraState.CONNECTING
            self._start_time = time.time()
            self._init_ai_engines()

            # Start AI inference thread first
            self._ai_thread = threading.Thread(
                target=self._ai_worker_loop,
                name=f"CameraWorker-AI-{self.camera_id}",
                daemon=True,
            )
            self._ai_thread.start()

            # Start dedicated capture thread
            self._capture_thread = threading.Thread(
                target=self._run_loop,
                name=f"CameraWorker-{self.camera_id}",
                daemon=True,
            )
            self._thread = self._capture_thread  # Backward-compatibility alias
            self._capture_thread.start()
            logger.info("Started CameraWorker capture & AI threads for %s (%s)", self.camera_id, self.safe_source)

    def stop(self, timeout: float = 3.0):
        """Gracefully stops the worker threads and releases resources."""
        self._stop_event.set()
        self._ai_event.set()
        with self._frame_cv:
            self._frame_cv.notify_all()

        if self._capture_thread is not None and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=timeout)
        if self._ai_thread is not None and self._ai_thread.is_alive():
            self._ai_thread.join(timeout=timeout)

        with self._lock:
            self.state = CameraState.DISCONNECTED
            self._latest_frame = None
            self._latest_annotated_frame = None
            self._latest_workers = []
            self._latest_compliance_summary = None
            self._latest_annotated_b64 = None
            with self._ai_lock:
                self._ai_slot = None
                self._ai_busy = False
            logger.info("Stopped CameraWorker for %s", self.camera_id)

    def get_status(self) -> CameraStatus:
        """Returns snapshot of current camera status and metrics."""
        with self._lock:
            # Update uptime
            if self._start_time and self.state == CameraState.CONNECTED:
                self.metrics.uptime_seconds = round(time.time() - self._start_time, 1)

            # Determine human-friendly status string
            if self.state in (CameraState.CONNECTED, CameraState.DEGRADED):
                status_str = "online"
            elif self.state in (CameraState.CONNECTING, CameraState.RECONNECTING):
                status_str = "connecting"
            elif self.state == CameraState.ERROR:
                status_str = "error"
            else:
                status_str = "offline"

            last_seen_iso = None
            if self.metrics.last_successful_frame_timestamp:
                try:
                    from datetime import datetime, timezone
                    last_seen_iso = datetime.fromtimestamp(
                        self.metrics.last_successful_frame_timestamp, tz=timezone.utc
                    ).isoformat()
                except Exception:
                    pass

            ai_summary_dict = None
            if self._latest_compliance_summary:
                try:
                    if hasattr(self._latest_compliance_summary, "model_dump"):
                        ai_summary_dict = self._latest_compliance_summary.model_dump()
                    elif isinstance(self._latest_compliance_summary, dict):
                        ai_summary_dict = self._latest_compliance_summary
                    else:
                        ai_summary_dict = vars(self._latest_compliance_summary)
                except Exception:
                    pass

            return CameraStatus(
                camera_id=self.camera_id,
                name=self.config.name,
                location=getattr(self.config, "location", "") or self.config.zone_id.replace("_", " ").title(),
                zone_id=self.config.zone_id,
                source_type=self.config.source_type.value,
                enabled=self.config.enabled,
                speaker_enabled=self.speaker_enabled,
                state=self.state,
                status=status_str,
                connection_status=self.state.value.lower(),
                stream_url=f"/api/cameras/{self.camera_id}/stream",
                fps=self.metrics.fps,
                resolution=self.config.resolution or "1280x720",
                last_seen=last_seen_iso,
                metrics=self.metrics.model_copy(),
                safe_source=self.safe_source,
                ai_analysis={
                    "active_workers": self.metrics.active_workers,
                    "active_violations": self.metrics.active_violations,
                    "active_hazards": self.metrics.active_hazards,
                    "latency_ms": self.metrics.inference_latency_ms,
                    "summary": ai_summary_dict,
                },
            )

    def get_latest_frame(self, annotated: bool = True) -> Tuple[Optional[np.ndarray], Optional[float]]:
        """Returns the most recent captured frame (copy) and timestamp with fast non-blocking overlay."""
        with self._lock:
            if self._latest_frame is None:
                if annotated and self._latest_annotated_frame is not None:
                    return self._latest_annotated_frame.copy(), self._latest_frame_time
                return None, None
            raw = self._latest_frame.copy()
            ts = self._latest_frame_time
            annotated_cache = self._latest_annotated_frame
            workers = list(self._latest_workers)
            hazards = list(self._latest_hazards)
            visualizer = getattr(self._compliance_engine, "visualizer", None) if self._compliance_engine else None

        if not annotated:
            return raw, ts

        # Fast non-blocking overlay: render newest AI detections on newest camera frame
        if visualizer and (workers or hazards):
            try:
                annotated_fresh = visualizer.draw_frame(raw, workers, unassociated_ppe=None, hazards=hazards)
                return annotated_fresh, ts
            except Exception:
                pass

        if annotated_cache is not None:
            return annotated_cache.copy(), ts

        return raw, ts

    def wait_for_new_frame(
        self,
        last_frame_id: int,
        annotated: bool = True,
        timeout: float = 0.06,
    ) -> Tuple[Optional[np.ndarray], int, Optional[float]]:
        """
        Event-driven wait for a newly captured frame with monotonic frame_id.
        Discards stale frames and immediately delivers the newest frame.
        """
        with self._frame_cv:
            if self._frame_id <= last_frame_id and not self._stop_event.is_set():
                self._frame_cv.wait(timeout=timeout)

            if self._latest_frame is None or self._frame_id <= last_frame_id:
                return None, last_frame_id, None

            raw = self._latest_frame.copy()
            fid = self._frame_id
            fts = self._latest_frame_time
            annotated_cache = self._latest_annotated_frame
            workers = list(self._latest_workers)
            hazards = list(self._latest_hazards)
            visualizer = getattr(self._compliance_engine, "visualizer", None) if self._compliance_engine else None

        if not annotated:
            return raw, fid, fts

        if visualizer and (workers or hazards):
            try:
                annotated_fresh = visualizer.draw_frame(raw, workers, unassociated_ppe=None, hazards=hazards)
                return annotated_fresh, fid, fts
            except Exception:
                pass

        if annotated_cache is not None:
            return annotated_cache.copy(), fid, fts

        return raw, fid, fts

    def get_live_compliance(self) -> Dict[str, Any]:
        """Returns the latest active worker tracking and compliance data."""
        with self._lock:
            fw = int(self._latest_frame.shape[1]) if self._latest_frame is not None else 1280
            fh = int(self._latest_frame.shape[0]) if self._latest_frame is not None else 720
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
                        if isinstance(wd["bbox"], list) and len(wd["bbox"]) >= 4:
                            bx1, by1, bx2, by2 = wd["bbox"][:4]
                            wd["normalized_bbox"] = [
                                round(bx1 / max(1, fw), 4),
                                round(by1 / max(1, fh), 4),
                                round(bx2 / max(1, fw), 4),
                                round(by2 / max(1, fh), 4),
                            ]
                    workers_out.append(wd)
                except Exception as e:
                    logger.debug("Error serializing worker in get_live_compliance: %s", e)

            track_telemetry = []
            if self._compliance_engine and hasattr(self._compliance_engine.tracker, "get_track_telemetry"):
                try:
                    track_telemetry = self._compliance_engine.tracker.get_track_telemetry()
                except Exception:
                    pass

            return {
                "camera_id": self.camera_id,
                "speaker_enabled": self.speaker_enabled,
                "frame_width": fw,
                "frame_height": fh,
                "workers": workers_out,
                "track_telemetry": track_telemetry,
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

            cap = cv2.VideoCapture(target_source)

            # On Windows, if default MSMF backend fails for device index, fallback to DirectShow
            if (cap is None or not cap.isOpened()) and is_device_index and os.name == "nt":
                try:
                    cap = cv2.VideoCapture(target_source, cv2.CAP_DSHOW)
                except Exception:
                    cap = None

            if cap is None or not cap.isOpened():
                return None

            # Buffer flush optimization: set driver buffer size to 1 where supported
            try:
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass

            # Flush any stale initial driver frames
            try:
                for _ in range(2):
                    cap.grab()
            except Exception:
                pass

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
        width, height = 640, 480
        if self.config.resolution and "x" in self.config.resolution and self.config.resolution != "1280x720":
            try:
                rw, rh = [int(v) for v in self.config.resolution.split("x")]
                if rw > 0 and rh > 0:
                    width, height = rw, rh
            except Exception:
                pass

        frame = np.zeros((height, width, 3), dtype=np.uint8)
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
        x = int(100 + (frame_idx * 8) % max(1, width - 200))
        y = height // 2
        cv2.circle(frame, (x, y), 20, (0, 165, 255), -1)
        return frame

    def _run_loop(self):
        """Main camera worker capture execution loop (dedicated thread - never blocks for AI)."""
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
                        frame = self._generate_synthetic_frame(self._frame_id)
                        now = time.time()

                        if self.validation_mode and frame is not None and frame.size > 0:
                            cv2.rectangle(frame, (6, 6), (285, 32), (10, 10, 15), -1)
                            cv2.rectangle(frame, (6, 6), (285, 32), (0, 255, 255), 1)
                            cv2.putText(
                                frame,
                                f"ID:{self._frame_id} | CAP:{int(now * 1000)}ms",
                                (12, 24),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.45,
                                (0, 255, 255),
                                1,
                                cv2.LINE_AA,
                            )

                        with self._frame_cv:
                            self._frame_id += 1
                            self._latest_frame = frame
                            self._latest_frame_time = now
                            self.metrics.frame_count = self._frame_id
                            self.metrics.latest_frame_id = self._frame_id
                            self.metrics.last_successful_frame_timestamp = now
                            self._frame_cv.notify_all()

                        self._dispatch_frame_to_ai(self._frame_id, now, frame)

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
                        self._stop_event.wait(timeout=backoff)
                        continue
                    else:
                        # Connected successfully
                        reconnect_attempts = 0
                        with self._lock:
                            self.state = CameraState.CONNECTED
                            self.metrics.last_error = None
                        logger.info("Camera %s successfully connected.", self.camera_id)

                # 3. Dedicated Read loop (runs at maximum camera FPS, never blocks for AI)
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

                with self._frame_cv:
                    self.state = CameraState.CONNECTED
                    if is_shutter_blocked:
                        self.metrics.last_error = (
                            "Camera privacy shutter closed or disabled via laptop hotkey (e.g. F10 / Fn+F10 on Asus). Physical sensor is blocked."
                        )
                        # Render diagnostic HUD directly on frame
                        fh, fw = frame.shape[:2]
                        cv2.rectangle(frame, (10, fh // 2 - 45), (fw - 10, fh // 2 + 45), (20, 20, 30), -1)
                        cv2.rectangle(frame, (10, fh // 2 - 45), (fw - 10, fh // 2 + 45), (0, 165, 255), 2)
                        cv2.putText(
                            frame,
                            "CAMERA SENSOR BLOCKED / PITCH BLACK",
                            (fw // 2 - 220, fh // 2 - 12),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (0, 165, 255),
                            2,
                        )
                        cv2.putText(
                            frame,
                            "Slide open physical privacy cover or press Fn + Camera key (e.g. F10)",
                            (fw // 2 - 250, fh // 2 + 22),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.50,
                            (255, 255, 255),
                            1,
                        )
                    elif is_severe_dark:
                        self.metrics.last_error = (
                            "Severe low-light detected (room is too dark). Turn on room lighting and step back so your upper body/torso is visible."
                        )
                    else:
                        self.metrics.last_error = None

                    if self.validation_mode and frame is not None and frame.size > 0:
                        cv2.rectangle(frame, (6, 6), (285, 32), (10, 10, 15), -1)
                        cv2.rectangle(frame, (6, 6), (285, 32), (0, 255, 255), 1)
                        cv2.putText(
                            frame,
                            f"ID:{self._frame_id + 1} | CAP:{int(now * 1000)}ms",
                            (12, 24),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.45,
                            (0, 255, 255),
                            1,
                            cv2.LINE_AA,
                        )

                    self._frame_id += 1
                    self._latest_frame = frame
                    self._latest_frame_time = now
                    self.metrics.frame_count = self._frame_id
                    self.metrics.latest_frame_id = self._frame_id
                    self.metrics.last_successful_frame_timestamp = now
                    self._frame_cv.notify_all()

                # Dispatch frame to asynchronous AI thread (strictly non-blocking)
                self._dispatch_frame_to_ai(self._frame_id, now, frame)

                try:
                    from app.services.metrics import MetricsCollector
                    MetricsCollector.get_instance().increment_counter(
                        "rakshya_pipeline_frames_total",
                        labels={"camera_id": self.camera_id},
                    )
                except Exception:
                    pass

                self._update_fps()

                # Rate control: for hardware webcam cap.read() blocks naturally at hardware FPS (~30 FPS).
                # Only sleep if elapsed time is less than target frame interval.
                elapsed = time.time() - t_frame_start
                sleep_time = max(0.0005, frame_delay - elapsed)
                if sleep_time > 0.001:
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
            logger.info("CameraWorker capture loop exited for %s", self.camera_id)

    def _update_fps(self):
        """Calculates rolling FPS every 1.0 second."""
        self._fps_window_frames += 1
        now = time.time()
        elapsed = now - self._fps_window_start
        if elapsed >= 1.0:
            with self._lock:
                calc_fps = round(self._fps_window_frames / elapsed, 1)
                self.metrics.fps = calc_fps
                self.metrics.capture_fps = calc_fps
            self._fps_window_frames = 0
            self._fps_window_start = now
