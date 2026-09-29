"""
resume_v3.py — Resume training ppe_fire_smoke_v3 to complete epochs 2 and 3.
Evaluates on validation and test sets and exports final model artifacts.
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent
LAST_WEIGHT = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "last.pt"
OUTPUT_DIR = ROOT / "models" / "detection" / "ppe_fire_smoke_v3"
DATA_YAML = ROOT / "datasets" / "processed_v3" / "data_v3.yaml"

CANONICAL_CLASSES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def resume_and_evaluate():
    print(f"Resuming training from checkpoint: {LAST_WEIGHT}")
    t0 = time.time()
    model = YOLO(str(LAST_WEIGHT))
    model.train(resume=True)
    train_duration = time.time() - t0
    print(f"Training resumed and finished in {train_duration:.1f}s")

    best_weight = OUTPUT_DIR / "weights" / "best.pt"
    if not best_weight.exists():
        best_weight = LAST_WEIGHT

    print(f"\nEvaluating final checkpoint: {best_weight}")
    val_model = YOLO(str(best_weight))

    # 1. Validation Split Metrics
    print("--- Evaluating on Validation Split (split='val') ---")
    val_metrics = val_model.val(data=str(DATA_YAML), split="val", imgsz=448, device="cpu", verbose=False)

    # 2. Test Split Evaluation (Unseen test set)
    print("--- Evaluating on Unseen Test Split (split='test') ---")
    test_metrics = val_model.val(data=str(DATA_YAML), split="test", imgsz=448, device="cpu", verbose=False)

    # 3. Benchmark Resolutions (Phase 12: 384 vs 448 vs 512)
    print("\n--- Benchmarking Latency Across Resolutions ---")
    test_sample = next((ROOT / "datasets" / "processed_v3" / "images" / "test").glob("*.*"))

    res_benchmarks = {}
    for sz in [384, 448, 512]:
        times = []
        for _ in range(5):
            val_model.predict(str(test_sample), imgsz=sz, device="cpu", verbose=False)
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

if __name__ == "__main__":
    resume_and_evaluate()
