"""
train.py — SafeSync Phase 3
Runs YOLOv8 training for experiment: ppe_fire_smoke_v1
Loads configs/training.yaml, applies hardware-appropriate overrides,
saves all artifacts to models/detection/ppe_fire_smoke_v1/
"""

import os
import sys
import json
import yaml
import time
import shutil
import hashlib
import platform
import datetime
import subprocess
import logging

import argparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def parse_args():
    parser = argparse.ArgumentParser(description="SafeSync — Model Training Engine")
    parser.add_argument("--config", type=str, default=os.path.join(ROOT, "configs", "training.yaml"), help="Path to training config YAML")
    parser.add_argument("--experiment", type=str, default=None, help="Experiment name override")
    parser.add_argument("--data", type=str, default=None, help="Path to data YAML override")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip pre-flight verification")
    return parser.parse_args()


def load_training_config(config_path):
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Training config not found: {config_path}")
    with open(config_path) as f:
        return yaml.safe_load(f)



def detect_hardware():
    """Returns dict with GPU info, VRAM, and recommended batch size."""
    info = {"cuda": False, "gpu_name": "CPU", "vram_gb": 0.0, "recommended_batch": 8}
    try:
        import torch
        if torch.cuda.is_available():
            info["cuda"] = True
            props = torch.cuda.get_device_properties(0)
            info["gpu_name"] = props.name
            info["vram_gb"] = props.total_memory / (1024 ** 3)
            vram = info["vram_gb"]
            if vram >= 16:
                info["recommended_batch"] = 32
            elif vram >= 8:
                info["recommended_batch"] = 16
            elif vram >= 6:
                info["recommended_batch"] = 12
            elif vram >= 4:
                info["recommended_batch"] = 8
            else:
                info["recommended_batch"] = 4
        else:
            info["recommended_batch"] = 4  # CPU training, keep small
    except ImportError:
        pass
    return info


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_preflight():
    preflight = os.path.join(ROOT, "scripts", "training", "preflight_training_check.py")
    log.info("Running pre-flight check ...")
    result = subprocess.run(
        [sys.executable, preflight],
        capture_output=False
    )
    if result.returncode != 0:
        log.error("Pre-flight check FAILED. Aborting training.")
        sys.exit(1)
    log.info("Pre-flight check PASSED.")


