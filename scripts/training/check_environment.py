"""
check_environment.py — RAKSHYA VISION Phase 3
Reports Python, PyTorch, Ultralytics, CUDA, GPU, RAM, disk,
and dataset image/label counts for all 3 splits.
"""

import sys
import os
import platform
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def separator(title=""):
    print(f"\n{'='*60}")
    if title:
        print(f"  {title}")
        print(f"{'='*60}")


def check_python():
    separator("PYTHON")
    print(f"  Version      : {sys.version}")
    print(f"  Executable   : {sys.executable}")
    print(f"  Platform     : {platform.platform()}")
    print(f"  Architecture : {platform.machine()}")


def check_pytorch():
    separator("PYTORCH")
    try:
        import torch
        print(f"  torch version    : {torch.__version__}")
        print(f"  CUDA available   : {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  CUDA version     : {torch.version.cuda}")
            print(f"  cuDNN version    : {torch.backends.cudnn.version()}")
            n = torch.cuda.device_count()
            print(f"  GPU count        : {n}")
            for i in range(n):
                props = torch.cuda.get_device_properties(i)
                vram_gb = props.total_memory / (1024 ** 3)
                print(f"  GPU[{i}]           : {props.name}  |  VRAM: {vram_gb:.2f} GB")
        else:
            print("  CUDA unavailable — CPU-only mode")
    except ImportError:
        print("  torch NOT installed")


def check_ultralytics():
    separator("ULTRALYTICS")
    try:
        import ultralytics
        print(f"  ultralytics version : {ultralytics.__version__}")
    except ImportError:
        print("  ultralytics NOT installed")


def check_system_resources():
    separator("SYSTEM RESOURCES")
    try:
        import psutil
        ram = psutil.virtual_memory()
        print(f"  Total RAM   : {ram.total / (1024**3):.2f} GB")
        print(f"  Available   : {ram.available / (1024**3):.2f} GB")
        print(f"  Used        : {ram.used / (1024**3):.2f} GB  ({ram.percent:.1f}%)")
        swap = psutil.swap_memory()
        print(f"  Swap Total  : {swap.total / (1024**3):.2f} GB")
        print(f"  CPU cores   : {psutil.cpu_count(logical=False)} physical / {psutil.cpu_count(logical=True)} logical")
    except ImportError:
        import resource_fallback  # noqa — fallback below
        pass

    # Disk for project root
    total, used, free = shutil.disk_usage(ROOT)
    print(f"\n  Disk (project drive):")
    print(f"    Total : {total / (1024**3):.1f} GB")
    print(f"    Used  : {used  / (1024**3):.1f} GB")
    print(f"    Free  : {free  / (1024**3):.1f} GB")


def check_dataset():
    separator("DATASET SPLITS")
    processed = os.path.join(ROOT, "datasets", "processed")
    splits = ["train", "val", "test"]
    for split in splits:
        img_dir = os.path.join(processed, "images", split)
        lbl_dir = os.path.join(processed, "labels", split)
        if os.path.isdir(img_dir):
            imgs = len([f for f in os.listdir(img_dir)
                        if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))])
        else:
            imgs = "MISSING"
        if os.path.isdir(lbl_dir):
            lbls = len([f for f in os.listdir(lbl_dir) if f.endswith(".txt")])
        else:
            lbls = "MISSING"
        print(f"  {split:6s} | images: {imgs:>6}  |  labels: {lbls:>6}")

    yaml_path = os.path.join(processed, "data.yaml")
    print(f"\n  data.yaml exists : {os.path.isfile(yaml_path)}")
    if os.path.isfile(yaml_path):
        with open(yaml_path) as f:
            print(f.read())


def check_misc_packages():
    separator("PACKAGE VERSIONS")
    packages = ["cv2", "numpy", "PIL", "matplotlib", "yaml"]
    for pkg in packages:
        try:
            mod = __import__(pkg)
            ver = getattr(mod, "__version__", "unknown")
            print(f"  {pkg:15s} : {ver}")
        except ImportError:
            print(f"  {pkg:15s} : NOT installed")


if __name__ == "__main__":
    check_python()
    check_pytorch()
    check_ultralytics()
    try:
        check_system_resources()
    except Exception as e:
        print(f"  (resource check error: {e})")
    check_dataset()
    check_misc_packages()
    separator("ENVIRONMENT CHECK COMPLETE")
