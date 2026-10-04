r"""
scripts/training/train_v6.py — SafeSync V6 Hard-Negative Candidate Training Engine
==================================================================================
Trains YOLOv8n on the balanced, curated V6 dataset (4,541 train, 752 val, 569 test):
- Includes 298 verified hard-negative images (hneg_): steam, glare, excavators, dust
- Excludes ~3,500 unannotated empty background images (maintaining 4.69% background ratio)
- Fine-tunes from validated ppe_fire_smoke_v3 weights
- Saves candidate output strictly to models/detection/safesync_v6_hardnegative/
- Computes SHA-256 and records validation metrics
"""

import sys
import time
import json
import hashlib
import argparse
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_YAML = ROOT / "datasets" / "v6_candidate" / "data_v6.yaml"
OUTPUT_DIR = ROOT / "models" / "detection" / "safesync_v6_hardnegative"
BASE_WEIGHTS = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"
FALLBACK_WEIGHTS = ROOT / "yolov8n.pt"

CLASS_NAMES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}


def sha256_file(filepath: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def train(epochs: int = 15, batch: int = 16, imgsz: int = 384, device: str = "cpu"):
    print("=" * 80)
    print("SafeSync: Training Candidate V6 (Hard-Negative Balanced)")
    print("=" * 80)
    print(f"Data config:      {DATA_YAML}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Hyperparameters:  epochs={epochs}, batch={batch}, imgsz={imgsz}, device={device}")

    if not DATA_YAML.exists():
        raise FileNotFoundError(f"data_v6.yaml not found at {DATA_YAML}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    weights_to_use = str(BASE_WEIGHTS) if BASE_WEIGHTS.exists() else str(FALLBACK_WEIGHTS)
    print(f"Initializing base model from: {weights_to_use}")
    model = YOLO(weights_to_use)

    t0 = time.time()

    train_results = model.train(
        data=str(DATA_YAML),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        workers=0,
        device=device,
        project=str(ROOT / "models" / "detection"),
        name="safesync_v6_hardnegative",
        exist_ok=True,
        save=True,
        plots=True,
        verbose=True,
    )

    duration = round(time.time() - t0, 1)
    print(f"\nTraining completed in {duration}s ({duration/60:.1f} mins)")

    best_pt = OUTPUT_DIR / "weights" / "best.pt"
    if not best_pt.exists():
        best_pt = OUTPUT_DIR / "weights" / "last.pt"

    best_sha = sha256_file(best_pt) if best_pt.exists() else None
    print(f"Saved candidate weights: {best_pt}")
    print(f"Weights SHA-256:         {best_sha}")

    # Validation
    print("\nRunning post-training validation on V6 val split (752 images) ...")
    val_model = YOLO(str(best_pt))
    metrics = val_model.val(
        data=str(DATA_YAML),
        split="val",
        imgsz=imgsz,
        device=device,
        verbose=True,
    )

    box = metrics.box
    names = metrics.names

    per_class = {}
    p_curve = box.p
    r_curve = box.r
    ap50_curve = box.ap50
    ap_curve = box.ap
    nt_per_class = getattr(metrics, "nt_per_class", None)

    for i in range(len(names)):
        cname = names[i]
        p_val = float(p_curve[i]) if (p_curve is not None and len(p_curve) > i) else 0.0
        r_val = float(r_curve[i]) if (r_curve is not None and len(r_curve) > i) else 0.0
        ap50_val = float(ap50_curve[i]) if (ap50_curve is not None and len(ap50_curve) > i) else 0.0
        ap_val = float(ap_curve[i]) if (ap_curve is not None and len(ap_curve) > i) else 0.0
        gt_cnt = int(nt_per_class[i]) if (nt_per_class is not None and len(nt_per_class) > i) else 0
        pred_cnt = int(round(r_val * gt_cnt / max(1e-5, p_val))) if (p_val > 0 and gt_cnt > 0) else 0

        per_class[cname] = {
            "class_id": i,
            "precision": round(p_val, 4),
            "recall": round(r_val, 4),
            "mAP50": round(ap50_val, 4),
            "mAP50_95": round(ap_val, 4),
            "ground_truth_count": gt_cnt,
            "prediction_count": pred_cnt,
        }

    report = {
        "model_name": "safesync_v6_hardnegative",
        "base_model": weights_to_use,
        "dataset": str(DATA_YAML),
        "total_images": 5862,
        "train_images": 4541,
        "val_images": 752,
        "test_images": 569,
        "epochs": epochs,
        "batch_size": batch,
        "imgsz": imgsz,
        "device": device,
        "training_duration_s": duration,
        "weights_path": str(best_pt),
        "sha256": best_sha,
        "overall_metrics": {
            "precision": round(float(box.mp), 4),
            "recall": round(float(box.mr), 4),
            "mAP50": round(float(box.map50), 4),
            "mAP50_95": round(float(box.map), 4),
        },
        "per_class_metrics": per_class,
    }

    report_path = OUTPUT_DIR / "training_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 80)
    print("SafeSync V6 Candidate Training & Validation Complete!")
    print(f"Report written to: {report_path}")
    print(f"Overall mAP@50:    {report['overall_metrics']['mAP50']}")
    print(f"Overall Precision: {report['overall_metrics']['precision']}")
    print(f"Overall Recall:    {report['overall_metrics']['recall']}")
    print("=" * 80)

    return report


def main():
    parser = argparse.ArgumentParser(description="Train SafeSync V6 candidate model.")
    parser.add_argument("--epochs", type=int, default=15, help="Number of epochs to train (default: 15).")
    parser.add_argument("--batch", type=int, default=16, help="Batch size (default: 16).")
    parser.add_argument("--imgsz", type=int, default=384, help="Image resolution size (default: 384).")
    parser.add_argument("--device", type=str, default="cpu", help="Device: 'cpu' or '0' (for GPU).")
    args = parser.parse_args()

    train(epochs=args.epochs, batch=args.batch, imgsz=args.imgsz, device=args.device)


if __name__ == "__main__":
    main()