def train(args=None):
    from ultralytics import YOLO

    if args is None:
        args = parse_args()

    cfg = load_training_config(args.config)
    experiment = args.experiment or cfg.get("experiment", "ppe_fire_smoke_v1")
    model_dir = os.path.join(ROOT, "models", "detection", experiment)
    data_yaml = args.data or cfg.get("data", os.path.join(ROOT, "datasets", "processed", "data.yaml"))

    os.makedirs(model_dir, exist_ok=True)
    hw = detect_hardware()

    log.info(f"Hardware: {hw['gpu_name']}  |  VRAM: {hw['vram_gb']:.2f} GB  |  CUDA: {hw['cuda']}")

    # Resolve batch size: config overrides hardware recommendation
    batch = cfg.get("batch", hw["recommended_batch"])
    device = "0" if hw["cuda"] else "cpu"

    model_size = cfg.get("model", "yolov8s.pt")
    epochs = cfg.get("epochs", 50)
    imgsz = cfg.get("imgsz", 640)
    workers = cfg.get("workers", 4)
    lr0 = cfg.get("lr0", 0.01)
    lrf = cfg.get("lrf", 0.001)
    patience = cfg.get("patience", 15)
    project_dir = os.path.join(ROOT, "models", "detection")

    log.info(f"Experiment : {experiment}")
    log.info(f"Data YAML  : {data_yaml}")
    log.info(f"Model      : {model_size}")
    log.info(f"Epochs     : {epochs}")
    log.info(f"Batch size : {batch}")
    log.info(f"Image size : {imgsz}")
    log.info(f"Device     : {device}")
    log.info(f"Output     : {model_dir}")

    import torch
    if not hw["cuda"]:
        torch.set_num_threads(8)
        log.info(f"PyTorch CPU threads set to: {torch.get_num_threads()}")

    model = YOLO(model_size)

    start_time = time.time()
    try:
        results = model.train(
            data=data_yaml,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
            workers=workers,
            lr0=lr0,
            lrf=lrf,
            warmup_epochs=cfg.get("warmup_epochs", 0.2),
            fraction=cfg.get("fraction", 1.0),
            patience=patience,
            project=project_dir,
            name=experiment,
            exist_ok=True,
            save=True,
            save_period=1,
            plots=True,
            verbose=True,
            cls=cfg.get("cls", 0.5),
            box=cfg.get("box", 7.5),
            mosaic=cfg.get("mosaic", 0.5),
            mixup=cfg.get("mixup", 0.0),
            copy_paste=cfg.get("copy_paste", 0.0),
            degrees=cfg.get("degrees", 0.0),
            fliplr=cfg.get("fliplr", 0.5),
        )
        elapsed = time.time() - start_time
        log.info(f"Training complete in {elapsed/3600:.2f} hours")
    except RuntimeError as e:
        if "out of memory" in str(e).lower() or "CUDA out of memory" in str(e):
            log.error(f"CUDA OOM at batch={batch}. Attempting recovery with batch={max(1, batch//2)} ...")
            import torch
            torch.cuda.empty_cache()
            reduced_batch = max(1, batch // 2)
            log.warning(f"Retrying with batch={reduced_batch}. Documenting change.")
            # Write OOM record
            oom_note = {
                "event": "CUDA_OOM",
                "original_batch": batch,
                "reduced_batch": reduced_batch,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "error": str(e)[:500],
            }
            oom_path = os.path.join(model_dir, "oom_recovery.json")
            with open(oom_path, "w") as f:
                json.dump(oom_note, f, indent=2)
            results = model.train(
                data=data_yaml,
                epochs=epochs,
                imgsz=imgsz,
                batch=reduced_batch,
                device=device,
                workers=workers,
                lr0=lr0,
                lrf=lrf,
                patience=patience,
                project=project_dir,
                name=experiment,
                exist_ok=True,
                save=True,
                plots=True,
                verbose=True,
                cls=cfg.get("cls", 0.5),
                box=cfg.get("box", 7.5),
                mosaic=cfg.get("mosaic", 1.0),
            )
            elapsed = time.time() - start_time
            log.info(f"Training complete (after OOM recovery) in {elapsed/3600:.2f} hours")
        else:
            raise

    # Compute SHA-256 of best.pt
    best_pt = os.path.join(model_dir, "weights", "best.pt")
    if not os.path.isfile(best_pt):
        # YOLO sometimes nests under experiment name
        alt = os.path.join(project_dir, experiment, "weights", "best.pt")
        if os.path.isfile(alt):
            best_pt = alt

    sha = sha256_file(best_pt) if os.path.isfile(best_pt) else "NOT_FOUND"

    sha_path = os.path.join(model_dir, "model.sha256")
    with open(sha_path, "w") as f:
        f.write(f"{sha}  best.pt\n")
    log.info(f"SHA-256: {sha}")

    # Write model_metadata.json
    metadata = {
        "experiment": experiment,
        "model_architecture": model_size,
        "framework": "Ultralytics YOLOv8",
        "training_completed_utc": datetime.datetime.utcnow().isoformat(),
        "training_duration_seconds": round(time.time() - start_time),
        "hardware": hw,
        "hyperparameters": {
            "epochs": epochs,
            "batch_size": batch,
            "imgsz": imgsz,
            "lr0": lr0,
            "lrf": lrf,
            "patience": patience,
            "mosaic": cfg.get("mosaic", 1.0),
            "mixup": cfg.get("mixup", 0.1),
            "device": device,
        },
        "dataset": {
            "path": data_yaml,
            "train_images": 15717,
            "val_images": 4490,
            "test_images": 2246,
            "classes": ["person", "helmet", "safety_vest", "gloves",
                        "safety_footwear", "fire", "smoke"],
        },
        "output": {
            "best_pt": best_pt,
            "sha256": sha,
        },
        "phase": cfg.get("phase", "Phase 3.1 — Model Diagnosis, Correction & Retraining"),
        "project": "SafeSync",
    }

    meta_path = os.path.join(model_dir, "model_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    log.info(f"Metadata written: {meta_path}")

    # Also copy training config to model directory
    shutil.copy2(args.config, os.path.join(model_dir, "training_config.yaml"))

    log.info("Training script complete. Run evaluate.py next.")
    return model_dir


if __name__ == "__main__":
    args = parse_args()
    if not args.skip_preflight:
        run_preflight()
    train(args)

