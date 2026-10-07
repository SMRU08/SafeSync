"""
train_v7_run2.py — SafeSync V7 Controlled Training Run 2 (Multi-Epoch Convergence)

Executes Run 2 multi-epoch convergence experiment:
- Base: yolov8n.pt
- Dataset: datasets/v7_candidate/dataset.yaml (6,163 images, 0 leakage)
- Resolution: 384x384
- Hyperparameters: SGD, lr0=0.01, momentum=0.937, box=7.5, cls=0.5, dfl=1.5, batch=16, seed=42
- Output: models/detection/safesync_v7_small_object/runs/run2/
- Checks & Preserves:
  - V3 Production Checkpoint (9b414f3018d5...)
  - V6 Shadow Checkpoint (c47705a2c27c...)
  - Run-1 Checkpoint (5a4e37fb381c...)
"""

import os
import sys
import time
import json
import shutil
import hashlib
import platform
import argparse
from pathlib import Path
import psutil
import torch
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent
YAML_PATH = ROOT / "datasets" / "v7_candidate" / "dataset.yaml"
BASE_MODEL = ROOT / "yolov8n.pt"
V7_DIR = ROOT / "models" / "detection" / "safesync_v7_small_object"
RUN2_DIR = V7_DIR / "runs" / "run2"
RUN2_WEIGHTS_DIR = RUN2_DIR / "weights"
RUN2_METRICS_DIR = RUN2_DIR / "metrics"

V3_PATH = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"
V6_PATH = ROOT / "models" / "detection" / "safesync_v6_hardnegative" / "weights" / "best.pt"
RUN1_PATH = V7_DIR / "runs" / "run1" / "weights" / "best.pt"

EXPECTED_V3_SHA = "9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe"
EXPECTED_V6_SHA = "c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc"
EXPECTED_RUN1_SHA = "5a4e37fb381c318f4dd88a5bc7e80d43489c9e8fbf566f8b2024813ad2da9334"

def hash_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def verify_all_locks():
    v3_sha = hash_file(V3_PATH)
    v6_sha = hash_file(V6_PATH)
    run1_sha = hash_file(RUN1_PATH) if RUN1_PATH.exists() else "MISSING"

    assert v3_sha == EXPECTED_V3_SHA, f"CRITICAL: V3 SHA mismatch: {v3_sha}"
    assert v6_sha == EXPECTED_V6_SHA, f"CRITICAL: V6 SHA mismatch: {v6_sha}"
    assert run1_sha == EXPECTED_RUN1_SHA, f"CRITICAL: Run-1 SHA mismatch: {run1_sha}"

    print(f"[LOCK VERIFIED] V3 Production: {v3_sha}")
    print(f"[LOCK VERIFIED] V6 Shadow:     {v6_sha}")
    print(f"[LOCK VERIFIED] Run-1 Backup:  {run1_sha}")

