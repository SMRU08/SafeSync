"""
process_video.py — SafeSync Phase 4
CLI tool for batch processing of video files with YOLO safety detection.
Usage:
    python scripts/inference/process_video.py --input path/to/video.mp4 [options]
"""

import os
import sys
import argparse
import logging
import json

# Ensure project root is in sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.ai.detection.video_processor import VideoProcessor
from backend.app.ai.detection.schemas import VideoProcessingOptions
from backend.app.ai.detection.model_loader import ModelLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="SafeSync — Video File Inference Engine")
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to input video file")
    parser.add_argument("--output", "-o", type=str, default=None, help="Path to save annotated output video")
    parser.add_argument("--confidence", "-c", type=float, default=0.25, help="Confidence threshold (0.01 - 1.0)")
    parser.add_argument("--iou", type=float, default=0.45, help="NMS IoU threshold (0.01 - 1.0)")
    parser.add_argument("--device", "-d", type=str, default="auto", help="Inference device ('auto', 'cpu', 'cuda')")
    parser.add_argument("--skip-frames", "-s", type=int, default=0, help="Frame skipping (0=none, 1=every 2nd, etc.)")
    parser.add_argument("--imgsz", type=int, default=384, help="Inference image resolution (default: 384)")
    parser.add_argument("--classes", nargs="*", default=None, help="Filter classes (e.g. --classes person helmet)")
    parser.add_argument("--no-save", action="store_true", help="Disable saving output video (benchmark mode)")
    return parser.parse_args()


def progress_tracker(current: int, total: int, fps: float):
    percent = (current / total) * 100 if total > 0 else 0
    sys.stdout.write(f"\rProcessing frame {current}/{total} ({percent:.1f}%) | Real-Time FPS: {fps:.1f}   ")
    sys.stdout.flush()


def main():
    args = parse_args()

    print("=" * 65)
    print("  SafeSync — Video Detection CLI")
    print("=" * 65)
    print(f"  Input File  : {args.input}")
    print(f"  Confidence  : {args.confidence}")
    print(f"  Device      : {args.device}")
    print(f"  Image Size  : {args.imgsz}")
    print(f"  Skip Frames : {args.skip_frames}")
    if args.classes:
        print(f"  Class Filter: {args.classes}")
    print("=" * 65)

    # Initialize model loader with requested device
    loader = ModelLoader.get_instance()
    loader.resolve_device(args.device)

    options = VideoProcessingOptions(
        confidence_threshold=args.confidence,
        iou_threshold=args.iou,
        image_size=args.imgsz,
        device=args.device,
        skip_frames=args.skip_frames,
        classes_filter=args.classes,
        save_video=not args.no_save,
        output_path=args.output,
    )

    processor = VideoProcessor()
    result = processor.process_video(
        video_path=args.input,
        options=options,
        progress_callback=progress_tracker,
    )
    print("\n")

    if not result.success:
        print(f"[ERROR] Video processing failed: {result.error_message}")
        sys.exit(1)

    print("=" * 65)
    print("  VIDEO PROCESSING COMPLETE")
    print("=" * 65)
    print(f"  Total Source Frames : {result.total_source_frames}")
    print(f"  Processed Frames    : {result.processed_frames}")
    print(f"  Skipped Frames      : {result.skipped_frames}")
    print(f"  Total Detections    : {result.total_detections}")
    print(f"  Class Counts        : {result.class_detection_counts}")
    print(f"  Input Source FPS    : {result.input_fps:.2f}")
    print(f"  Processing FPS      : {result.processing_fps:.2f}")
    print(f"  Inference FPS       : {result.inference_fps:.2f}")
    print(f"  Mean Latency        : {result.mean_inference_latency_ms:.2f} ms")
    print(f"  Total Runtime       : {result.total_processing_time_s:.2f} s")
    if result.output_video_path:
        print(f"  Output Video Saved  : {result.output_video_path}")
    print("=" * 65)


if __name__ == "__main__":
    main()
