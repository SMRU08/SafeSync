"""
detector.py — SafeSync Phase 4
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

    def __init__(self, model_loader: Optional[ModelLoader] = None, model_type: str = "ppe"):
        self.model_type = model_type.lower()
        self.loader = model_loader or ModelLoader.get_instance()
        self.config = self.loader.config.get("inference", {})
        self.default_conf = float(self.config.get("confidence_threshold", 0.20))
        self.default_iou = float(self.config.get("iou_threshold", 0.45))
        self.default_imgsz = int(self.config.get("image_size", 384))
        raw_class_confs = self.config.get("class_confidence_thresholds", {})
        self.class_conf_thresholds = {
            str(k).lower(): float(v) for k, v in raw_class_confs.items()
        } if isinstance(raw_class_confs, dict) else {}

        # Augment with ModelRegistry operating thresholds
        try:
            try:
                from app.ai.detection.model_registry import ModelRegistry
            except ImportError:
                from backend.app.ai.detection.model_registry import ModelRegistry
            reg_info = ModelRegistry.get_instance().get_model_info(self.model_type)
            if reg_info and "operating_thresholds" in reg_info:
                for k, v in reg_info["operating_thresholds"].items():
                    if k.lower() not in self.class_conf_thresholds:
                        self.class_conf_thresholds[k.lower()] = float(v)
        except Exception as e:
            log.debug("Registry threshold lookup skipped: %s", e)

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

    @staticmethod
    def _calc_iou(b1: List[float], b2: List[float]) -> float:
        """Calculates Intersection-over-Union between two [x1, y1, x2, y2] boxes."""
        xA = max(b1[0], b2[0])
        yA = max(b1[1], b2[1])
        xB = min(b1[2], b2[2])
        yB = min(b1[3], b2[3])
        inter_area = max(0.0, xB - xA) * max(0.0, yB - yA)
        a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
        a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
        union_area = a1 + a2 - inter_area
        return inter_area / max(1e-6, union_area)

    @staticmethod
    def _validate_and_clamp_bbox(
        coords: List[float],
        img_w: int,
        img_h: int,
        class_name: str = "",
    ) -> Optional[BoundingBox]:
        """
        Clamps bounding box to frame boundaries and rejects invalid/degenerate boxes.
        Applies geometric constraints (minimum size and aspect ratios) tailored to class.
        """
        if len(coords) < 4:
            return None

        x1 = max(0.0, min(float(coords[0]), float(img_w - 1)))
        y1 = max(0.0, min(float(coords[1]), float(img_h - 1)))
        x2 = max(x1 + 1.0, min(float(coords[2]), float(img_w)))
        y2 = max(y1 + 1.0, min(float(coords[3]), float(img_h)))

        box_w = x2 - x1
        box_h = y2 - y1

        low_name = class_name.lower()
        if low_name == "person":
            # Person boxes: min width 15px, min height 25px, area >= 375px
            if box_w < 15.0 or box_h < 25.0:
                return None
            # Reject extreme degenerate aspect ratios (e.g. razor-thin horizontal or vertical artifacts)
            aspect = box_w / max(1.0, box_h)
            if aspect > 3.0 or aspect < 0.12:
                return None
        else:
            # PPE items: min width 8px, min height 8px
            if box_w < 8.0 or box_h < 8.0:
                return None

        return BoundingBox(
            x1=round(x1, 2),
            y1=round(y1, 2),
            x2=round(x2, 2),
            y2=round(y2, 2),
        )

    def detect_image(
        self,
        image_input: Union[str, np.ndarray, bytes],
        conf: Optional[float] = None,
        iou: Optional[float] = None,
        imgsz: Optional[int] = None,
        classes_filter: Optional[List[str]] = None,
        annotate: bool = False,
        apply_class_thresholds: bool = True,
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
            apply_class_thresholds: Whether to enforce per-class confidence thresholds.

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

        # Determine predict confidence: predict at minimum required confidence
        pred_conf = conf_thresh
        if apply_class_thresholds and self.class_conf_thresholds:
            min_class_conf = min(self.class_conf_thresholds.values())
            pred_conf = min(conf_thresh, min_class_conf)

        # 3. Execute inference
        model = self.loader.model
        device = self.loader.device

        # Enable FP16 half-precision on GPU to stabilize latency and accelerate Tensor Cores
        use_half = False
        if str(device).lower() not in ("cpu", ""):
            use_half = True

        t0 = time.perf_counter()
        results = model.predict(
            source=frame,
            conf=pred_conf,
            iou=iou_thresh,
            imgsz=inference_size,
            device=device,
            half=use_half,
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

                    # Model class routing
                    low_name = cls_name.lower()
                    if self.model_type == "hazards":
                        if low_name not in ("fire", "smoke"):
                            continue

                    # Per-class confidence filtering
                    req_conf = conf_thresh
                    if apply_class_thresholds and self.class_conf_thresholds:
                        class_min = self.class_conf_thresholds.get(low_name)
                        if class_min is not None:
                            if conf is None or conf == self.default_conf:
                                req_conf = class_min
                            else:
                                req_conf = max(conf, class_min)

                    if score < req_conf:
                        continue

                    # Optional class filtering
                    if filter_set and low_name not in filter_set:
                        continue

                    coords = box.xyxy[0].tolist()
                    clamped_bbox = self._validate_and_clamp_bbox(coords, w, h, low_name)
                    if clamped_bbox is None:
                        continue

                    det = DetectionObject(
                        class_id=cls_id,
                        class_name=cls_name,
                        confidence=round(score, 4),
                        bbox=clamped_bbox,
                    )
                    detections.append(det)
                    class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

        # 4b. Ensure person recall for walking, multi-person, close-up, and non-standard silhouettes:
        # Only relevant for the PPE pipeline; merges primary PPE detections with COCO person detector via IoU NMS
        if self.model_type == "ppe" and (filter_set is None or "person" in filter_set):
            p_model = self._get_person_model()
            if p_model is not None:
                try:
                    p_results = p_model.predict(
                        source=frame,
                        conf=max(0.20, conf_thresh),
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
                                clamped_bbox = self._validate_and_clamp_bbox(coords, w, h, "person")
                                if clamped_bbox is None:
                                    continue

                                # Check overlap with already detected persons (IoU NMS merge)
                                p_box_arr = [clamped_bbox.x1, clamped_bbox.y1, clamped_bbox.x2, clamped_bbox.y2]
                                matched_idx = -1
                                for idx, existing_det in enumerate(detections):
                                    if existing_det.class_name.lower() == "person":
                                        eb = existing_det.bbox
                                        e_arr = [eb.x1, eb.y1, eb.x2, eb.y2]
                                        if self._calc_iou(p_box_arr, e_arr) >= 0.45:
                                            matched_idx = idx
                                            break

                                if matched_idx >= 0:
                                    # If the base COCO model has higher confidence or better coverage, update
                                    if score > detections[matched_idx].confidence:
                                        detections[matched_idx].confidence = round(score, 4)
                                        detections[matched_idx].bbox = clamped_bbox
                                else:
                                    # New person detected (e.g. walking worker or second person missed by primary model)
                                    det = DetectionObject(
                                        class_id=0,
                                        class_name="person",
                                        confidence=round(score, 4),
                                        bbox=clamped_bbox,
                                    )
                                    detections.append(det)
                                    class_counts["person"] = class_counts.get("person", 0) + 1
                except Exception as p_err:
                    log.debug("Multi-person recall detection error: %s", p_err)

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
