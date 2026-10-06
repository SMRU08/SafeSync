r"""
scripts/training/train_glove_detector.py — SafeSync Multi-Color Glove Detection Training Engine
================================================================================================
Trains a dedicated YOLOv8n Glove Detector:
- Single canonical class: GLOVES (Class 0)
- Explicit visual morphology learning (finger contours, cuffs, palms, stitching)
- Invariant to glove color (Red, Blue, Black, White, Yellow, Green, Leather, etc.)
- Strong negative background suppression for bare hands, sleeves, and tools
- SafeSync Protection: Does NOT touch existing V3 model weights or thresholds.
"""

import sys, time, json, hashlib, argparse
from pathlib import Path
from ultralytics import YOLO

ROOT = Path("D:/Additional/PROJECT/SafeSync")
DATA_YAML = ROOT / "datasets" / "glove_detector" / "data_glove.yaml"
OUTPUT_DIR = ROOT / "models" / "detection" / "safesync_glove_detector"
BASE_WEIGHTS = ROOT / "yolov8n.pt"

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def train(epochs: int = 15, batch: int = 16, imgsz: int = 384, device: str = "cpu"):
    print("=" * 80)
    print("SafeSync: Training Multi-Color Glove Detector (YOLOv8n)")
    print("=" * 80)
    print(f"Data config:      {DATA_YAML}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Hyperparameters:  epochs={epochs}, batch={batch}, imgsz={imgsz}, device={device}")
    
    if not DATA_YAML.exists():
        raise FileNotFoundError(f"data_glove.yaml not found at {DATA_YAML}")
        
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize base YOLOv8n model
    model = YOLO(str(BASE_WEIGHTS))
    
    start_time = time.time()
    
    # Train with strong color jitter to prevent color bias
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
        lr0=0.002,
        lrf=0.01,
        weight_decay=0.0005,
        # Augmentation for multi-color & spatial generalization
        hsv_h=0.035,   # Hue jitter: shifts colors across color wheel
        hsv_s=0.7,     # Saturation jitter: handles bright vs faded colors
        hsv_v=0.4,     # Value jitter: handles lighting and shadows
        degrees=10.0,  # Slight rotation for natural hand tilt
        translate=0.1, # Translation for edge-of-frame hands
        scale=0.5,     # Scale for distance variations
        fliplr=0.5,    # Left-hand vs right-hand invariance
        mosaic=0.5,    # Multi-worker hand co-occurrence
        workers=4,
        verbose=True,
        save=True,
        save_period=5,
        plots=True,
    )
    
    train_duration = time.time() - start_time
    print(f"\nTraining completed in {train_duration:.1f} seconds ({train_duration / 60:.2f} minutes).")
    
    best_weights = OUTPUT_DIR / "weights" / "best.pt"
    if best_weights.exists():
        hsh = sha256_file(best_weights)
        sz_mb = best_weights.stat().st_size / (1024 * 1024)
        print(f"\nModel exported successfully:")
        print(f"  Path:    {best_weights}")
        print(f"  Size:    {sz_mb:.2f} MB")
        print(f"  SHA-256: {hsh}")
        
        # Save training metadata
        meta = {
            "model_name": "safesync_glove_detector",
            "architecture": "YOLOv8n",
            "task": "Multi-Color Glove Detection",
            "classes": ["GLOVES"],
            "sha256": hsh,
            "trained_epochs": epochs,
            "batch_size": batch,
            "imgsz": imgsz,
            "train_duration_seconds": train_duration,
            "training_dataset": str(DATA_YAML),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(OUTPUT_DIR / "training_metadata.json", "w") as f:
            json.dump(meta, f, indent=2)
            
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=384)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()
    
    train(epochs=args.epochs, batch=args.batch, imgsz=args.imgsz, device=args.device)
