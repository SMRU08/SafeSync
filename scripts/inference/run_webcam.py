"""
run_webcam.py — RAKSHYA VISION Phase 4
Live webcam safety detection runner.
Usage:
    python scripts/inference/run_webcam.py --camera 0 [options]
"""

import os
import sys
import argparse
import logging
import cv2

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.ai.detection.frame_processor import FrameProcessor
from backend.app.ai.detection.model_loader import ModelLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="RAKSHYA VISION — Live Webcam Detection")
    parser.add_argument("--camera", "-c", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--confidence", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--device", "-d", type=str, default="auto", help="Inference device")
    parser.add_argument("--width", type=int, default=1280, help="Target capture width")
    parser.add_argument("--height", type=int, default=720, help="Target capture height")
    parser.add_argument("--imgsz", type=int, default=384, help="Inference image resolution")
    parser.add_argument("--max-frames", type=int, default=0, help="Exit after N frames (0=infinite)")
    parser.add_argument("--headless", action="store_true", help="Run without cv2.imshow (headless test mode)")
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 65)
    print("  RAKSHYA VISION — Live Webcam Detection")
    print("=" * 65)
    print(f"  Camera Index : {args.camera}")
    print(f"  Confidence   : {args.confidence}")
    print(f"  Device       : {args.device}")
    print(f"  Resolution   : {args.width}x{args.height}")
    print(f"  Inference Sz : {args.imgsz}")
    print("  Press 'q' or ESC in the video window to stop.")
    print("=" * 65)

    # Initialize model
    loader = ModelLoader.get_instance()
    loader.resolve_device(args.device)
    processor = FrameProcessor()

    # Open camera
    cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY)
    if not cap.isOpened():
        log.error(
            f"Could not open camera at index {args.camera}. "
            "Verify that a physical webcam is connected, drivers are installed, and permissions are granted."
        )
        sys.exit(2)  # Non-zero exit code indicating hardware unavailability

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    log.info(f"Webcam stream initialized at {actual_w}x{actual_h}")

    window_name = "RAKSHYA VISION — Real-Time Safety Monitor (Press 'q' to exit)"
    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                log.warning("Failed to capture frame from webcam. Stream interrupted.")
                break

            frame_count += 1

            detections, annotated_frame, latency_ms, fps = processor.process_frame(
                frame=frame,
                conf=args.confidence,
                imgsz=args.imgsz,
                annotate=True,
            )

            if not args.headless:
                cv2.imshow(window_name, annotated_frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q"), 27):  # 'q' or ESC
                    log.info("User requested exit.")
                    break
            else:
                if frame_count % 30 == 0:
                    log.info(f"Frame #{frame_count} | FPS: {fps:.1f} | Latency: {latency_ms:.1f}ms | Detections: {len(detections)}")

            if args.max_frames > 0 and frame_count >= args.max_frames:
                log.info(f"Reached max frames limit ({args.max_frames}). Stopping.")
                break

    finally:
        cap.release()
        if not args.headless:
            cv2.destroyAllWindows()
        log.info(f"Webcam resources released. Total frames captured: {frame_count}")


if __name__ == "__main__":
    main()
