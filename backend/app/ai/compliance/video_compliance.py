"""
video_compliance.py — SafeSync Phase 5
Video processing pipeline for Worker Tracking, Spatial PPE Association & Compliance.
Computes and exports tracking stability metrics to outputs/tracking/tracking_metrics.json.
"""

import os
import cv2
import json
import time
import logging
from typing import Optional, Dict, Any

try:
    from app.ai.detection.utils import resolve_video_writer
    from app.ai.compliance.compliance_engine import WorkerComplianceEngine
    from app.ai.compliance.schemas import (
        VideoComplianceResult,
        ComplianceSummary,
        OverallComplianceState,
    )
except ImportError:
    from backend.app.ai.detection.utils import resolve_video_writer
    from backend.app.ai.compliance.compliance_engine import WorkerComplianceEngine
    from backend.app.ai.compliance.schemas import (
        VideoComplianceResult,
        ComplianceSummary,
        OverallComplianceState,
    )

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
log = logging.getLogger(__name__)


def process_compliance_video(
    input_path: str,
    output_path: Optional[str] = None,
    confidence: float = 0.25,
    skip_frames: int = 0,
    metrics_path: Optional[str] = None,
) -> VideoComplianceResult:
    """
    Processes a video file through worker tracking, spatial association, and temporal compliance.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input video not found: {input_path}")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"OpenCV failed to open video: {input_path}")

    total_source_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    source_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if output_path is None:
        out_dir = os.path.join(ROOT, "outputs", "compliance", "videos")
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(out_dir, f"{base}_compliance.mp4")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    writer, resolved_output_path = resolve_video_writer(output_path, source_fps, width, height)

    engine = WorkerComplianceEngine()
    engine.reset()

    frame_idx = 0
    processed_count = 0
    all_seen_worker_states: Dict[int, OverallComplianceState] = {}
    latencies = []

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
            t0 = time.perf_counter()
            response, annotated_frame, l_breakdown = engine.process_frame(
                frame, confidence_threshold=confidence, annotate=True
            )
            latencies.append((time.perf_counter() - t0) * 1000.0)

            # Record worker compliance states
            for w in response.workers:
                all_seen_worker_states[w.track_id] = w.overall_status

            if writer:
                writer.write(annotated_frame)

    finally:
        cap.release()
        if writer:
            writer.release()

    total_wall_s = max(0.001, time.perf_counter() - start_wall_time)
    processing_fps = processed_count / total_wall_s
    mean_lat_ms = sum(latencies) / len(latencies) if latencies else 0.0

    # Compile tracking metrics
    tracker_metrics = engine.tracker.metrics
    track_durations = list(tracker_metrics.get("track_durations", {}).values())
    avg_duration = sum(track_durations) / len(track_durations) if track_durations else 0.0

    metrics_record = {
        "video": input_path,
        "resolution": f"{width}x{height}",
        "total_source_frames": total_source_frames,
        "processed_frames": processed_count,
        "total_unique_tracks": tracker_metrics.get("total_unique_tracks", 0),
        "average_track_duration_frames": round(avg_duration, 1),
        "lost_track_events": tracker_metrics.get("lost_count", 0),
        "recovered_track_events": tracker_metrics.get("recovered_count", 0),
        "id_switches": tracker_metrics.get("id_switches", 0),
        "processing_fps": round(processing_fps, 2),
        "mean_latency_ms": round(mean_lat_ms, 2),
        "compliance_summary": {
            "total_workers": len(all_seen_worker_states),
            "compliant": sum(1 for s in all_seen_worker_states.values() if s == OverallComplianceState.COMPLIANT),
            "non_compliant": sum(1 for s in all_seen_worker_states.values() if s == OverallComplianceState.NON_COMPLIANT),
            "unknown": sum(1 for s in all_seen_worker_states.values() if s == OverallComplianceState.UNKNOWN),
        },
    }

    if metrics_path is None:
        track_dir = os.path.join(ROOT, "outputs", "tracking")
        os.makedirs(track_dir, exist_ok=True)
        metrics_path = os.path.join(track_dir, "tracking_metrics.json")

    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_record, f, indent=2)

    final_summary = ComplianceSummary(
        total_workers=metrics_record["compliance_summary"]["total_workers"],
        compliant_workers=metrics_record["compliance_summary"]["compliant"],
        non_compliant_workers=metrics_record["compliance_summary"]["non_compliant"],
        unknown_workers=metrics_record["compliance_summary"]["unknown"],
    )

    return VideoComplianceResult(
        video_path=input_path,
        output_video_path=resolved_output_path,
        total_frames=total_source_frames,
        processed_frames=processed_count,
        unique_tracks_count=metrics_record["total_unique_tracks"],
        average_track_duration_frames=metrics_record["average_track_duration_frames"],
        final_compliance_summary=final_summary,
        processing_fps=metrics_record["processing_fps"],
        mean_latency_ms=metrics_record["mean_latency_ms"],
        tracking_metrics_path=metrics_path,
    )
