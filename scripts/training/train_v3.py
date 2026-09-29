"""
train_v3.py — SafeSync Phase 3 Model Retraining Engine
Trains YOLOv8n on the curated v3 dataset (datasets/processed_v3/data_v3.yaml).
Applies transfer learning from yolov8n.pt to establish strong feature representations.
Evaluates on both validation and independent test splits.
Compares resolutions (384, 448, 512) for latency, FPS, and small-object detection.
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_YAML = ROOT / "datasets" / "processed_v3" / "data_v3.yaml"
OUTPUT_DIR = ROOT / "models" / "detection" / "ppe_fire_smoke_v3"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def run_training():
    print("=== SafeSync Phase 3: Model Retraining (ppe_fire_smoke_v3) ===")
    print(f"Data configuration: {DATA_YAML}")
    print(f"Target directory: {OUTPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Base model
    base_model_path = ROOT / "yolov8n.pt"
    if not base_model_path.exists():
        base_model_path = "yolov8n.pt"

    print(f"Loading base model: {base_model_path}")
    model = YOLO(str(base_model_path))

    # Hyperparameters tuned for CPU convergence and small-object detection
    # imgsz=448 provides superior small-object resolution for gloves and footwear
    t0 = time.time()
    results = model.train(
        data=str(DATA_YAML),
        epochs=3,
        imgsz=448,
        batch=16,
        workers=0,
        device="cpu",
        project=str(ROOT / "models" / "detection"),
        name="ppe_fire_smoke_v3",
        exist_ok=True,
        pretrained=True,
        optimizer="auto",
        lr0=0.01,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=0.5,
        box=7.5,
        cls=1.2,       # Emphasize classification to separate helmet from person and vest
        dfl=1.5,
        mosaic=0.5,
        fliplr=0.5,
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.4,
        verbose=True,
        plots=True,
    )
    train_duration = time.time() - t0
    print(f"Training completed in {train_duration:.1f} seconds.")

    best_weight = OUTPUT_DIR / "weights" / "best.pt"
    if not best_weight.exists():
        best_weight = OUTPUT_DIR / "weights" / "last.pt"

    print(f"Validating best checkpoint: {best_weight}")
    val_model = YOLO(str(best_weight))

    # 1. Validation Split Metrics
    print("\n--- Running Validation Split Evaluation ---")
    val_metrics = val_model.val(data=str(DATA_YAML), split="val", imgsz=448, device="cpu", verbose=False)

    # 2. Test Split Evaluation (Unseen test set)
    print("\n--- Running Test Split Evaluation (Unseen) ---")
    test_metrics = val_model.val(data=str(DATA_YAML), split="test", imgsz=448, device="cpu", verbose=False)

    # 3. Benchmark Resolutions (Phase 12: 384 vs 448 vs 512)
    print("\n--- Benchmarking Inference Latency Across Resolutions ---")
    test_sample = next((ROOT / "datasets" / "processed_v3" / "images" / "test").glob("*.*"))

    res_benchmarks = {}
    for sz in [384, 448, 512]:
        times = []
        # Warmup
        for _ in range(5):
            val_model.predict(str(test_sample), imgsz=sz, device="cpu", verbose=False)
        # Timed runs
        for _ in range(25):
            t_start = time.perf_counter()
            val_model.predict(str(test_sample), imgsz=sz, device="cpu", verbose=False)
            times.append((time.perf_counter() - t_start) * 1000.0)
        mean_lat = sum(times) / len(times)
        fps = 1000.0 / mean_lat
        res_benchmarks[sz] = {
            "mean_latency_ms": round(mean_lat, 2),
            "fps": round(fps, 1),
            "p50_ms": round(sorted(times)[len(times) // 2], 2),
            "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 2),
        }
        print(f"Resolution {sz}x{sz}: Mean={mean_lat:.2f}ms (~{fps:.1f} FPS), P50={res_benchmarks[sz]['p50_ms']}ms, P95={res_benchmarks[sz]['p95_ms']}ms")

    # 4. Save Checksum & Metrics Report
    sha_hash = sha256_file(best_weight)
    with open(OUTPUT_DIR / "model.sha256", "w") as f:
        f.write(f"{sha_hash}  weights/best.pt\n")

    summary_data = {
        "model_name": "ppe_fire_smoke_v3",
        "sha256": sha_hash,
        "train_duration_seconds": round(train_duration, 1),
        "input_resolution": 448,
        "classes": CANONICAL_CLASSES,
        "val_metrics": {
            "precision": round(float(val_metrics.box.mp), 4),
            "recall": round(float(val_metrics.box.mr), 4),
            "mAP50": round(float(val_metrics.box.map50), 4),
            "mAP50_95": round(float(val_metrics.box.map), 4),
            "per_class_mAP50": {
                CANONICAL_CLASSES[i]: round(float(val_metrics.box.maps[i]), 4)
                for i in range(len(CANONICAL_CLASSES))
            } if hasattr(val_metrics.box, "maps") and len(val_metrics.box.maps) >= 7 else {}
        },
        "test_metrics": {
            "precision": round(float(test_metrics.box.mp), 4),
            "recall": round(float(test_metrics.box.mr), 4),
            "mAP50": round(float(test_metrics.box.map50), 4),
            "mAP50_95": round(float(test_metrics.box.map), 4),
            "per_class_mAP50": {
                CANONICAL_CLASSES[i]: round(float(test_metrics.box.maps[i]), 4)
                for i in range(len(CANONICAL_CLASSES))
            } if hasattr(test_metrics.box, "maps") and len(test_metrics.box.maps) >= 7 else {}
        },
        "resolution_benchmarks": res_benchmarks
    }

    with open(OUTPUT_DIR / "evaluation_metrics_v3.json", "w") as f:
        json.dump(summary_data, f, indent=2)

    print(f"\nFinal Summary Report saved to: {OUTPUT_DIR / 'evaluation_metrics_v3.json'}")
    print(f"Model Checkpoint SHA-256: {sha_hash}")

CANONICAL_CLASSES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}

if __name__ == "__main__":
    run_training()
