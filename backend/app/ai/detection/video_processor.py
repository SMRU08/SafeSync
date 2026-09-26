"""
video_processor.py — SafeSync Phase 4
Video file inference engine using OpenCV VideoCapture & VideoWriter.
Supports frame skipping, codec negotiation, corrupted frame recovery, and latency tracking.
"""

import os
import time
import logging
from typing import Optional, Dict, Any, Callable
import cv2

try:
    from app.ai.detection.frame_processor import FrameProcessor
    from app.ai.detection.schemas import VideoProcessingOptions, VideoProcessingResult
    from app.ai.detection.utils import resolve_video_writer
except ImportError:
    from backend.app.ai.detection.frame_processor import FrameProcessor
    from backend.app.ai.detection.schemas import VideoProcessingOptions, VideoProcessingResult
    from backend.app.ai.detection.utils import resolve_video_writer

log = logging.getLogger(__name__)


class VideoProcessor:
    """Processes recorded video files with object detection and annotations."""

    def __init__(self, frame_processor: Optional[FrameProcessor] = None):
        self.frame_processor = frame_processor or FrameProcessor()

    def process_video(
        self,
        video_path: str,
        options: Optional[VideoProcessingOptions] = None,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
    ) -> VideoProcessingResult:
        """
        Executes end-to-end video inference and produces an annotated output video.

        Args:
            video_path: Path to input video file.
            options: VideoProcessingOptions configuration.
            progress_callback: Optional callback fn(current_frame, total_frames, fps).

        Returns:
            VideoProcessingResult with full metrics.
        """
        opts = options or VideoProcessingOptions()

        # 1. Validation
        if not os.path.isfile(video_path):
            return VideoProcessingResult(
                success=False,
                input_video=video_path,
                error_message=f"Input video file not found at: {video_path}",
            )

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return VideoProcessingResult(
                success=False,
                input_video=video_path,
                error_message=f"OpenCV could not open video file: {video_path}",
            )

        # 2. Extract video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        input_fps = float(cap.get(cv2.CAP_PROP_FPS))
        total_source_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if width <= 0 or height <= 0 or input_fps <= 0:
            cap.release()
            return VideoProcessingResult(
                success=False,
                input_video=video_path,
                error_message=f"Invalid video metadata: {width}x{height} at {input_fps} FPS",
            )

        log.info(
            f"Opened video: '{video_path}' | Resolution: {width}x{height} | FPS: {input_fps:.2f} | Frames: {total_source_frames}"
        )

        # 3. Prepare output video path & writer
        writer = None
        final_output_path = None

        if opts.save_video:
            if opts.output_path:
                final_output_path = opts.output_path
            else:
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                out_dir = os.path.join("outputs", "detection", "videos")
                os.makedirs(out_dir, exist_ok=True)
                final_output_path = os.path.join(out_dir, f"{base_name}_detected.mp4")

            os.makedirs(os.path.dirname(os.path.abspath(final_output_path)), exist_ok=True)
            try:
                writer, final_output_path = resolve_video_writer(
                    output_path=final_output_path,
                    fps=input_fps,
                    width=width,
                    height=height,
                )
                log.info(f"VideoWriter initialized: {final_output_path}")
            except Exception as e:
                log.error(f"Failed to initialize VideoWriter: {e}")
                cap.release()
                return VideoProcessingResult(
                    success=False,
                    input_video=video_path,
                    error_message=f"VideoWriter error: {e}",
                )

        # 4. Processing loop
        self.frame_processor.reset_fps()

        frame_idx = 0
        processed_count = 0
        skipped_count = 0
        corrupted_count = 0
        total_detections = 0
        class_counts: Dict[str, int] = {}
        inference_latencies = []

        t_video_start = time.perf_counter()

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1

                # Corrupted frame check
                if not self.frame_processor.validate_frame(frame):
                    corrupted_count += 1
                    log.warning(f"Frame #{frame_idx} corrupted or empty. Skipping.")
                    continue

                # Frame skipping logic
                # skip_frames=0 means process every frame
                # skip_frames=1 means process every 2nd frame (frame_idx % 2 == 1)
                # skip_frames=2 means process every 3rd frame (frame_idx % 3 == 1)
                stride = opts.skip_frames + 1
                if (frame_idx - 1) % stride != 0:
                    skipped_count += 1
                    if writer is not None:
                        # Write original unannotated frame to keep video timing intact
                        writer.write(frame)
                    continue

                # Run inference & annotation
                detections, annotated_frame, latency_ms, current_fps = self.frame_processor.process_frame(
                    frame=frame,
                    conf=opts.confidence_threshold,
                    iou=opts.iou_threshold,
                    imgsz=opts.image_size,
                    classes_filter=opts.classes_filter,
                    annotate=opts.save_video,
                )

                processed_count += 1
                total_detections += len(detections)
                inference_latencies.append(latency_ms)

                for d in detections:
                    class_counts[d.class_name] = class_counts.get(d.class_name, 0) + 1

                if writer is not None and annotated_frame is not None:
                    writer.write(annotated_frame)

                if progress_callback and total_source_frames > 0:
                    progress_callback(frame_idx, total_source_frames, current_fps)

        finally:
            cap.release()
            if writer is not None:
                writer.release()

        total_time_s = time.perf_counter() - t_video_start
        mean_latency = sum(inference_latencies) / len(inference_latencies) if inference_latencies else 0.0
        processing_fps = processed_count / total_time_s if total_time_s > 0 else 0.0
        inference_fps = 1000.0 / mean_latency if mean_latency > 0 else 0.0

        # Verify output file
        if opts.save_video and final_output_path and os.path.isfile(final_output_path):
            file_size = os.path.getsize(final_output_path)
            log.info(f"Output video verified: '{final_output_path}' ({file_size:,} bytes)")

        log.info(
            f"Video processing finished: {processed_count} frames processed, "
            f"{skipped_count} skipped in {total_time_s:.2f}s ({processing_fps:.1f} FPS)"
        )

        return VideoProcessingResult(
            success=True,
            input_video=video_path,
            output_video_path=final_output_path,
            video_width=width,
            video_height=height,
            total_source_frames=total_source_frames,
            processed_frames=processed_count,
            skipped_frames=skipped_count,
            corrupted_frames=corrupted_count,
            total_detections=total_detections,
            class_detection_counts=class_counts,
            input_fps=round(input_fps, 2),
            processing_fps=round(processing_fps, 2),
            inference_fps=round(inference_fps, 2),
            mean_inference_latency_ms=round(mean_latency, 2),
            total_processing_time_s=round(total_time_s, 2),
            device=self.frame_processor.detector.loader.device,
        )
