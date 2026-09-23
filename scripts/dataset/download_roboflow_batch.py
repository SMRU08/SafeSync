"""
download_roboflow_batch.py — RAKSHYA VISION
Downloads remaining Roboflow datasets into datasets/raw/ using the provided API key.
"""

import os
import sys
from roboflow import Roboflow

api_key = os.environ.get("ROBOFLOW_API_KEY")
if not api_key:
    print("Error: ROBOFLOW_API_KEY environment variable not set.")
    sys.exit(1)

rf = Roboflow(api_key=api_key)

tasks = [
    ("tpu-uwyxu", "safety-ppe-4", 1, "datasets/raw/safety_ppe_4"),
    ("safety-jmser", "safety_ppe", 23, "datasets/raw/safety_ppe"),
    ("bangga", "ppe-hgqzw", 6, "datasets/raw/bangga_ppe"),
]

for ws, pid, ver, target in tasks:
    if os.path.exists(target) and any(f.endswith((".jpg", ".png", ".jpeg")) for r, d, files in os.walk(target) for f in files):
        print(f"Skipping {target}: already downloaded and verified.")
        continue

    print(f"\n{'='*50}\nStarting download: {ws}/{pid} v{ver} -> {target}...")
    try:
        proj = rf.workspace(ws).project(pid)
        v = proj.version(ver)
        v.download("yolov8", location=target, overwrite=True)
        imgs = sum(len(files) for r, d, files in os.walk(target) if any(f.endswith((".jpg", ".png", ".jpeg")) for f in files))
        print(f"SUCCESS: {target} successfully downloaded with {imgs} images!")
    except Exception as e:
        print(f"ERROR downloading {ws}/{pid} v{ver}: {e}")
