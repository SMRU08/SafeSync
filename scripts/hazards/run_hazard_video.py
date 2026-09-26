"""
run_hazard_video.py — SafeSync Phase 6
CLI Runner for Fire & Smoke Hazard Analysis on Video Files.
Extracts fire/smoke detections, tracks persistent events, resolves camera & zone metadata,
and exports benchmark metrics to outputs/hazards/hazard_benchmark.json.

Usage:
    python scripts/hazards/run_hazard_video.py --input datasets/test_safety_video.mp4 --camera-id camera_01
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

from backend.app.ai.hazards.video_hazard import process_hazard_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="SafeSync Phase 6 — Fire & Smoke Hazard Analysis Video CLI"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default="datasets/test_safety_video.mp4",
        help="Path to input video file (default: datasets/test_safety_video.mp4)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Path to save annotated video (default: outputs/hazards/videos/<name>_hazard.mp4)",
    )
    parser.add_argument(
        "--camera-id",
        type=str,
        default="camera_01",
        help="Camera identifier from configs/cameras.yaml (default: camera_01)",
    )
    parser.add_argument(
        "--confidence", "-c",
        type=float,
        default=None,
        help="Optional confidence override (default: use configs/hazard.yaml)",
    )
    parser.add_argument(
        "--skip-frames", "-s",
        type=int,
        default=0,
        help="Frame skipping interval (default: 0 = process every frame)",
    )
    parser.add_argument(
        "--benchmark", "-b",
        type=str,
        default=None,
        help="Path to save benchmark JSON (default: outputs/hazards/hazard_benchmark.json)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    input_file = os.path.abspath(args.input)
    if not os.path.isfile(input_file):
        log.error("Input video file not found: %s", input_file)
        sys.exit(1)

    print("=" * 70)
    print("  SafeSync — Phase 6: Fire & Smoke Hazard Analysis CLI")
    print("=" * 70)
    print(f"  Input Video   : {input_file}")
    print(f"  Camera ID     : {args.camera_id}")
    print(f"  Confidence    : {args.confidence or 'Default (configs/hazard.yaml)'}")
    print(f"  Skip Frames   : {args.skip_frames}")
    print("=" * 70)

    try:
        result = process_hazard_video(
            input_path=input_file,
            output_path=args.output,
            camera_id=args.camera_id,
            confidence=args.confidence,
            skip_frames=args.skip_frames,
            benchmark_path=args.benchmark,
        )

        print("\n" + "=" * 70)
        print("  PROCESSING COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"  Output Video         : {result.output_video_path}")
        print(f"  Benchmark JSON       : {result.benchmark_path}")
        print(f"  Processed Frames     : {result.processed_frames} / {result.total_frames}")
        print(f"  Processing Speed     : {result.processing_fps:.2f} FPS")
        print(f"  Mean Frame Latency   : {result.mean_latency_ms:.2f} ms")
        print("-" * 70)
        print(f"  Total Fire Events    : {result.total_fire_events}")
        print(f"  Total Smoke Events   : {result.total_smoke_events}")
        print(f"  Confirmed Events     : {result.confirmed_events}")
        print(f"  Suspected Events     : {result.suspected_events}")
        print(f"  Cleared Events       : {result.cleared_events}")
        print("=" * 70)

        if result.benchmark_path and os.path.isfile(result.benchmark_path):
            with open(result.benchmark_path, "r", encoding="utf-8") as bf:
                bdata = json.load(bf)
            print("\n  Benchmark Metrics Payload:")
            print(json.dumps(bdata, indent=2))

    except Exception as exc:
        log.exception("Hazard video processing failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
