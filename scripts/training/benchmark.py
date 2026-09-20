"""
benchmark.py — RAKSHYA VISION Phase 3
Benchmarks inference latency of the trained model on GPU and CPU.
Outputs results to models/detection/ppe_fire_smoke_v1/benchmark_results.json
"""

import os
import sys
import json
import time
import logging
import datetime
import statistics

import argparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
N_WARMUP = 5
N_RUNS = 50
IMGSZ = 384


def parse_args():
    parser = argparse.ArgumentParser(description="RAKSHYA VISION — Latency Benchmark")
    parser.add_argument("--experiment", "-e", type=str, default="ppe_fire_smoke_v1", help="Experiment name")
    parser.add_argument("--model", "-m", type=str, default=None, help="Explicit weights path override")
    return parser.parse_args()


def find_best_pt(model_dir, experiment):
    candidates = [
        os.path.join(model_dir, "weights", "best.pt"),
        os.path.join(ROOT, "models", "detection", experiment, "weights", "best.pt"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    raise FileNotFoundError(
        f"best.pt not found. Checked: {candidates}. Run train.py first."
    )



def benchmark_device(model_path, device, n_warmup=N_WARMUP, n_runs=N_RUNS):
    """Load model on given device and measure inference latency."""
    from ultralytics import YOLO
    import torch
    import numpy as np

    log.info(f"Benchmarking on device: {device}")
    model = YOLO(model_path)
    model.to(device)

    # Create dummy image (random noise, float32, 0-255)
    dummy_img = np.random.randint(0, 255, (IMGSZ, IMGSZ, 3), dtype=np.uint8)

    # Warm-up runs
    log.info(f"  Warm-up ({n_warmup} runs) ...")
    for _ in range(n_warmup):
        model.predict(dummy_img, verbose=False, device=device)

    if device != "cpu" and torch.cuda.is_available():
        torch.cuda.synchronize()

    # Timed runs
    log.info(f"  Timed runs ({n_runs} runs) ...")
    latencies = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        model.predict(dummy_img, verbose=False, device=device)
        if device != "cpu" and torch.cuda.is_available():
            torch.cuda.synchronize()
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)  # ms

    result = {
        "device": str(device),
        "n_runs": n_runs,
        "image_size": IMGSZ,
        "mean_ms": round(statistics.mean(latencies), 2),
        "median_ms": round(statistics.median(latencies), 2),
        "min_ms": round(min(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "stdev_ms": round(statistics.stdev(latencies), 2),
        "fps": round(1000.0 / statistics.mean(latencies), 1),
    }

    log.info(f"  Mean latency : {result['mean_ms']} ms  |  FPS: {result['fps']}")
    return result


def main():
    import torch
    args = parse_args()
    experiment = args.experiment
    model_dir = os.path.join(ROOT, "models", "detection", experiment)
    best_pt = args.model or find_best_pt(model_dir, experiment)

    results = {
        "experiment": experiment,
        "model": best_pt,
        "benchmarked_utc": datetime.datetime.utcnow().isoformat(),
        "image_size": IMGSZ,
        "devices": [],
    }

    # GPU benchmark
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_properties(0).name
        log.info(f"GPU available: {gpu_name}")
        try:
            gpu_result = benchmark_device(best_pt, device="0")
            gpu_result["gpu_name"] = gpu_name
            results["devices"].append(gpu_result)
        except Exception as e:
            log.error(f"GPU benchmark failed: {e}")
            results["devices"].append({"device": "GPU", "error": str(e)})
    else:
        log.info("CUDA not available — skipping GPU benchmark")
        results["devices"].append({"device": "GPU", "error": "CUDA not available"})

    # CPU benchmark
    try:
        cpu_result = benchmark_device(best_pt, device="cpu")
        results["devices"].append(cpu_result)
    except Exception as e:
        log.error(f"CPU benchmark failed: {e}")
        results["devices"].append({"device": "cpu", "error": str(e)})

    # Save results
    out_path = os.path.join(model_dir, "benchmark_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    log.info(f"Benchmark results saved: {out_path}")

    # Print summary
    print("\n" + "=" * 50)
    print("  INFERENCE BENCHMARK SUMMARY")
    print("=" * 50)
    for d in results["devices"]:
        if "error" in d:
            print(f"  {d['device']:8s} : ERROR — {d['error']}")
        else:
            print(f"  {d['device']:8s} : {d['mean_ms']} ms  ({d['fps']} FPS)")
    print("=" * 50)



if __name__ == "__main__":
    main()
