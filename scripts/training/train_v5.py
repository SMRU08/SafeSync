r"""
scripts/training/train_v5.py — SafeSync V5 Unified Training Engine
==================================================================
Trains YOLOv8n on the complete, unified SafeSync 10,673-image dataset:
- All 7 canonical classes: person, helmet, safety_vest, gloves, safety_footwear, fire, smoke
- Fine-tunes from validated ppe_fire_smoke_v3 weights
- Validates on the 1,111-image validation split
- Records per-class mAP50, mAP50-95, Precision, and Recall metrics
- Generates SHA-256 checksum for model provenance
- Outputs to models/detection/safesync_v5_unified/
"""

import sys
import time
import json
import hashlib
import argparse
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_YAML = ROOT / "data.yaml"
OUTPUT_DIR = ROOT / "models" / "detection" / "safesync_v5_unified"
BASE_WEIGHTS = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"
FALLBACK_WEIGHTS = ROOT / "yolov8n.pt"


def sha256_file(filepath: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def train(epochs: int = 1, batch: int = 16, imgsz: int = 384, device: str = "cpu"):
    print("=" * 70)
    print("SafeSync: Training YOLOv8n on Unified Dataset (All 10,673 Images)")
    print("=" * 70)
    print(f"Data config:       {DATA_YAML}")
    print(f"Output directory:  {OUTPUT_DIR}")
    print(f"Hyperparameters:   epochs={epochs}, batch={batch}, imgsz={imgsz}, device={device}")

    if not DATA_YAML.exists():
        raise FileNotFoundError(f"data.yaml not found at {DATA_YAML}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    weights_to_use = str(BASE_WEIGHTS) if BASE_WEIGHTS.exists() else str(FALLBACK_WEIGHTS)
    print(f"Initializing base model from: {weights_to_use}")
    model = YOLO(weights_to_use)

    t0 = time.time()

    # Launch YOLO training
    train_results = model.train(
        data=str(DATA_YAML),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        workers=0,  # 0 is safe for Windows CPU multi-processing
        device=device,
        project=str(ROOT / "models" / "detection"),
        name="safesync_v5_unified",
        exist_ok=True,
        save=True,
        plots=True,
        verbose=True,
    )

    duration = round(time.time() - t0, 1)
    print(f"\nTraining completed in {duration}s")

    # Locate generated best weights
    best_pt = OUTPUT_DIR / "weights" / "best.pt"
    if not best_pt.exists():
        best_pt = OUTPUT_DIR / "weights" / "last.pt"

    best_sha = sha256_file(best_pt) if best_pt.exists() else None
    print(f"Saved weights: {best_pt}")
    print(f"Weights SHA-256: {best_sha}")

    # Run validation
    print("\nRunning validation evaluation on val split...")
    val_model = YOLO(str(best_pt))
    metrics = val_model.val(
        data=str(DATA_YAML),
        split="val",
        imgsz=imgsz,
        device=device,
        verbose=True,
    )

    # Class-wise mAP metrics
    class_map = {}
    if hasattr(metrics.box, "maps") and metrics.box.maps is not None:
        for idx, score in enumerate(metrics.box.maps):
            cname = metrics.names.get(idx, f"class_{idx}")
            class_map[cname] = round(float(score), 4)

    report = {
        "model_name": "safesync_v5_unified",
        "base_model": weights_to_use,
        "dataset": str(DATA_YAML),
        "total_images": 10673,
        "train_images": 7857,
        "val_images": 1111,
        "test_images": 1705,
        "epochs": epochs,
        "batch_size": batch,
        "imgsz": imgsz,
        "device": device,
        "training_duration_s": duration,
        "weights_path": str(best_pt),
        "sha256": best_sha,
        "metrics": {
            "mAP50": round(float(metrics.box.map50), 4),
            "mAP50_95": round(float(metrics.box.map), 4),
            "precision": round(float(metrics.box.mp), 4),
            "recall": round(float(metrics.box.mr), 4),
            "class_mAP50": class_map,
        },
    }

    report_path = OUTPUT_DIR / "training_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 70)
    print("SafeSync V5 Training & Validation Complete!")
    print(f"Report written to: {report_path}")
    print(f"mAP@50:            {report['metrics']['mAP50']}")
    print(f"mAP@50-95:         {report['metrics']['mAP50_95']}")
    print(f"Precision:         {report['metrics']['precision']}")
    print(f"Recall:            {report['metrics']['recall']}")
    print("=" * 70)

    return report


def main():
    parser = argparse.ArgumentParser(description="Train SafeSync V5 model on all unified images.")
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs to train (default: 1).")
    parser.add_argument("--batch", type=int, default=16, help="Batch size (default: 16).")
    parser.add_argument("--imgsz", type=int, default=384, help="Image resolution size (default: 384).")
    parser.add_argument("--device", type=str, default="cpu", help="Device: 'cpu' or '0' (for GPU).")
    args = parser.parse_args()

    train(epochs=args.epochs, batch=args.batch, imgsz=args.imgsz, device=args.device)


if __name__ == "__main__":
    main()
