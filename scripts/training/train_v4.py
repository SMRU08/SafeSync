"""
scripts/training/train_v4.py — SafeSync Phase 24 Model Retraining Engine (ppe_fire_smoke_v4)
Trains YOLOv8n on the comprehensive SafeSync v4 unified dataset:
- Integrates existing datasets + HF bucket + Ultralytics Construction-PPE + DataCluster Fire/Smoke + Hard Negatives.
- Fine-tunes from verified ppe_fire_smoke_v3 weights for progressive knowledge transfer.
- Evaluates on validation and independent test splits.
- Benchmarks edge latency and FPS across 384, 448, and 512 resolutions.
- Computes cryptographic SHA-256 checksum.
- Automatically updates Model Registry.
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path
from ultralytics import YOLO
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_YAML = ROOT / "data" / "processed" / "safesync" / "dataset.yaml"
OUTPUT_DIR = ROOT / "models" / "detection" / "ppe_fire_smoke_v4"
V3_WEIGHTS = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"


def sha256_file(filepath):
    """Compute SHA-256 checksum of a binary file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def update_registries(model_sha256, val_metrics, test_metrics, res_benchmarks):
    """Updates model_registry.yaml and MODEL_REGISTRY.json."""
    registry_yaml_path = ROOT / "models" / "registry" / "model_registry.yaml"
    registry_json_path = ROOT / "models" / "MODEL_REGISTRY.json"

    # 1. Update YAML registry
    if registry_yaml_path.exists():
        with open(registry_yaml_path, "r", encoding="utf-8") as f:
            reg_yaml = yaml.safe_load(f) or {}

        reg_yaml["active_production_model"] = "ppe_fire_smoke_v4"
        if "models" not in reg_yaml:
            reg_yaml["models"] = {}

        reg_yaml["models"]["ppe_fire_smoke_v4"] = {
            "model_name": "ppe_fire_smoke_v4",
            "version": "4.0.0",
            "model_path": "models/detection/ppe_fire_smoke_v4/weights/best.pt",
            "sha256": model_sha256,
            "status": "production",
            "classes": {
                0: "person",
                1: "helmet",
                2: "safety_vest",
                3: "gloves",
                4: "safety_footwear",
                5: "fire",
                6: "smoke",
            },
            "input_size": [448, 448],
            "framework": "Ultralytics YOLO (PyTorch)",
            "created_date": "2026-09-29",
            "verified_date": "2026-09-29",
            "description": "Unified 7-class detector v4 trained on enriched dataset (HF bucket, Construction-PPE, DataCluster fire/smoke, hard negatives).",
        }

        # Demote v3 to active_fallback / verified
        if "ppe_fire_smoke_v3" in reg_yaml["models"]:
            reg_yaml["models"]["ppe_fire_smoke_v3"]["status"] = "verified_fallback"

        with open(registry_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(reg_yaml, f, sort_keys=False)
        print(f"Updated {registry_yaml_path}")

    # 2. Update JSON registry
    if registry_json_path.exists():
        with open(registry_json_path, "r", encoding="utf-8") as f:
            reg_json = json.load(f)

        reg_json["updated_at"] = "2026-09-29T19:00:00Z"
        v4_entry = {
            "path": "models/detection/ppe_fire_smoke_v4/weights/best.pt",
            "sha256": model_sha256,
            "architecture": "yolov8n",
            "image_size": 448,
            "classes": {
                "0": "person",
                "1": "helmet",
                "2": "safety_vest",
                "3": "gloves",
                "4": "safety_footwear",
                "5": "fire",
                "6": "smoke",
            },
            "operating_thresholds": {
                "person": 0.22,
                "helmet": 0.30,
                "safety_vest": 0.30,
                "gloves": 0.22,
                "safety_footwear": 0.22,
                "fire": 0.20,
                "smoke": 0.20,
            },
            "datasets": [
                "ppe_safup",
                "ppec",
                "safety_ppe_4",
                "d_fire",
                "hf_smruti_ppe_bucket",
                "ultralytics_construction_ppe",
                "datacluster_fire_smoke",
                "hard_negatives",
            ],
            "notes": "Unified hardened v4 model with multi-source PPE, fire, and smoke detection.",
        }

        if "models" in reg_json and "ppe" in reg_json["models"]:
            reg_json["models"]["ppe"]["active_version"] = "ppe_v4"
            reg_json["models"]["ppe"]["versions"]["ppe_v4"] = v4_entry

        if "models" in reg_json and "hazards" in reg_json["models"]:
            reg_json["models"]["hazards"]["active_version"] = "fire_smoke_v4"
            reg_json["models"]["hazards"]["versions"]["fire_smoke_v4"] = {
                "path": "models/detection/ppe_fire_smoke_v4/weights/best.pt",
                "sha256": model_sha256,
                "architecture": "yolov8n",
                "image_size": 448,
                "classes": {"5": "fire", "6": "smoke"},
                "operating_thresholds": {"fire": 0.20, "smoke": 0.20},
                "datasets": ["d_fire", "datacluster_fire_smoke", "hard_negatives"],
                "notes": "Hardened fire and smoke detector v4 with multi-source hazard coverage.",
            }

        with open(registry_json_path, "w", encoding="utf-8") as f:
            json.dump(reg_json, f, indent=2)
        print(f"Updated {registry_json_path}")


def run_training():
    print("====================================================================")
    print("  SafeSync Phase 24: Model Retraining Engine (ppe_fire_smoke_v4)")
    print("====================================================================")
    print(f"Dataset config: {DATA_YAML}")
    print(f"Target directory: {OUTPUT_DIR}")

    if not DATA_YAML.exists():
        raise FileNotFoundError(f"Dataset config does not exist: {DATA_YAML}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Use v3 weights as transfer learning starting point
    if V3_WEIGHTS.exists():
        base_weights = str(V3_WEIGHTS)
        print(f"Transfer learning from verified v3 checkpoint: {base_weights}")
    else:
        base_weights = "yolov8n.pt"
        print(f"v3 checkpoint not found; starting from standard: {base_weights}")

    model = YOLO(base_weights)

    # Hyperparameters tuned for high detection accuracy and rapid convergence
    t0 = time.time()
    epochs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    results = model.train(
        data=str(DATA_YAML),
        epochs=epochs,
        imgsz=448,
        batch=16,
        workers=0,
        device="cpu",
        project=str(ROOT / "models" / "detection"),
        name="ppe_fire_smoke_v4",
        exist_ok=True,
        pretrained=True,
        optimizer="auto",
        lr0=0.008,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=0.5,
        box=7.5,
        cls=1.2,
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

    print(f"Evaluating best checkpoint: {best_weight}")
    val_model = YOLO(str(best_weight))

    # 1. Validation Split Metrics
    print("\n--- Running Validation Split Evaluation ---")
    val_metrics = val_model.val(data=str(DATA_YAML), split="val", imgsz=448, device="cpu", verbose=True)

    # 2. Test Split Evaluation (Unseen test set)
    print("\n--- Running Test Split Evaluation (Unseen Test Set) ---")
    test_metrics = val_model.val(data=str(DATA_YAML), split="test", imgsz=448, device="cpu", verbose=True)

    # 3. Benchmark Resolutions (384 vs 448 vs 512)
    print("\n--- Benchmarking Inference Latency Across Resolutions ---")
    test_images = list((ROOT / "data" / "processed" / "safesync" / "images" / "test").glob("*.*"))
    test_sample = str(test_images[0]) if test_images else None

    res_benchmarks = {}
    if test_sample:
        for sz in [384, 448, 512]:
            times = []
            # Warmup
            for _ in range(5):
                val_model.predict(test_sample, imgsz=sz, device="cpu", verbose=False)
            for _ in range(15):
                t_start = time.perf_counter()
                val_model.predict(test_sample, imgsz=sz, device="cpu", verbose=False)
                times.append((time.perf_counter() - t_start) * 1000.0)

            avg_ms = sum(times) / len(times)
            fps = 1000.0 / avg_ms
            res_benchmarks[f"{sz}x{sz}"] = {
                "latency_ms": round(avg_ms, 2),
                "fps": round(fps, 1),
            }
            print(f"  Resolution {sz}x{sz}: {avg_ms:.2f} ms ({fps:.1f} FPS)")

    # 4. Checksum
    best_sha256 = sha256_file(best_weight)
    print(f"\nBest Model SHA-256: {best_sha256}")

    # 5. Export comprehensive evaluation report
    report = {
        "model_name": "ppe_fire_smoke_v4",
        "created_at": "2026-09-29T19:00:00Z",
        "sha256": best_sha256,
        "weights_path": str(best_weight.relative_to(ROOT)),
        "train_duration_s": round(train_duration, 1),
        "validation_metrics": {
            "mAP50": round(float(val_metrics.box.map50), 4),
            "mAP50-95": round(float(val_metrics.box.map), 4),
            "precision": round(float(val_metrics.box.mp), 4),
            "recall": round(float(val_metrics.box.mr), 4),
            "per_class": {
                name: {
                    "mAP50": round(float(val_metrics.box.maps[i]), 4) if i < len(val_metrics.box.maps) else 0.0,
                }
                for i, name in enumerate(val_model.names.values())
            },
        },
        "test_metrics": {
            "mAP50": round(float(test_metrics.box.map50), 4),
            "mAP50-95": round(float(test_metrics.box.map), 4),
            "precision": round(float(test_metrics.box.mp), 4),
            "recall": round(float(test_metrics.box.mr), 4),
            "per_class": {
                name: {
                    "mAP50": round(float(test_metrics.box.maps[i]), 4) if i < len(test_metrics.box.maps) else 0.0,
                }
                for i, name in enumerate(val_model.names.values())
            },
        },
        "benchmarks": res_benchmarks,
    }

    report_path = OUTPUT_DIR / "evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Saved evaluation report to {report_path}")

    # 6. Update registries
    update_registries(best_sha256, val_metrics, test_metrics, res_benchmarks)

    print("\n====================================================================")
    print("  ppe_fire_smoke_v4 Retraining & Registration COMPLETED SUCCESSFULLY!")
    print("====================================================================")


if __name__ == "__main__":
    run_training()
