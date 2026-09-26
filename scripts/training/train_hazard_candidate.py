"""
train_hazard_candidate.py — SafeSync Phase 6 Production Hardening
Trains a dedicated Fire & Smoke candidate model (YOLOv8n) with curated industrial hard negatives.
Saves all training artifacts, metrics, and checksum to models/detection/fire_smoke/candidate_v2/
"""

import os
import sys
import json
import yaml
import time
import shutil
import hashlib
from datetime import datetime, timezone
from ultralytics import YOLO

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_YAML = os.path.join(ROOT, "datasets", "normalized", "fire_smoke", "data.yaml")
OUTPUT_DIR = os.path.join(ROOT, "models", "detection", "fire_smoke", "candidate_v2")
BASE_WEIGHTS = os.path.join(ROOT, "yolov8n.pt")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("=" * 65)
    print("SafeSync Fire & Smoke Candidate Model Training (Candidate v2)")
    print("=" * 65)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    weights_dir = os.path.join(OUTPUT_DIR, "weights")
    os.makedirs(weights_dir, exist_ok=True)

    training_cfg = {
        "model": "yolov8n.pt",
        "data": DATA_YAML.replace(os.sep, "/"),
        "epochs": 2,
        "fraction": 0.25,
        "imgsz": 384,
        "batch": 16,
        "workers": 0,
        "device": "cpu",
        "optimizer": "AdamW",
        "lr0": 0.005,
        "lrf": 0.01,
        "weight_decay": 0.0005,
        "warmup_epochs": 0.3,
        "mosaic": 0.3,
        "hsv_h": 0.015,
        "hsv_s": 0.4,
        "hsv_v": 0.3,
        "fliplr": 0.5,
        "flipud": 0.0,
        "project": os.path.join(ROOT, "runs", "train_hazard").replace(os.sep, "/"),
        "name": "candidate_v2",
        "exist_ok": True,
        "seed": 42,
        "patience": 5,
        "val": True,
    }

    # Save training configuration
    cfg_save_path = os.path.join(OUTPUT_DIR, "training_config.yaml")
    with open(cfg_save_path, "w", encoding="utf-8") as f:
        yaml.dump(training_cfg, f, indent=2)

    print(f"Dataset YAML: {DATA_YAML}")
    print(f"Target Output: {OUTPUT_DIR}")
    print("Training parameters:")
    for k, v in training_cfg.items():
        print(f"  {k}: {v}")

    # Load base YOLO model
    print("\n[1/3] Initializing base YOLOv8n architecture...")
    model = YOLO(BASE_WEIGHTS if os.path.exists(BASE_WEIGHTS) else "yolov8n.pt")

    # Train
    print("\n[2/3] Executing training run...")
    t_start = time.time()
    results = model.train(**training_cfg)
    t_train = time.time() - t_start
    print(f"\nTraining completed in {t_train:.1f}s ({t_train/60:.2f} min)")

    # Locate trained weights
    run_dir = os.path.join(ROOT, "runs", "train_hazard", "candidate_v2")
    src_best = os.path.join(run_dir, "weights", "best.pt")
    src_last = os.path.join(run_dir, "weights", "last.pt")

    dst_best = os.path.join(weights_dir, "best.pt")
    dst_last = os.path.join(weights_dir, "last.pt")

    if os.path.exists(src_best):
        shutil.copy2(src_best, dst_best)
    elif os.path.exists(src_last):
        shutil.copy2(src_last, dst_best)
    else:
        raise FileNotFoundError(f"Training failed to produce weights in {run_dir}")

    if os.path.exists(src_last):
        shutil.copy2(src_last, dst_last)

    # Compute checksum
    ckpt_hash = sha256_file(dst_best)
    with open(os.path.join(OUTPUT_DIR, "model.sha256"), "w") as f:
        f.write(f"{ckpt_hash}  best.pt\n")

    print(f"\nTrained weights saved to: {dst_best}")
    print(f"SHA-256 Checksum: {ckpt_hash}")

    # Evaluate on val and test sets
    print("\n[3/3] Evaluating candidate model on validation and test sets...")
    cand_model = YOLO(dst_best)

    val_res = cand_model.val(data=DATA_YAML, split="val", imgsz=384, batch=16, device="cpu", verbose=False)
    test_res = cand_model.val(data=DATA_YAML, split="test", imgsz=384, batch=16, device="cpu", verbose=False)

    metrics_record = {
        "experiment": "hazard_candidate_v2",
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": ckpt_hash,
        "training_time_seconds": round(t_train, 2),
        "val": {
            "all": {
                "precision": round(float(val_res.results_dict.get("metrics/precision(B)", 0)), 4),
                "recall": round(float(val_res.results_dict.get("metrics/recall(B)", 0)), 4),
                "mAP50": round(float(val_res.results_dict.get("metrics/mAP50(B)", 0)), 4),
                "mAP50_95": round(float(val_res.results_dict.get("metrics/mAP50-95(B)", 0)), 4),
            },
            "fire": {
                "precision": round(float(val_res.box.p[0]) if len(val_res.box.p) > 0 else 0.0, 4),
                "recall": round(float(val_res.box.r[0]) if len(val_res.box.r) > 0 else 0.0, 4),
                "mAP50": round(float(val_res.box.ap50[0]) if len(val_res.box.ap50) > 0 else 0.0, 4),
                "mAP50_95": round(float(val_res.box.ap[0]) if len(val_res.box.ap) > 0 else 0.0, 4),
            },
            "smoke": {
                "precision": round(float(val_res.box.p[1]) if len(val_res.box.p) > 1 else 0.0, 4),
                "recall": round(float(val_res.box.r[1]) if len(val_res.box.r) > 1 else 0.0, 4),
                "mAP50": round(float(val_res.box.ap50[1]) if len(val_res.box.ap50) > 1 else 0.0, 4),
                "mAP50_95": round(float(val_res.box.ap[1]) if len(val_res.box.ap) > 1 else 0.0, 4),
            },
        },
        "test": {
            "all": {
                "precision": round(float(test_res.results_dict.get("metrics/precision(B)", 0)), 4),
                "recall": round(float(test_res.results_dict.get("metrics/recall(B)", 0)), 4),
                "mAP50": round(float(test_res.results_dict.get("metrics/mAP50(B)", 0)), 4),
                "mAP50_95": round(float(test_res.results_dict.get("metrics/mAP50-95(B)", 0)), 4),
            },
            "fire": {
                "precision": round(float(test_res.box.p[0]) if len(test_res.box.p) > 0 else 0.0, 4),
                "recall": round(float(test_res.box.r[0]) if len(test_res.box.r) > 0 else 0.0, 4),
                "mAP50": round(float(test_res.box.ap50[0]) if len(test_res.box.ap50) > 0 else 0.0, 4),
                "mAP50_95": round(float(test_res.box.ap[0]) if len(test_res.box.ap) > 0 else 0.0, 4),
            },
            "smoke": {
                "precision": round(float(test_res.box.p[1]) if len(test_res.box.p) > 1 else 0.0, 4),
                "recall": round(float(test_res.box.r[1]) if len(test_res.box.r) > 1 else 0.0, 4),
                "mAP50": round(float(test_res.box.ap50[1]) if len(test_res.box.ap50) > 1 else 0.0, 4),
                "mAP50_95": round(float(test_res.box.ap[1]) if len(test_res.box.ap) > 1 else 0.0, 4),
            },
        }
    }

    metrics_save_path = os.path.join(OUTPUT_DIR, "candidate_metrics.json")
    with open(metrics_save_path, "w", encoding="utf-8") as f:
        json.dump(metrics_record, f, indent=2)

    print(f"\nCandidate Metrics saved to: {metrics_save_path}")
    print("\nSummary on Validation Set:")
    print(f"  Fire  - Precision: {metrics_record['val']['fire']['precision']*100:.1f}%, Recall: {metrics_record['val']['fire']['recall']*100:.1f}%, mAP50: {metrics_record['val']['fire']['mAP50']*100:.1f}%")
    print(f"  Smoke - Precision: {metrics_record['val']['smoke']['precision']*100:.1f}%, Recall: {metrics_record['val']['smoke']['recall']*100:.1f}%, mAP50: {metrics_record['val']['smoke']['mAP50']*100:.1f}%")
    print(f"  All   - Precision: {metrics_record['val']['all']['precision']*100:.1f}%, Recall: {metrics_record['val']['all']['recall']*100:.1f}%, mAP50: {metrics_record['val']['all']['mAP50']*100:.1f}%")


if __name__ == "__main__":
    main()
