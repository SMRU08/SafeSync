"""
video_hazard.py — RAKSHYA VISION Phase 6
Video processing and benchmarking pipeline for Fire & Smoke Hazard Analysis.
Generates annotated hazard output video and exports performance metrics to outputs/hazards/hazard_benchmark.json.
"""

import os
import cv2
import json
import time
import logging
from typing import Optional, Dict, Any

try:
    from app.ai.detection.utils import resolve_video_writer
    from app.ai.hazards.hazard_engine import HazardAnalysisEngine
    from app.ai.hazards.schemas import VideoHazardResult, HazardState, HazardType
except ImportError:
    from backend.app.ai.detection.utils import resolve_video_writer
    from backend.app.ai.hazards.hazard_engine import HazardAnalysisEngine
    from backend.app.ai.hazards.schemas import VideoHazardResult, HazardState, HazardType

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
log = logging.getLogger(__name__)


def process_hazard_video(
    input_path: str,
    output_path: Optional[str] = None,
    camera_id: str = "camera_01",
    confidence: Optional[float] = None,
    skip_frames: int = 0,
    benchmark_path: Optional[str] = None,
) -> VideoHazardResult:
    """
    Processes a video file through the Fire & Smoke Hazard Analysis pipeline.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input video not found: {input_path}")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open video: {input_path}")

    total_source_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    source_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if output_path is None:
        out_dir = os.path.join(ROOT, "outputs", "hazards", "videos")
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(out_dir, f"{base}_hazard.mp4")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    writer, resolved_output_path = resolve_video_writer(output_path, source_fps, width, height)

    engine = HazardAnalysisEngine()
    engine.reset()

    frame_idx = 0
    processed_count = 0

    all_event_states: Dict[str, HazardState] = {}
    all_event_types: Dict[str, HazardType] = {}
    all_event_confs: Dict[str, float] = {}

    detect_latencies = []
    hazard_analysis_latencies = []
    total_latencies = []

    start_wall_time = time.perf_counter()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1

            if skip_frames > 0 and (frame_idx % (skip_frames + 1)) != 1:
                continue

            processed_count += 1
            t_frame_start = time.perf_counter()

            resp, annotated_frame, lat_dict = engine.process_frame(
                frame=frame,
                camera_id=camera_id,
                confidence_override=confidence,
                annotate=True,
            )

            t_total = (time.perf_counter() - t_frame_start) * 1000.0
            detect_latencies.append(lat_dict.get("detect_ms", 0.0))
            hazard_analysis_latencies.append(
                lat_dict.get("track_ms", 0.0) + lat_dict.get("temporal_ms", 0.0)
            )
            total_latencies.append(t_total)

            # Record event lifecycle states
            for h in resp.hazards:
                all_event_states[h.event_id] = h.state
                all_event_types[h.event_id] = h.hazard_type
                all_event_confs[h.event_id] = max(all_event_confs.get(h.event_id, 0.0), h.max_confidence)

            if writer:
                writer.write(annotated_frame)

    finally:
        cap.release()
        if writer:
            writer.release()

    total_wall_s = max(0.001, time.perf_counter() - start_wall_time)
    processing_fps = processed_count / total_wall_s

    mean_detect_ms = sum(detect_latencies) / len(detect_latencies) if detect_latencies else 0.0
    mean_hazard_ms = sum(hazard_analysis_latencies) / len(hazard_analysis_latencies) if hazard_analysis_latencies else 0.0
    mean_total_ms = sum(total_latencies) / len(total_latencies) if total_latencies else 0.0

    # Counts
    fire_events = sum(1 for t in all_event_types.values() if t == HazardType.FIRE)
    smoke_events = sum(1 for t in all_event_types.values() if t == HazardType.SMOKE)
    confirmed_count = sum(1 for s in all_event_states.values() if s == HazardState.CONFIRMED)
    suspected_count = sum(1 for s in all_event_states.values() if s == HazardState.SUSPECTED)
    cleared_count = sum(1 for s in all_event_states.values() if s == HazardState.CLEARED)
    avg_conf = sum(all_event_confs.values()) / len(all_event_confs) if all_event_confs else 0.0

    benchmark_data = {
        "video": input_path,
        "resolution": f"{width}x{height}",
        "total_source_frames": total_source_frames,
        "processed_frames": processed_count,
        "performance": {
            "processing_fps": round(processing_fps, 2),
            "detection_latency_ms": round(mean_detect_ms, 2),
            "hazard_analysis_latency_ms": round(mean_hazard_ms, 2),
            "total_latency_ms": round(mean_total_ms, 2),
        },
        "hazard_metrics": {
            "total_fire_events": fire_events,
            "total_smoke_events": smoke_events,
            "confirmed_events": confirmed_count,
            "suspected_events": suspected_count,
            "cleared_events": cleared_count,
            "average_confidence": round(avg_conf, 4),
        },
        "event_states": {eid: st.value for eid, st in all_event_states.items()},
    }

    if benchmark_path is None:
        out_bench_dir = os.path.join(ROOT, "outputs", "hazards")
        os.makedirs(out_bench_dir, exist_ok=True)
        benchmark_path = os.path.join(out_bench_dir, "hazard_benchmark.json")

    os.makedirs(os.path.dirname(benchmark_path), exist_ok=True)
    with open(benchmark_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2)

    return VideoHazardResult(
        video_path=input_path,
        output_video_path=resolved_output_path,
        total_frames=total_source_frames,
        processed_frames=processed_count,
        total_fire_events=fire_events,
        total_smoke_events=smoke_events,
        confirmed_events=confirmed_count,
        suspected_events=suspected_count,
        cleared_events=cleared_count,
        processing_fps=round(processing_fps, 2),
        mean_latency_ms=round(mean_total_ms, 2),
        benchmark_path=benchmark_path,
    )
