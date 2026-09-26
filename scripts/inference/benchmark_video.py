"""
benchmark_video.py — SafeSync Phase 4
Video inference benchmark suite.
Measures real processing FPS, latency statistics (mean, median, min, max, stdev),
and outputs a clean diagnostic table.
"""

import os
import sys
import time
import json
import statistics
import argparse
import cv2

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.ai.detection.model_loader import ModelLoader
from backend.app.ai.detection.detector import Detector


def parse_args():
    parser = argparse.ArgumentParser(description="SafeSync — Video Inference Benchmark")
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to input video")
    parser.add_argument("--output-json", "-o", type=str, default=None, help="Path to save benchmark JSON")
    parser.add_argument("--confidence", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--device", "-d", type=str, default="auto", help="Device")
    parser.add_argument("--max-frames", type=int, default=300, help="Max frames to benchmark (default: 300)")
    parser.add_argument("--imgsz", type=int, default=384, help="Inference resolution")
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.isfile(args.input):
        print(f"[ERROR] Input video not found: {args.input}")
        sys.exit(1)

    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video file: {args.input}")
        sys.exit(1)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    input_fps = float(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    loader = ModelLoader.get_instance()
    device = loader.resolve_device(args.device)
    detector = Detector(loader)

    print("=" * 60)
    print("  SafeSync — Video Inference Latency Benchmark")
    print("=" * 60)
    print(f"  Input Video   : {args.input}")
    print(f"  Resolution    : {width}x{height}")
    print(f"  Input FPS     : {input_fps:.2f}")
    print(f"  Total Frames  : {total_frames}")
    print(f"  Target Frames : {min(args.max_frames, total_frames) if total_frames > 0 else args.max_frames}")
    print(f"  Device        : {device}")
    print(f"  Image Size    : {args.imgsz}")
    print("=" * 60)

    latencies_ms = []
    frame_count = 0
    t_start = time.perf_counter()

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            frame_count += 1

            # Time single frame inference
            resp, _ = detector.detect_image(
                image_input=frame,
                conf=args.confidence,
                imgsz=args.imgsz,
                annotate=False,
            )
            latencies_ms.append(resp.inference_time_ms)

            if args.max_frames > 0 and frame_count >= args.max_frames:
                break
    finally:
        cap.release()

    total_time_s = time.perf_counter() - t_start

    if not latencies_ms:
        print("[ERROR] No frames could be processed.")
        sys.exit(1)

    mean_lat = statistics.mean(latencies_ms)
    median_lat = statistics.median(latencies_ms)
    min_lat = min(latencies_ms)
    max_lat = max(latencies_ms)
    stdev_lat = statistics.stdev(latencies_ms) if len(latencies_ms) > 1 else 0.0
    processing_fps = frame_count / total_time_s if total_time_s > 0 else 0.0
    inference_fps = 1000.0 / mean_lat if mean_lat > 0 else 0.0

    print("\n" + "=" * 60)
    print("  VIDEO BENCHMARK RESULTS")
    print("=" * 60)
    print(f"  Frames Benchmarked : {frame_count}")
    print(f"  Resolution         : {width}x{height}")
    print(f"  Input Stream FPS   : {input_fps:.2f}")
    print(f"  Overall System FPS : {processing_fps:.2f}")
    print(f"  Raw Inference FPS  : {inference_fps:.2f}")
    print(f"  Mean Latency       : {mean_lat:.2f} ms")
    print(f"  Median Latency     : {median_lat:.2f} ms")
    print(f"  Min / Max Latency  : {min_lat:.2f} ms / {max_lat:.2f} ms")
    print(f"  Std Deviation      : {stdev_lat:.2f} ms")
    print(f"  Total Duration     : {total_time_s:.2f} s")
    print(f"  Device Used        : {device}")
    print("=" * 60)

    summary = {
        "video": args.input,
        "resolution": f"{width}x{height}",
        "frames_tested": frame_count,
        "input_fps": round(input_fps, 2),
        "processing_fps": round(processing_fps, 2),
        "inference_fps": round(inference_fps, 2),
        "mean_latency_ms": round(mean_lat, 2),
        "median_latency_ms": round(median_lat, 2),
        "min_latency_ms": round(min_lat, 2),
        "max_latency_ms": round(max_lat, 2),
        "stdev_latency_ms": round(stdev_lat, 2),
        "total_runtime_s": round(total_time_s, 2),
        "device": device,
    }

    out_json = args.output_json or os.path.join("outputs", "detection", "logs", "benchmark_summary.json")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nBenchmark JSON saved to: {out_json}")


if __name__ == "__main__":
    main()
