# Phase 4 — Real-Time Video Detection Engineering Documentation
**Project:** RAKSHYA VISION — AI Vision-Based Safety Monitoring  
**Phase:** 4 (Real-Time / Video Detection)  
**Status:** COMPLETED & VERIFIED  

---

## 1. Executive Summary

Phase 4 bridges the Phase 3 trained YOLO detection model (`ppe_fire_smoke_v1/weights/best.pt`) with production-grade video processing capabilities. The system supports three primary video ingestion modes:
1. **Uploaded Video Files**: Asynchronous processing with frame-level bounding box visualization, class count aggregation, and encoded video export.
2. **Local Webcam Ingestion**: High-throughput video streaming from physical/USB camera devices with interactive OpenCV display and graceful keyboard interrupt ('q' / ESC).
3. **RTSP / IP Camera Feeds**: Robust network stream reader featuring automatic TCP transport, bounded exponential backoff reconnection, and URI credential masking.

In addition, Phase 4 delivers high-performance FastAPI REST endpoints for real-time single-frame inspection, video upload processing, and detection engine health monitoring.

---

## 2. Architecture & Components

```
RAKSHYA VISION
├── configs/
│   └── detection.yaml                     # Central detection configuration
├── backend/app/ai/detection/
│   ├── __init__.py                        # Clean public module exports
│   ├── schemas.py                         # Pydantic v2 schemas for detections & video
│   ├── model_loader.py                    # Thread-safe Singleton YOLO model loader
│   ├── utils.py                           # Color palette, text rendering, VideoWriter resolver
│   ├── detector.py                        # Core inference engine (detect_image, timing)
│   ├── frame_processor.py                 # Per-frame validation, drawing, and FPS tracking
│   └── video_processor.py                 # Multi-frame OpenCV pipeline with frame-skipping
├── backend/app/api/
│   └── detection.py                       # FastAPI REST endpoints (/health, /image, /video)
├── scripts/inference/
│   ├── process_video.py                   # CLI for batch/offline video processing
│   ├── run_webcam.py                      # CLI for live webcam safety detection
│   ├── run_rtsp.py                        # CLI for RTSP network stream monitoring
│   ├── benchmark_video.py                 # CLI for latency & throughput benchmarking
│   └── create_test_video.py               # Test utility to generate synthetic safety videos
└── outputs/detection/
    ├── benchmark_report.json              # Latency distribution and FPS metrics
    ├── README.md                          # Output catalog
    └── videos/test_safety_detected.mp4    # Processed verification video (120 frames)
```

### 2.1 Model Loader (`model_loader.py`)
- **Singleton Pattern**: Prevents duplicate multi-hundred-megabyte YOLO weights in memory.
- **Hardware Adaptability**: Automatically evaluates CUDA availability. When CUDA is absent, safely defaults to CPU while pinning `torch.set_num_threads(8)` to utilize high-efficiency performance cores on modern hybrid architectures without core thrashing.
- **Class Schema Validation**: Verifies that loaded weights match the 7 canonical classes:
  `{0: 'person', 1: 'helmet', 2: 'safety_vest', 3: 'gloves', 4: 'safety_footwear', 5: 'fire', 6: 'smoke'}`.

### 2.2 Visualization & Drawing (`utils.py`)
- Consistent BGR color coding:
  - `person`: Neon Yellow `(0, 215, 255)`
  - `helmet`: Lime Green `(0, 255, 0)`
  - `safety_vest`: Safety Orange `(0, 140, 255)`
  - `gloves`: Cyan `(255, 255, 0)`
  - `safety_footwear`: Deep Blue `(255, 100, 0)`
  - `fire`: Bright Red `(0, 0, 255)`
  - `smoke`: Slate Gray `(128, 128, 128)`
- Anti-aliased labels: Drawn with filled background rectangles and `[class] [confidence]` formatting (`cv2.LINE_AA`).
- Non-destructive processing: Always operates on explicit image copies (`image.copy()`) to avoid mutating source frames.

### 2.3 Video Processing Engine (`video_processor.py`)
- **Codec Negotiation**: Probes `mp4v` (primary) and falls back to `XVID` (`.avi`) if MP4 encoding is not supported on the target host.
- **Corrupted Frame Resilience**: Catches invalid frames or read failures without crashing the pipeline, cleanly incrementing error counters.
- **Frame Skipping**: Configurable `skip_frames` parameter allows reducing compute requirements for high-FPS sources (e.g., skip 1 of every 2 frames for 2x speedup).

---

## 3. CLI Usage Guide

### 3.1 Video Processing CLI
Processes an uploaded or local video file and exports an annotated output video:
```powershell
python scripts/inference/process_video.py `
    --input datasets/test_safety_video.mp4 `
    --output outputs/detection/videos/test_safety_detected.mp4 `
    --confidence 0.25 `
    --device auto `
    --imgsz 384
```

### 3.2 Live Webcam CLI
Captures frames from a local USB/integrated webcam and streams real-time detections with HUD overlay:
```powershell
# Interactive display mode (press 'q' or ESC to exit)
python scripts/inference/run_webcam.py --camera 0 --confidence 0.25

# Headless server / test mode (runs 30 frames and exits)
python scripts/inference/run_webcam.py --camera 0 --headless --max-frames 30
```

### 3.3 RTSP Stream CLI
Connects to an RTSP IP camera with credential masking and exponential backoff:
```powershell
# Stream from IP camera
python scripts/inference/run_rtsp.py `
    --url "rtsp://admin:password@192.168.1.100:554/live/ch0" `
    --confidence 0.25 `
    --max-retries 5 `
    --retry-delay 3.0
