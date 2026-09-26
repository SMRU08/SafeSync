"""
frame_processor.py — SafeSync Phase 4
Per-frame validation, inference execution, latency measurement, and visual annotation.
Safe handling of corrupted/None frames to prevent pipeline crashes.
"""

import time
import logging
from typing import Tuple, List, Optional
import numpy as np

try:
    from app.ai.detection.detector import Detector
    from app.ai.detection.schemas import DetectionObject
    from app.ai.detection.utils import draw_detections
except ImportError:
    from backend.app.ai.detection.detector import Detector
    from backend.app.ai.detection.schemas import DetectionObject
    from backend.app.ai.detection.utils import draw_detections

log = logging.getLogger(__name__)


class FrameProcessor:
    """Processes individual video or camera frames safely and measures latency."""

    def __init__(self, detector: Optional[Detector] = None):
        self.detector = detector or Detector()
        self._fps_history: List[float] = []
        self._last_time: Optional[float] = None

    def validate_frame(self, frame: Optional[np.ndarray]) -> bool:
        """Validates that frame is a non-empty, multi-dimensional BGR image."""
        if frame is None:
            return False
        if not isinstance(frame, np.ndarray):
            return False
        if frame.size == 0 or len(frame.shape) != 3:
            return False
        h, w, c = frame.shape
        if h <= 0 or w <= 0 or c != 3:
            return False
        return True

    def process_frame(
        self,
        frame: np.ndarray,
        conf: Optional[float] = None,
        iou: Optional[float] = None,
        imgsz: Optional[int] = None,
        classes_filter: Optional[List[str]] = None,
        annotate: bool = True,
    ) -> Tuple[List[DetectionObject], Optional[np.ndarray], float, float]:
        """
        Processes a single frame: validates, runs detector, updates FPS, and annotates.

        Args:
            frame: OpenCV BGR image
            conf: Confidence threshold override
            iou: IoU threshold override
            imgsz: Resolution override
            classes_filter: Optional class name filter
            annotate: Whether to draw bounding boxes on frame

        Returns:
            Tuple of (detections, annotated_frame, inference_latency_ms, current_fps)
        """
        if not self.validate_frame(frame):
            raise ValueError("Invalid frame supplied to process_frame")

        t_start = time.perf_counter()

        # Run detector
        response, _ = self.detector.detect_image(
            image_input=frame,
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            classes_filter=classes_filter,
            annotate=False,
        )

        inference_ms = response.inference_time_ms
        total_frame_time = time.perf_counter() - t_start

        # Calculate instantaneous FPS
        now = time.perf_counter()
        if self._last_time is not None:
            delta = now - self._last_time
            instant_fps = 1.0 / delta if delta > 0 else 0.0
            self._fps_history.append(instant_fps)
            if len(self._fps_history) > 30:
                self._fps_history.pop(0)
            avg_fps = sum(self._fps_history) / len(self._fps_history)
        else:
            avg_fps = 1.0 / total_frame_time if total_frame_time > 0 else 0.0

        self._last_time = now

        annotated_frame = None
        if annotate:
            annotated_frame = draw_detections(
                frame,
                response.detections,
                fps=avg_fps,
                latency_ms=inference_ms,
                show_fps=True,
                show_timestamp=True,
            )

        return response.detections, annotated_frame, inference_ms, avg_fps

    def reset_fps(self):
        """Resets FPS rolling window (useful when starting a new stream or file)."""
        self._fps_history.clear()
        self._last_time = None
