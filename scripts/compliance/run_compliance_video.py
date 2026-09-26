"""
run_compliance_video.py — SafeSync Phase 5
CLI runner for Worker Tracking, Spatial PPE Association & Compliance Video Analysis.
Processes video through the complete ByteTrack + Spatial Association + Temporal State Machine pipeline.
Outputs annotated video with checklist HUD overlay and exports tracking stability metrics.

Usage:
    python scripts/compliance/run_compliance_video.py --input datasets/test_safety_video.mp4
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

from backend.app.ai.compliance.video_compliance import process_compliance_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="SafeSync Phase 5 — Worker Tracking & PPE Compliance Video CLI"
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
        help="Path to save annotated video (default: outputs/compliance/videos/<name>_compliance.mp4)",
    )
    parser.add_argument(
        "--confidence", "-c",
        type=float,
        default=0.25,
        help="YOLO detection confidence threshold (default: 0.25)",
    )
    parser.add_argument(
        "--skip-frames", "-s",
        type=int,
        default=0,
        help="Frame skipping interval (default: 0 = process every frame)",
    )
    parser.add_argument(
        "--metrics", "-m",
        type=str,
        default=None,
        help="Path to save tracking stability metrics JSON (default: outputs/tracking/tracking_metrics.json)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    input_file = os.path.abspath(args.input)
    if not os.path.isfile(input_file):
        log.error("Input video file not found: %s", input_file)
        sys.exit(1)

    print("=" * 70)
    print("  SafeSync — Phase 5: Worker Tracking & PPE Compliance Engine")
    print("=" * 70)
    print(f"  Input Video   : {input_file}")
    print(f"  Confidence    : {args.confidence}")
    print(f"  Skip Frames   : {args.skip_frames}")
    print("=" * 70)

    try:
        result = process_compliance_video(
            input_path=input_file,
            output_path=args.output,
            confidence=args.confidence,
            skip_frames=args.skip_frames,
            metrics_path=args.metrics,
        )

        print("\n" + "=" * 70)
        print("  PROCESSING COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"  Output Video       : {result.output_video_path}")
        print(f"  Tracking Metrics   : {result.tracking_metrics_path}")
        print(f"  Processed Frames   : {result.processed_frames} / {result.total_frames}")
        print(f"  Unique Tracks      : {result.unique_tracks_count}")
        print(f"  Avg Track Duration : {result.average_track_duration_frames:.1f} frames")
        print(f"  Processing Speed   : {result.processing_fps:.2f} FPS")
        print(f"  Mean Frame Latency : {result.mean_latency_ms:.2f} ms")
        print("-" * 70)
        print(f"  Total Workers Seen : {result.final_compliance_summary.total_workers}")
        print(f"  Compliant Workers  : {result.final_compliance_summary.compliant_workers}")
        print(f"  Non-Compliant      : {result.final_compliance_summary.non_compliant_workers}")
        print(f"  Unknown State      : {result.final_compliance_summary.unknown_workers}")
        print("=" * 70)

        # Print tracking metrics file contents for verification
        if os.path.isfile(result.tracking_metrics_path):
            with open(result.tracking_metrics_path, "r", encoding="utf-8") as mf:
                metrics_data = json.load(mf)
            print("\n  Summary Metrics Payload:")
            print(json.dumps(metrics_data, indent=2))

    except Exception as exc:
        log.exception("Compliance video processing failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