def main():
    parser = argparse.ArgumentParser(description="Train SafeSync V7 Run 2 (Multi-Epoch)")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=384, help="Input image size")
    parser.add_argument("--workers", type=int, default=0, help="DataLoader workers")
    args = parser.parse_args()

    print("=" * 70)
    print("SAFESYNC V7 CONTROLLED TRAINING RUN 2 — MULTI-EPOCH CONVERGENCE")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. Pre-flight Locks
    verify_all_locks()

    # 2. Hardware and Environment Metadata
    env_info = {
        "python_version": platform.python_version(),
        "pytorch_version": torch.__version__,
        "ultralytics_version": "8.4.156",
        "platform": platform.platform(),
        "processor": platform.processor(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "device": "cpu",
        "cuda_available": torch.cuda.is_available()
    }
    print("\nEnvironment & Hardware:")
    for k, v in env_info.items():
        print(f"  {k}: {v}")

    # 3. Model Initialization from yolov8n.pt base
    assert BASE_MODEL.exists(), f"Base model {BASE_MODEL} not found!"
    print(f"\nInitializing YOLOv8n base from: {BASE_MODEL}")
    model = YOLO(str(BASE_MODEL))

    train_params = {
        "data": str(YAML_PATH),
        "imgsz": args.imgsz,
        "epochs": args.epochs,
        "batch": args.batch,
        "workers": args.workers,
        "device": "cpu",
        "project": str(V7_DIR / "runs"),
        "name": "run2",
        "exist_ok": True,
        "seed": 42,
        "deterministic": True,
        "optimizer": "SGD",
        "lr0": 0.01,
        "lrf": 0.01,
        "momentum": 0.937,
        "box": 7.5,
        "cls": 0.5,
        "dfl": 1.5,
        "hsv_h": 0.015,
        "hsv_s": 0.7,
        "hsv_v": 0.4,
        "fliplr": 0.5,
        "mosaic": 1.0,
        "mixup": 0.1,
        "copy_paste": 0.1,
        "plots": True,
        "verbose": True
    }

    print("\nRun-2 Training Parameters:")
    for k, v in train_params.items():
        print(f"  {k}: {v}")

    # Clean only run2 directory if exists
    shutil.rmtree(RUN2_DIR, ignore_errors=True)

    start_time = time.time()
    start_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
    print(f"\n[START TRAINING RUN 2] {start_str}")

    results = model.train(**train_params)

    end_time = time.time()
    duration_sec = round(end_time - start_time, 2)
    end_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
    print(f"\n[TRAINING RUN 2 FINISHED] {end_str} (Duration: {duration_sec}s / {round(duration_sec/60, 2)} min)")

    # 4. Checkpoint Verification
    RUN2_WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    best_pt = RUN2_WEIGHTS_DIR / "best.pt"
    last_pt = RUN2_WEIGHTS_DIR / "last.pt"

    best_sha = hash_file(best_pt) if best_pt.exists() else "MISSING"
    last_sha = hash_file(last_pt) if last_pt.exists() else "MISSING"

    print(f"\nRun-2 Checksum Records:")
    print(f"  Run-2 best.pt SHA-256: {best_sha}")
    print(f"  Run-2 last.pt SHA-256: {last_sha}")

    # 5. Re-verify Locks
    verify_all_locks()

    # 6. Parse Epoch Metrics from CSV
    results_csv = RUN2_DIR / "results.csv"
    epoch_metrics = []
    if results_csv.exists():
        import csv
        with open(results_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleaned = {k.strip(): float(v.strip()) if v.strip() else 0.0 for k, v in row.items()}
                epoch_metrics.append(cleaned)

    # 7. Write Training Summary JSON
    RUN2_METRICS_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = RUN2_METRICS_DIR / "training_summary.json"
    summary_data = {
        "experiment_name": "safesync_v7_run2_convergence",
        "status": "RUN2_TRAINED_EXPERIMENTAL",
        "start_time": start_str,
        "end_time": end_str,
        "duration_seconds": duration_sec,
        "duration_minutes": round(duration_sec / 60, 2),
        "environment": env_info,
        "hyperparameters": {
            "epochs": args.epochs,
            "batch_size": args.batch,
            "imgsz": args.imgsz,
            "optimizer": "SGD",
            "lr0": 0.01,
            "momentum": 0.937,
            "box": 7.5,
            "cls": 0.5,
            "dfl": 1.5,
            "seed": 42
        },
        "checkpoints": {
            "run2_best_pt": str(best_pt),
            "run2_best_sha256": best_sha,
            "run2_last_pt": str(last_pt),
            "run2_last_sha256": last_sha,
            "run1_best_sha256": EXPECTED_RUN1_SHA
        },
        "production_lock": {
            "v3_sha": hash_file(V3_PATH),
            "v6_sha": hash_file(V6_PATH),
            "status": "UNTOUCHED"
        },
        "epoch_metrics": epoch_metrics
    }

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2)
    print(f"\nSaved Run-2 training summary to: {summary_path}")
    print("=" * 70)
    print("V7 RUN 2 CONTROLLED TRAINING COMPLETED SUCCESSFULLY")
    print("=" * 70)

if __name__ == '__main__':
    main()
