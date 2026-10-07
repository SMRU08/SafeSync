"""
train_v7_controlled.py — SafeSync V7 Controlled Training Pipeline

Executes controlled, reproducible training of SafeSync V7 experimental model:
- Base: yolov8n.pt
- Dataset: datasets/v7_candidate/dataset.yaml (7 classes, 6,163 images, 0 leakage)
- Resolution: 384x384 (edge CPU constraint)
- Architecture & hyperparameter specs from configs/v7_architecture_spec.yaml
- Checkpoint policy: writes ONLY to models/detection/safesync_v7_small_object/weights/
- Never alters V3 or V6
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
WEIGHTS_DIR = V7_DIR / "weights"
RUNS_DIR = V7_DIR / "runs"

V3_PATH = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"
V6_PATH = ROOT / "models" / "detection" / "safesync_v6_hardnegative" / "weights" / "best.pt"
EXPECTED_V3_SHA = "9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe"
EXPECTED_V6_SHA = "c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc"

def hash_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def verify_locks():
    v3_sha = hash_file(V3_PATH)
    v6_sha = hash_file(V6_PATH)
    assert v3_sha == EXPECTED_V3_SHA, f"CRITICAL: V3 SHA mismatch: {v3_sha}"
    assert v6_sha == EXPECTED_V6_SHA, f"CRITICAL: V6 SHA mismatch: {v6_sha}"
    print(f"[LOCK VERIFIED] V3: {v3_sha}")
    print(f"[LOCK VERIFIED] V6: {v6_sha}")

def main():
    parser = argparse.ArgumentParser(description="Train SafeSync V7 Controlled Experiment")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=384, help="Input image size")
    parser.add_argument("--workers", type=int, default=2, help="DataLoader workers")
    args = parser.parse_args()

    print("=" * 70)
    print("SAFESYNC V7 CONTROLLED TRAINING SESSION")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. Pre-flight Locks
    verify_locks()

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

    # 3. Model Initialization
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
        "project": str(RUNS_DIR),
        "name": "v7_controlled",
        "exist_ok": True,
        "seed": 42,
        "deterministic": True,
        "optimizer": "SGD",
        "lr0": 0.01,
        "lrf": 0.01,
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

    print("\nTraining Parameters:")
    for k, v in train_params.items():
        print(f"  {k}: {v}")

    start_time = time.time()
    start_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
    print(f"\n[START TRAINING] {start_str}")

    # Ensure clean run directory
    shutil.rmtree(RUNS_DIR / "v7_controlled", ignore_errors=True)

    results = model.train(**train_params)

    end_time = time.time()
    duration_sec = round(end_time - start_time, 2)
    end_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
    print(f"\n[TRAINING FINISHED] {end_str} (Duration: {duration_sec}s / {round(duration_sec/60, 2)} min)")

    # 4. Checkpoint Management
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    run_weights = RUNS_DIR / "v7_controlled" / "weights"
    
    src_best = run_weights / "best.pt"
    src_last = run_weights / "last.pt"
    
    dst_best = WEIGHTS_DIR / "best.pt"
    dst_last = WEIGHTS_DIR / "last.pt"

    if src_best.exists():
        shutil.copy2(src_best, dst_best)
        print(f"Copied best checkpoint -> {dst_best}")
    if src_last.exists():
        shutil.copy2(src_last, dst_last)
        print(f"Copied last checkpoint -> {dst_last}")

    best_sha = hash_file(dst_best) if dst_best.exists() else "MISSING"
    last_sha = hash_file(dst_last) if dst_last.exists() else "MISSING"

    print(f"\nV7 Checksum Records:")
    print(f"  best.pt SHA-256: {best_sha}")
    print(f"  last.pt SHA-256: {last_sha}")

    # 5. Re-verify Locks
    verify_locks()

    # 6. Parse Epoch Metrics from CSV
    results_csv = RUNS_DIR / "v7_controlled" / "results.csv"
    epoch_metrics = []
    if results_csv.exists():
        import csv
        with open(results_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleaned = {k.strip(): float(v.strip()) if v.strip() else 0.0 for k, v in row.items()}
                epoch_metrics.append(cleaned)

    # 7. Write Training Summary JSON
    summary_path = V7_DIR / "training" / "training_summary.json"
    summary_data = {
        "experiment_name": "safesync_v7_small_object",
        "status": "TRAINED_EXPERIMENTAL",
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
            "lrf": 0.01,
            "box": 7.5,
            "cls": 0.5,
            "dfl": 1.5,
            "seed": 42
        },
        "checkpoints": {
            "best_pt": str(dst_best),
            "best_sha256": best_sha,
            "last_pt": str(dst_last),
            "last_sha256": last_sha
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
    print(f"\nSaved training summary to: {summary_path}")
    print("=" * 70)
    print("V7 CONTROLLED TRAINING RUN COMPLETED SUCCESSFULLY")
    print("=" * 70)

if __name__ == '__main__':
    main()
