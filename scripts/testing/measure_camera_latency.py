"""
measure_camera_latency.py — SafeSync Real-Time Latency Verification
Benchmark measuring:
1. Capture loop FPS and throughput
2. AI inference decoupling & execution latency
3. Stream delivery latency (T_delivery - T_capture)
4. Queue depth validation (bounded at 0 or 1, zero stale buildup)
5. Latest-frame-wins discard validation
"""

import os
import sys
import time
import statistics
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from app.camera.schemas import CameraConfigModel, CameraSourceType, CameraState
from app.camera.worker import CameraWorker
from app.camera.manager import CameraManager


def benchmark_camera_worker_latency(duration_seconds: float = 3.0):
    print("=" * 70)
    print("BENCHMARK: CameraWorker Real-Time Latency & Decoupled AI Verification")
    print("=" * 70)

    cfg = CameraConfigModel(
        id="bench_cam_01",
        name="Latency Benchmark Camera",
        source="synthetic://test",
        source_type=CameraSourceType.SYNTHETIC,
        enabled=True,
        fps_target=30,
    )
    worker = CameraWorker(cfg)
    worker.start()

    latencies_ms = []
    delivered_frames = 0
    last_frame_id = -1
    queue_depths = []

    start_time = time.time()
    try:
        while time.time() - start_time < duration_seconds:
            t_req = time.time()
            frame, frame_id, cap_time = worker.wait_for_new_frame(
                last_frame_id=last_frame_id,
                annotated=True,
                timeout=0.06,
            )
            if frame is not None and frame_id > last_frame_id:
                t_delivered = time.time()
                latency = (t_delivered - cap_time) * 1000.0  # ms
                latencies_ms.append(latency)
                last_frame_id = frame_id
                delivered_frames += 1
                queue_depths.append(worker.metrics.frame_queue_depth)

            time.sleep(0.01)  # Simulate fast streaming client
    finally:
        worker.stop()

    status = worker.get_status()
    total_captured = worker.metrics.frame_count
    dropped_ai = worker.metrics.dropped_ai_frames

    avg_lat = statistics.mean(latencies_ms) if latencies_ms else 0.0
    p50_lat = statistics.median(latencies_ms) if latencies_ms else 0.0
    p95_lat = np.percentile(latencies_ms, 95) if latencies_ms else 0.0
    max_lat = max(latencies_ms) if latencies_ms else 0.0
    max_queue = max(queue_depths) if queue_depths else 0

    print(f"Total Frames Captured:        {total_captured} frames")
    print(f"Stream Delivered Frames:      {delivered_frames} frames")
    print(f"Frames Dropped for AI:        {dropped_ai} frames (Latest-frame-wins)")
    print(f"Max Pending Queue Depth:      {max_queue} (Target: <= 1)")
    print(f"Capture FPS:                  {status.metrics.capture_fps:.1f} FPS")
    print(f"Inference Latency:            {status.metrics.inference_latency_ms:.1f} ms")
    print(f"Average Delivery Latency:     {avg_lat:.2f} ms")
    print(f"Median (P50) Latency:         {p50_lat:.2f} ms")
    print(f"95th Percentile (P95) Latency:{p95_lat:.2f} ms")
    print(f"Maximum Delivery Latency:     {max_lat:.2f} ms")

    # Assertions
    assert max_queue <= 1, f"Queue depth exceeded 1: {max_queue}"
    assert avg_lat < 150.0, f"Average delivery latency too high: {avg_lat}ms"
    assert delivered_frames > 0, "No frames delivered"
    print("\n>>> ALL REAL-TIME LATENCY CRITERIA PASSED! <<<")


if __name__ == "__main__":
    benchmark_camera_worker_latency(duration_seconds=3.0)
