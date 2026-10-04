"""
scripts/training/train_construction_ppe.py — SafeSync
Trains YOLOv8n on the normalized Construction-PPE dataset.
- Uses canonical 7-class ontology mapping.
- Fine-tunes from verified ppe_fire_smoke_v3 weights.
- Evaluates on validation set and records metrics.
- Computes SHA-256 checksum of generated model weights.
- Saves cleanly to models/detection/construction_ppe_v1.
"""

import sys
import time
import json
import hashlib
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_YAML = ROOT / "datasets" / "normalized" / "construction_ppe" / "data.yaml"
OUTPUT_DIR = ROOT / "models" / "detection" / "construction_ppe_v1"
BASE_WEIGHTS = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"
FALLBACK_WEIGHTS = ROOT / "yolov8n.pt"


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("=" * 70)
    print("SafeSync: Training YOLOv8n on Normalized Construction-PPE")
    print("=" * 70)
    print(f"Data config:    {DATA_YAML}")
    print(f"Output directory: {OUTPUT_DIR}")

    if not DATA_YAML.exists():
        raise FileNotFoundError(f"Data config not found: {DATA_YAML}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    weights_to_use = str(BASE_WEIGHTS) if BASE_WEIGHTS.exists() else str(FALLBACK_WEIGHTS)
    print(f"Initializing model from: {weights_to_use}")
    model = YOLO(weights_to_use)

    epochs = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    imgsz = 384
    batch = 16

    print(f"Hyperparameters: epochs={epochs}, batch={batch}, imgsz={imgsz}, device=cpu")
    t0 = time.time()

    # Train
    train_results = model.train(
        data=str(DATA_YAML),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        workers=0,
        device="cpu",
        project=str(ROOT / "models" / "detection"),
        name="construction_ppe_v1",
        exist_ok=True,
        save=True,
        plots=True,
        verbose=True,
    )

    duration = round(time.time() - t0, 1)
    print(f"\nTraining completed in {duration}s")

    # Locate best.pt
    best_pt = OUTPUT_DIR / "weights" / "best.pt"
    if not best_pt.exists():
        best_pt = OUTPUT_DIR / "weights" / "last.pt"

    best_sha = sha256_file(best_pt) if best_pt.exists() else None
    print(f"Saved weights: {best_pt}")
    print(f"Weights SHA-256: {best_sha}")

    # Validate
    print("\nRunning validation on val split...")
    val_model = YOLO(str(best_pt))
    metrics = val_model.val(data=str(DATA_YAML), split="val", imgsz=imgsz, device="cpu", verbose=True)

    report = {
        "model_name": "construction_ppe_v1",
        "base_model": weights_to_use,
        "dataset": str(DATA_YAML),
        "epochs": epochs,
        "imgsz": imgsz,
        "training_duration_s": duration,
        "sha256": best_sha,
        "weights_path": str(best_pt),
        "metrics": {
            "mAP50": round(float(metrics.box.map50), 4),
            "mAP50_95": round(float(metrics.box.map), 4),
            "precision": round(float(metrics.box.mp), 4),
            "recall": round(float(metrics.box.mr), 4),
        },
    }

    report_path = OUTPUT_DIR / "training_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport generated: {report_path}")
    print(f"Validation mAP50: {report['metrics']['mAP50']}")
    print(f"Validation mAP50-95: {report['metrics']['mAP50_95']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
