"""
utils.py — RAKSHYA VISION Phase 4
Drawing utilities, color palettes, image conversion, and video codec helpers.
Strictly decoupled from violation/compliance labels.
"""

import time
from typing import List, Tuple, Dict, Optional, Any
import numpy as np
import cv2
try:
    from app.ai.detection.schemas import DetectionObject, BoundingBox
except ImportError:
    from backend.app.ai.detection.schemas import DetectionObject, BoundingBox

# High-visibility BGR color palette for 7 canonical classes
CLASS_COLORS_BGR: Dict[int, Tuple[int, int, int]] = {
    0: (255, 140, 0),     # person: Deep Sky Blue / Orange (BGR: 255, 140, 0)
    1: (0, 215, 255),     # helmet: Bright Yellow / Gold (BGR: 0, 215, 255)
    2: (0, 255, 127),     # safety_vest: Spring Green / High-Vis (BGR: 0, 255, 127)
    3: (238, 130, 238),   # gloves: Violet (BGR: 238, 130, 238)
    4: (42, 42, 165),     # safety_footwear: Brown / Dark Khaki (BGR: 42, 42, 165)
    5: (0, 69, 255),      # fire: Bright Orange-Red (BGR: 0, 69, 255)
    6: (169, 169, 169),   # smoke: Medium Gray (BGR: 169, 169, 169)
}

DEFAULT_COLOR: Tuple[int, int, int] = (0, 255, 0)


def get_class_color(class_id: int) -> Tuple[int, int, int]:
    """Returns color for a given class ID."""
    return CLASS_COLORS_BGR.get(class_id, DEFAULT_COLOR)


def draw_detections(
    frame: np.ndarray,
    detections: List[DetectionObject],
    fps: Optional[float] = None,
    latency_ms: Optional[float] = None,
    show_fps: bool = True,
    show_timestamp: bool = True,
    title: str = "RAKSHYA VISION — AI Safety Monitor",
) -> np.ndarray:
    """
    Draws bounding boxes and labels on an OpenCV BGR frame.
    Format: '[class_name] [confidence:.2f]'
    No violation or compliance text is drawn (deferred to Phase 5).
    """
    canvas = frame.copy()
    h, w = canvas.shape[:2]

    for det in detections:
        color = get_class_color(det.class_id)
        x1, y1 = int(round(det.bbox.x1)), int(round(det.bbox.y1))
        x2, y2 = int(round(det.bbox.x2)), int(round(det.bbox.y2))

        # Clamp to frame boundary
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))
        x2 = max(0, min(x2, w - 1))
        y2 = max(0, min(y2, h - 1))

        # Draw bounding box
        thickness = max(2, int(min(w, h) / 300))
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, thickness)

        # Label: '[class_name] [confidence:.2f]'
        label = f"{det.class_name} {det.confidence:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.4, min(w, h) / 1000.0)
        label_thickness = max(1, int(thickness / 2))

        (tw, th), baseline = cv2.getTextSize(label, font, font_scale, label_thickness)

        # Label background
        label_y1 = max(0, y1 - th - baseline - 4)
        label_y2 = y1
        label_x2 = min(w, x1 + tw + 6)
        cv2.rectangle(canvas, (x1, label_y1), (label_x2, label_y2), color, -1)

        # Text in contrasting black or white
        text_color = (0, 0, 0) if sum(color) > 380 else (255, 255, 255)
        cv2.putText(
            canvas,
            label,
            (x1 + 3, y1 - baseline - 2),
            font,
            font_scale,
            text_color,
            label_thickness,
            cv2.LINE_AA,
        )

    # Header Overlay (Title, FPS, Latency)
    if show_fps or show_timestamp:
        overlay_y = 25
        # Top banner background bar
        cv2.rectangle(canvas, (0, 0), (w, 35), (20, 20, 20), -1)

        # Title
        cv2.putText(
            canvas,
            title,
            (10, overlay_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        # Metrics text (Right-aligned or beside title)
        info_parts = []
        if show_fps and fps is not None:
            info_parts.append(f"FPS: {fps:.1f}")
        if latency_ms is not None:
            info_parts.append(f"Inf: {latency_ms:.1f}ms")
        info_parts.append(f"Detections: {len(detections)}")

        info_text = " | ".join(info_parts)
        (itw, _), _ = cv2.getTextSize(info_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        info_x = max(10, w - itw - 15)
        cv2.putText(
            canvas,
            info_text,
            (info_x, overlay_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )

    return canvas


def bytes_to_bgr_image(image_bytes: bytes) -> Optional[np.ndarray]:
    """Decodes raw image bytes (e.g. from HTTP upload) into an OpenCV BGR ndarray."""
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


def bgr_to_jpeg_bytes(image: np.ndarray, quality: int = 90) -> bytes:
    """Encodes an OpenCV BGR ndarray to JPEG bytes."""
    success, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not success:
        raise RuntimeError("Failed to encode image to JPEG")
    return encoded.tobytes()


def resolve_video_writer(
    output_path: str,
    fps: float,
    width: int,
    height: int,
) -> Tuple[cv2.VideoWriter, str]:
    """
    Creates an OpenCV VideoWriter with automatic codec selection and fallback.
    Tries 'mp4v' for MP4, falls back to 'avc1' or 'XVID' if needed.
    """
    codecs_to_try = [
        ("mp4v", output_path),
        ("avc1", output_path),
        ("XVID", output_path.rsplit(".", 1)[0] + ".avi"),
    ]

    last_error = None
    for fourcc_str, out_file in codecs_to_try:
        try:
            fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
            writer = cv2.VideoWriter(out_file, fourcc, fps, (width, height))
            if writer.isOpened():
                return writer, out_file
            writer.release()
        except Exception as e:
            last_error = e

    raise RuntimeError(
        f"Failed to initialize VideoWriter for resolution {width}x{height} at {fps} FPS. Error: {last_error}"
    )