```
*Note: Sensitive credentials in the URL are masked in all console logs (e.g., `rtsp://***:***@192.168.1.100:554/live/ch0`).*

### 3.4 Video Benchmark Tool
Measures true throughput, frame rate, and latency distributions (min, max, mean, median, stdev):
```powershell
python scripts/inference/benchmark_video.py `
    --input datasets/test_safety_video.mp4 `
    --output outputs/detection/benchmark_report.json `
    --frames 120
```

---

## 4. REST API Documentation

The FastAPI backend exposes detection endpoints under `/api/detection`.

### 4.1 Health Check
- **Endpoint**: `GET /api/detection/health`
- **Response**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cpu",
  "model_path": "D:\\Additional\\PROJECT\\RAKSHYA-VISION\\models\\detection\\ppe_fire_smoke_v1\\weights\\best.pt",
  "supported_classes": [
    "person", "helmet", "safety_vest", "gloves", "safety_footwear", "fire", "smoke"
  ]
}
```

### 4.2 Image Detection
- **Endpoint**: `POST /api/detection/image`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file`: Image file (`image/jpeg`, `image/png`, `image/webp`, max 20 MB)
  - `confidence`: Optional float (default: 0.25)
  - `annotate`: Optional bool (default: false, returns base64 annotated image)
- **Response**: `ImageDetectionResponse` schema with bounding boxes, labels, confidence scores, and latency in milliseconds.

### 4.3 Video Detection
- **Endpoint**: `POST /api/detection/video`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file`: Video file (`video/mp4`, `video/avi`, `video/quicktime`, max 100 MB)
  - `confidence`: Optional float (default: 0.25)
  - `skip_frames`: Optional int (default: 0)
- **Response**: `VideoProcessingResult` schema with frame counts, class distribution, processing FPS, and mean latency.

---

## 5. Quantitative Benchmark Results

Benchmarked on **Intel Core i5-13420H (CPU execution)** using a 120-frame safety video (640x480 resolution, 384px inference resolution):

| Metric | Value |
| :--- | :--- |
| **Test Video Resolution** | 640x480 px |
| **Inference Resolution** | 384x384 px |
| **Input Stream FPS** | 15.0 FPS |
| **Overall Pipeline FPS** | **16.04 FPS** |
| **Raw Inference FPS** | **16.96 FPS** |
| **Median Frame Latency** | **32.89 ms** (~30.4 FPS steady-state) |
| **Min Frame Latency** | **28.33 ms** (~35.3 FPS peak) |
| **Mean Frame Latency** | **58.95 ms** |
| **Max Frame Latency** | 3,020.37 ms (one-time cold model warmup on frame 1) |
| **Total Frames Processed** | 120 / 120 (0 skipped) |
| **Total Detections** | 88 (`helmet`: 74, `safety_vest`: 14) |
| **Hardware State** | CPU (Intel UHD Graphics, no CUDA) |

---

## 6. Verification & Automated Test Suite

A comprehensive test suite in `backend/tests/` covers unit, integration, and API functionality:
- `test_bounding_box_properties`: Validates coordinates and width/height calculations.
- `test_detection_object_schema`: Validates Pydantic serialization.
- `test_model_loader_singleton`: Confirms single instance creation across callers.
- `test_device_selection_auto_and_cpu`: Verifies robust CPU fallback when CUDA is absent.
- `test_device_selection_invalid_cuda_fails_clearly`: Confirms descriptive errors for missing hardware.
- `test_model_loading_and_canonical_classes`: Verifies 7 canonical classes.
- `test_detector_inference_on_synthetic_image`: Tests inference output format.
- `test_detector_invalid_image_raises_error`: Ensures corrupted/empty arrays raise descriptive errors.
- `test_detector_confidence_filtering`: Verifies threshold filtering.
- `test_frame_processor_validation`: Validates input frame dimensions and types.
- `test_frame_processor_execution`: Tests end-to-end frame processing and FPS calculation.
- `test_class_colors_exist_for_all_canonical_classes`: Verifies full color palette coverage.
- `test_draw_detections_does_not_modify_in_place`: Guarantees immutability of input frames.
- `test_video_processor_missing_file_returns_error`: Verifies graceful failure for nonexistent files.
- `test_api_detection_health`: Verifies `/api/detection/health`.
- `test_api_detection_image_valid`: Verifies `/api/detection/image` with test payload.
- `test_api_detection_image_unsupported_format`: Verifies rejection of invalid MIME types.
- `test_api_detection_image_zero_bytes`: Verifies rejection of 0-byte uploads.
- `test_api_detection_video_unsupported_format`: Verifies rejection of invalid video files.
- `test_root_endpoint`, `test_health_endpoint`, `test_invalid_endpoint_returns_404`, `test_invalid_method_returns_405`: Core API resilience tests.

**Test Run Summary:**
- Total Tests: **23 passed**
- Failed / Skipped: **0**
- Execution Duration: **7.47s**

---

## 7. Strict Phase Boundaries & Next Phase Readiness

- **Tracking (ByteTrack/DeepSORT)**: NOT implemented in Phase 4.
- **Worker-to-PPE Association**: NOT implemented in Phase 4.
- **Safety Violation / Compliance Rules**: NOT implemented in Phase 4.
- **Live Alert Dispatch & WebSocket Push**: NOT implemented in Phase 4.

The pipeline is completely verified and ready for **Phase 5 (Worker Tracking & Safety Engine)** upon user instruction.
