"""
scripts/training/train_gloves_candidate.py
SafeSync Phase 10: Candidate Model Training Engine

Fine-tunes YOLOv8n starting from verified V3 weights (ppe_fire_smoke_v3)
using the newly compiled, balanced gloves candidate dataset
(datasets/processed/gloves_candidate/data.yaml):
- Canonical 7 classes preserved (person, helmet, vest, gloves, footwear, fire, smoke).
- Multi-color glove enrichment + bare-hand negative background samples.
- Zero data leakage into frozen val/test benchmark sets.
- Strict isolation: saves exclusively to models/experiments/gloves_candidate/.
- NEVER touches or modifies production model weights or production configs.
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path
from ultralytics import YOLO

ROOT = Path("D:/Additional/PROJECT/SafeSync").resolve()
DATA_YAML = ROOT / "datasets" / "processed" / "gloves_candidate" / "data.yaml"
OUTPUT_DIR = ROOT / "models" / "experiments" / "gloves_candidate"
V3_WEIGHTS = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 80)
    print("SafeSync Phase 10: Training Gloves Candidate Model")
    print("=" * 80)
    print(f"Data config:      {DATA_YAML}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Base checkpoint:  {V3_WEIGHTS}")

    if not DATA_YAML.exists():
        raise FileNotFoundError(f"Candidate dataset config not found at {DATA_YAML}")

    if not V3_WEIGHTS.exists():
        raise FileNotFoundError(f"V3 production checkpoint not found at {V3_WEIGHTS}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    epochs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    batch = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    imgsz = 448
    device = "cpu"

    print(f"Hyperparameters:  epochs={epochs}, batch={batch}, imgsz={imgsz}, device={device}")

    # Load baseline model for fine-tuning
    model = YOLO(str(V3_WEIGHTS))

    start_time = time.time()
    results = model.train(
        data=str(DATA_YAML),
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        project=str(OUTPUT_DIR.parent),
        name=OUTPUT_DIR.name,
        exist_ok=True,
        pretrained=True,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        weight_decay=0.0005,
        warmup_epochs=0.5,
        hsv_h=0.02,
        hsv_s=0.5,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.3,
        fliplr=0.5,
        mosaic=0.3,
        workers=0,
        verbose=True,
        plots=True,
        save=True,
        save_period=1,
    )
    train_duration = time.time() - start_time
    print(f"\nCandidate training completed in {train_duration:.1f}s ({train_duration / 60:.2f} mins).")

    best_weights = OUTPUT_DIR / "weights" / "best.pt"
    if not best_weights.exists():
        best_weights = OUTPUT_DIR / "weights" / "last.pt"

    if best_weights.exists():
        hsh = sha256_file(best_weights)
        sz_mb = best_weights.stat().st_size / (1024 * 1024)
        print(f"\nCandidate model saved successfully:")
        print(f"  Path:    {best_weights}")
        print(f"  Size:    {sz_mb:.2f} MB")
        print(f"  SHA-256: {hsh}")

        metadata = {
            "model_name": "safesync_gloves_candidate_v1",
            "experiment_id": "gloves_candidate",
            "base_model": "ppe_fire_smoke_v3",
            "base_sha256": "9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe",
            "candidate_sha256": hsh,
            "architecture": "YOLOv8n",
            "classes": {
                "0": "person",
                "1": "helmet",
                "2": "safety_vest",
                "3": "gloves",
                "4": "safety_footwear",
                "5": "fire",
                "6": "smoke"
            },
            "training_epochs": epochs,
            "batch_size": batch,
            "input_resolution": [imgsz, imgsz],
            "training_duration_seconds": train_duration,
            "training_dataset": str(DATA_YAML),
            "device": device,
        }
        with open(OUTPUT_DIR / "candidate_metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"Saved candidate metadata to {OUTPUT_DIR / 'candidate_metadata.json'}")
    else:
        print("WARNING: best.pt / last.pt not found after training!")

if __name__ == "__main__":
    main()
