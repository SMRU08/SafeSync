"""
run_rtsp.py — SafeSync Phase 4
RTSP / IP camera stream safety detection runner.
Credentials are NEVER stored in source code; passed via CLI or RTSP_URL env var.
Implements bounded exponential backoff reconnection logic.
"""

import os
import sys
import time
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
    parser = argparse.ArgumentParser(description="SafeSync — RTSP Stream Detection")
    parser.add_argument("--url", "-u", type=str, default=None, help="RTSP stream URL (or set RTSP_URL env var)")
    parser.add_argument("--confidence", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--device", "-d", type=str, default="auto", help="Inference device")
    parser.add_argument("--max-retries", type=int, default=5, help="Max reconnection attempts (default: 5)")
    parser.add_argument("--retry-delay", type=float, default=3.0, help="Delay between reconnect attempts in seconds")
    parser.add_argument("--imgsz", type=int, default=384, help="Inference image resolution")
    parser.add_argument("--headless", action="store_true", help="Run without UI window (server mode)")
    parser.add_argument("--max-frames", type=int, default=0, help="Stop after N frames (testing)")
    return parser.parse_args()


def sanitize_url(url: str) -> str:
    """Masks credentials in RTSP URL for safe logging."""
    if "@" in url and "://" in url:
        protocol, rest = url.split("://", 1)
        user_info, host_path = rest.split("@", 1)
        return f"{protocol}://***:***@{host_path}"
    return url


def connect_rtsp(url: str, timeout_s: float = 10.0) -> cv2.VideoCapture:
    """Initializes OpenCV VideoCapture for RTSP stream with network timeout settings."""
    # Set OpenCV FFMPEG network flags
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000"
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    return cap


def main():
    args = parse_args()

    rtsp_url = args.url or os.environ.get("RTSP_URL")
    if not rtsp_url:
        print("[ERROR] No RTSP URL provided. Specify via --url '<RTSP_URL>' or set RTSP_URL environment variable.")
        sys.exit(1)

    clean_url = sanitize_url(rtsp_url)
    print("=" * 65)
    print("  SafeSync — RTSP / IP Camera Detection")
    print("=" * 65)
    print(f"  Stream URL   : {clean_url}")
    print(f"  Confidence   : {args.confidence}")
    print(f"  Device       : {args.device}")
    print(f"  Max Retries  : {args.max_retries}")
    print(f"  Retry Delay  : {args.retry_delay}s")
    print("  Press 'q' or ESC in the window to stop.")
    print("=" * 65)

    loader = ModelLoader.get_instance()
    loader.resolve_device(args.device)
    processor = FrameProcessor()

    attempts = 0
    total_frames = 0
    window_name = f"SafeSync RTSP — {clean_url}"

    while attempts < args.max_retries:
        log.info(f"Connecting to RTSP stream: {clean_url} (Attempt {attempts + 1}/{args.max_retries})...")
        cap = connect_rtsp(rtsp_url)

        if not cap.isOpened():
            attempts += 1
            log.warning(f"Connection failed. Retrying in {args.retry_delay}s ({attempts}/{args.max_retries})...")
            time.sleep(args.retry_delay)
            continue

        log.info("RTSP stream connected successfully. Ingesting frames...")
        consecutive_failures = 0
        attempts = 0  # Reset retry counter upon successful connection

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    consecutive_failures += 1
                    if consecutive_failures > 30:
                        log.warning("Lost RTSP stream connection (30 empty frames). Triggering reconnection.")
                        break
                    time.sleep(0.01)
                    continue

                consecutive_failures = 0
                total_frames += 1

                detections, annotated_frame, latency_ms, fps = processor.process_frame(
                    frame=frame,
                    conf=args.confidence,
                    imgsz=args.imgsz,
                    annotate=True,
                )

                if not args.headless:
                    cv2.imshow(window_name, annotated_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord("q"), ord("Q"), 27):
                        log.info("User requested exit.")
                        return

                if args.max_frames > 0 and total_frames >= args.max_frames:
                    log.info(f"Reached max frames ({args.max_frames}). Exiting.")
                    return

        finally:
            cap.release()
            if not args.headless:
                cv2.destroyAllWindows()

        attempts += 1
        log.warning(f"RTSP stream dropped. Reconnecting ({attempts}/{args.max_retries})...")
        time.sleep(args.retry_delay)

    log.error(f"Exceeded maximum RTSP reconnection attempts ({args.max_retries}). Pipeline stopped.")
    sys.exit(3)


if __name__ == "__main__":
    main()
