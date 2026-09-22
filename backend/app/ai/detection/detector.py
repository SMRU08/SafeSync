"""
detector.py — RAKSHYA VISION Phase 4
Core object detector for single images and frames.
Executes YOLO inference, parses bounding boxes, applies confidence/class filtering,
and returns structured DetectionObject schemas.
"""

import os
import time
import logging
from typing import List, Optional, Union, Dict, Tuple, Any
import numpy as np
import cv2

try:
    from app.ai.detection.model_loader import ModelLoader
    from app.ai.detection.schemas import DetectionObject, BoundingBox, ImageDetectionResponse
    from app.ai.detection.utils import draw_detections, bytes_to_bgr_image
except ImportError:
    from backend.app.ai.detection.model_loader import ModelLoader
    from backend.app.ai.detection.schemas import DetectionObject, BoundingBox, ImageDetectionResponse
    from backend.app.ai.detection.utils import draw_detections, bytes_to_bgr_image

log = logging.getLogger(__name__)


class Detector:
    """High-level safety object detector using the trained Phase 3 YOLO model."""

    def __init__(self, model_loader: Optional[ModelLoader] = None):
        self.loader = model_loader or ModelLoader.get_instance()
        self.config = self.loader.config.get("inference", {})
        self.default_conf = float(self.config.get("confidence_threshold", 0.20))
        self.default_iou = float(self.config.get("iou_threshold", 0.45))
        self.default_imgsz = int(self.config.get("image_size", 384))
        self._person_model = None

    def _get_person_model(self):
        """Loads lightweight base detector for person recall when specialized model misses portrait/webcam silhouettes."""
        if self._person_model is None:
            try:
                from ultralytics import YOLO
                root_backend = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                w_path = os.path.join(root_backend, "yolov8n.pt")
                if not os.path.isfile(w_path):
                    w_path = "yolov8n.pt"
                self._person_model = YOLO(w_path)
            except Exception as e:
                log.debug("Base person detector unavailable: %s", e)
        return self._person_model

    def detect_image(
        self,
        image_input: Union[str, np.ndarray, bytes],
        conf: Optional[float] = None,
        iou: Optional[float] = None,
        imgsz: Optional[int] = None,
        classes_filter: Optional[List[str]] = None,
        annotate: bool = False,
    ) -> Tuple[ImageDetectionResponse, Optional[np.ndarray]]:
        """
        Runs object detection on an image input.

        Args:
            image_input: File path (str), BGR ndarray, or raw bytes.
            conf: Minimum confidence threshold (defaults to configs/detection.yaml).
            iou: NMS IoU threshold.
            imgsz: Inference image size.
            classes_filter: Optional list of class names to include.
            annotate: Whether to return an annotated BGR image.

        Returns:
            Tuple of (ImageDetectionResponse, annotated_bgr_image or None)
        """
        # 1. Resolve and validate image
        frame = self._resolve_image(image_input)
        if frame is None or frame.size == 0:
            raise ValueError("Invalid or corrupted image input. Could not decode into BGR array.")

        h, w = frame.shape[:2]

        # 2. Resolve parameters
        conf_thresh = conf if conf is not None else self.default_conf
        iou_thresh = iou if iou is not None else self.default_iou
        inference_size = imgsz if imgsz is not None else self.default_imgsz

        filter_set = set(c.lower() for c in classes_filter) if classes_filter else None

        # 3. Execute inference
        model = self.loader.model
        device = self.loader.device

        t0 = time.perf_counter()
        results = model.predict(
            source=frame,
            conf=conf_thresh,
            iou=iou_thresh,
            imgsz=inference_size,
            device=device,
            verbose=False,
        )
        latency_ms = (time.perf_counter() - t0) * 1000.0

        # 4. Extract detections
        detections: List[DetectionObject] = []
        class_counts: Dict[str, int] = {}

        if results and len(results) > 0:
            boxes = results[0].boxes
            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    cls_name = model.names.get(cls_id, f"class_{cls_id}")
                    score = float(box.conf[0].item())

                    # Optional class filtering
                    if filter_set and cls_name.lower() not in filter_set:
                        continue

                    coords = box.xyxy[0].tolist()
                    bbox = BoundingBox(
                        x1=round(float(coords[0]), 2),
                        y1=round(float(coords[1]), 2),
                        x2=round(float(coords[2]), 2),
                        y2=round(float(coords[3]), 2),
                    )

                    det = DetectionObject(
                        class_id=cls_id,
                        class_name=cls_name,
                        confidence=round(score, 4),
                        bbox=bbox,
                    )
                    detections.append(det)
                    class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

        # 4b. Ensure person recall for close-up webcam and low-light scenes:
        # If the fine-tuned model didn't detect any person, run fallback person detector
        has_person = any(d.class_name.lower() == "person" for d in detections)
        if not has_person and (filter_set is None or "person" in filter_set):
            p_model = self._get_person_model()
            if p_model is not None:
                try:
                    p_results = p_model.predict(
                        source=frame,
                        conf=max(0.18, conf_thresh),
                        iou=iou_thresh,
                        imgsz=inference_size,
                        device=device,
                        verbose=False,
                    )
                    if p_results and len(p_results) > 0 and p_results[0].boxes is not None:
                        for box in p_results[0].boxes:
                            if int(box.cls[0].item()) == 0:  # Class 0 in COCO is 'person'
                                score = float(box.conf[0].item())
                                coords = box.xyxy[0].tolist()
                                bbox = BoundingBox(
                                    x1=round(float(coords[0]), 2),
                                    y1=round(float(coords[1]), 2),
                                    x2=round(float(coords[2]), 2),
                                    y2=round(float(coords[3]), 2),
                                )
                                det = DetectionObject(
                                    class_id=0,
                                    class_name="person",
                                    confidence=round(score, 4),
                                    bbox=bbox,
                                )
                                detections.append(det)
                                class_counts["person"] = class_counts.get("person", 0) + 1
                except Exception as p_err:
                    log.debug("Fallback person detection error: %s", p_err)

        # 5. Build response
        response = ImageDetectionResponse(
            success=True,
            detections=detections,
            total_detections=len(detections),
            inference_time_ms=round(latency_ms, 2),
            image_width=w,
            image_height=h,
            model_version=self.loader.config.get("model", {}).get("name", "ppe_fire_smoke_v1"),
            device=device,
            class_counts=class_counts,
        )

        annotated_frame = None
        if annotate:
            annotated_frame = draw_detections(
                frame,
                detections,
                latency_ms=latency_ms,
                show_fps=False,
            )

        return response, annotated_frame

    def _resolve_image(self, image_input: Union[str, np.ndarray, bytes]) -> Optional[np.ndarray]:
        """Converts diverse image input formats to a standard OpenCV BGR numpy array."""
        if isinstance(image_input, np.ndarray):
            return image_input
        elif isinstance(image_input, bytes):
            return bytes_to_bgr_image(image_input)
        elif isinstance(image_input, str):
            if not os.path.isfile(image_input):
                raise FileNotFoundError(f"Image file does not exist: {image_input}")
            return cv2.imread(image_input, cv2.IMREAD_COLOR)
        return None
