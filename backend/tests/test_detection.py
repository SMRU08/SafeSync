"""
test_detection.py — RAKSHYA VISION Phase 4 Unit & Integration Tests
Tests:
- ModelLoader: checkpoint loading, device resolution, class exposure
- Detector: image inference, bounding boxes, schema validation, confidence filtering
- FrameProcessor: frame validation, corrupted frame handling, FPS tracking
- VideoProcessor: invalid video handling, metadata parsing
- Drawing & utils: draw_detections, BGR colors
- API endpoints: /api/detection/health, /api/detection/image, error handling
"""

import os
import io
import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient

from app.main import app
from app.ai.detection.model_loader import ModelLoader
from app.ai.detection.detector import Detector
from app.ai.detection.frame_processor import FrameProcessor
from app.ai.detection.video_processor import VideoProcessor
from app.ai.detection.schemas import (
    BoundingBox,
    DetectionObject,
    ImageDetectionResponse,
    VideoProcessingOptions,
)
from app.ai.detection.utils import draw_detections, get_class_color, CLASS_COLORS_BGR

client = TestClient(app)


# ─── 1. BoundingBox & Schema Tests ──────────────────────────────────────────

def test_bounding_box_properties():
    box = BoundingBox(x1=10.0, y1=20.0, x2=110.0, y2=220.0)
    assert box.width == 100.0
    assert box.height == 200.0
    assert box.area == 20000.0


def test_detection_object_schema():
    box = BoundingBox(x1=50.0, y1=50.0, x2=150.0, y2=150.0)
    det = DetectionObject(
        class_id=1,
        class_name="helmet",
        confidence=0.885,
        bbox=box,
    )
    assert det.class_id == 1
    assert det.class_name == "helmet"
    assert det.confidence == 0.885
    assert det.bbox.x1 == 50.0


# ─── 2. ModelLoader Tests ───────────────────────────────────────────────────

def test_model_loader_singleton():
    loader1 = ModelLoader.get_instance()
    loader2 = ModelLoader.get_instance()
    assert loader1 is loader2


def test_device_selection_auto_and_cpu():
    loader = ModelLoader.get_instance()
    # 'cpu' must resolve to 'cpu'
    dev = loader.resolve_device("cpu")
    assert dev == "cpu"

    # 'auto' must resolve to 'cpu' (on this CPU machine) or '0'
    dev_auto = loader.resolve_device("auto")
    assert dev_auto in ("cpu", "0")


def test_device_selection_invalid_cuda_fails_clearly():
    loader = ModelLoader.get_instance()
    import torch
    if not torch.cuda.is_available():
        with pytest.raises(RuntimeError) as exc_info:
            loader.resolve_device("cuda")
        assert "not available" in str(exc_info.value).lower()


def test_model_loading_and_canonical_classes():
    loader = ModelLoader.get_instance()
    model = loader.model
    assert model is not None
    classes = loader.classes
    assert len(classes) == 7
    expected = {
        0: "person",
        1: "helmet",
        2: "safety_vest",
        3: "gloves",
        4: "safety_footwear",
        5: "fire",
        6: "smoke",
    }
    for idx, name in expected.items():
        assert classes[idx] == name


# ─── 3. Detector & Image Inference Tests ────────────────────────────────────

def test_detector_inference_on_synthetic_image():
    detector = Detector()
    # Create synthetic test image (384x384 RGB noise)
    dummy_img = np.random.randint(0, 255, (384, 384, 3), dtype=np.uint8)

    response, annotated = detector.detect_image(
        image_input=dummy_img,
        conf=0.1,
        annotate=True,
    )
    assert response.success is True
    assert response.image_width == 384
    assert response.image_height == 384
    assert response.inference_time_ms > 0
    assert annotated is not None
    assert annotated.shape == dummy_img.shape


def test_detector_invalid_image_raises_error():
    detector = Detector()
    with pytest.raises(ValueError):
        detector.detect_image(np.array([]))  # Empty array


def test_detector_confidence_filtering():
    detector = Detector()
    dummy_img = np.random.randint(0, 255, (384, 384, 3), dtype=np.uint8)

    # Ultra-high confidence should yield 0 or very few detections
    resp_high, _ = detector.detect_image(dummy_img, conf=0.999)
    assert len(resp_high.detections) == 0


# ─── 4. FrameProcessor & Validation Tests ───────────────────────────────────

def test_frame_processor_validation():
    processor = FrameProcessor()
    assert processor.validate_frame(None) is False
    assert processor.validate_frame(np.array([])) is False
    assert processor.validate_frame(np.zeros((10, 10), dtype=np.uint8)) is False  # 2D (grayscale)
    assert processor.validate_frame(np.zeros((100, 100, 3), dtype=np.uint8)) is True


def test_frame_processor_execution():
    processor = FrameProcessor()
    frame = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    detections, annotated, lat_ms, fps = processor.process_frame(frame, conf=0.25, annotate=True)
    assert isinstance(detections, list)
    assert annotated is not None
    assert lat_ms > 0
    assert fps >= 0


# ─── 5. Drawing & Color Palette Tests ───────────────────────────────────────

def test_class_colors_exist_for_all_canonical_classes():
    for class_id in range(7):
        color = get_class_color(class_id)
        assert len(color) == 3
        assert all(0 <= c <= 255 for c in color)


def test_draw_detections_does_not_modify_in_place():
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    det = DetectionObject(
        class_id=1,
        class_name="helmet",
        confidence=0.90,
        bbox=BoundingBox(x1=20, y1=20, x2=80, y2=80),
    )
    result = draw_detections(frame, [det], fps=30.0, latency_ms=25.0)
    assert result is not frame
    # Result must have drawn pixels (non-zero)
    assert result.sum() > 0


# ─── 6. VideoProcessor Tests ────────────────────────────────────────────────

def test_video_processor_missing_file_returns_error():
    processor = VideoProcessor()
    result = processor.process_video("non_existent_file.mp4")
    assert result.success is False
    assert "not found" in result.error_message.lower()


# ─── 7. FastAPI API Endpoints Tests ─────────────────────────────────────────

def test_api_detection_health():
    response = client.get("/api/detection/health")
    assert response.status_code == 200
    data = response.json()
    assert data["model_loaded"] is True
    assert data["model_version"] in ["ppe_fire_smoke_v1", "ppe_fire_smoke_v2"]
    assert data["class_count"] == 7
    assert data["status"] == "healthy"
    assert "helmet" in data["classes"].values()


def test_api_detection_image_valid():
    # Create valid synthetic image encoded as JPEG
    img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    _, encoded = cv2.imencode(".jpg", img)
    file_bytes = io.BytesIO(encoded.tobytes())

    response = client.post(
        "/api/detection/image",
        files={"file": ("test.jpg", file_bytes, "image/jpeg")},
        data={"confidence": "0.15"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "detections" in data
    assert data["image_width"] == 200
    assert data["image_height"] == 200
    assert data["inference_time_ms"] > 0


def test_api_detection_image_unsupported_format():
    file_bytes = io.BytesIO(b"fake text content")
    response = client.post(
        "/api/detection/image",
        files={"file": ("test.txt", file_bytes, "text/plain")},
    )
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


def test_api_detection_image_zero_bytes():
    file_bytes = io.BytesIO(b"")
    response = client.post(
        "/api/detection/image",
        files={"file": ("empty.jpg", file_bytes, "image/jpeg")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_api_detection_video_unsupported_format():
    file_bytes = io.BytesIO(b"fake data")
    response = client.post(
        "/api/detection/video",
        files={"file": ("test.pdf", file_bytes, "application/pdf")},
    )
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()
