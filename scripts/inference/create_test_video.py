"""
create_test_video.py — SafeSync Phase 4
Generates a realistic test video from the held-out test split images.
Includes scenes with helmets, vests, workers, and fire/smoke.
"""

import os
import glob
import cv2

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEST_IMG_DIR = os.path.join(ROOT, "datasets", "processed", "images", "test")
OUTPUT_VIDEO = os.path.join(ROOT, "datasets", "test_safety_video.mp4")

TARGET_W, TARGET_H = 640, 480
FPS = 15
FRAMES_PER_IMAGE = 15  # 1 second per scene
MAX_SCENES = 8         # 8 diverse scenes = 120 frames total (8 seconds of video)


def create_video():
    # Curate verified test scenes with workers, helmets, vests, and fire/smoke
    target_bases = [
        "cppe_00000070_jpg.rf.00daeaf9d7220853beba957400594103",  # person + helmet + vest
        "cppe_00000151_jpg.rf.e84faf7e4f19a5091d24bea2bf944a16",  # person + helmet
        "cppe_00000169_jpg.rf.2dadfdbc93d2b3d5edcfa68a55f96dbb",  # person + helmet
        "cppe_00000190_jpg.rf.4ab32c663db52edf20b8a01ee328208b",  # person + helmet + vest
        "cppe_00000239_jpg.rf.ae2ee3ab4b8a19f7b10428cd8228f6fa",  # person + helmet + vest
    ]

    selected = []
    for b in target_bases:
        for ext in [".jpg", ".png"]:
            p = os.path.join(TEST_IMG_DIR, b + ext)
            if os.path.isfile(p):
                selected.append(p)
                break

    # Add 1 fire/smoke image for multi-modal coverage
    hazard_imgs = sorted(glob.glob(os.path.join(TEST_IMG_DIR, "dfire_*.jpg")) + glob.glob(os.path.join(TEST_IMG_DIR, "dfire_*.png")))
    if hazard_imgs:
        selected.append(hazard_imgs[0])

    if not selected:
        # Fallback to any images
        selected = (glob.glob(os.path.join(TEST_IMG_DIR, "*.jpg")) + glob.glob(os.path.join(TEST_IMG_DIR, "*.png")))[:MAX_SCENES]

    print(f"Creating test video from {len(selected)} real test images...")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, FPS, (TARGET_W, TARGET_H))

    total_written = 0
    for img_path in selected:
        img = cv2.imread(img_path)
        if img is None:
            continue
        resized = cv2.resize(img, (TARGET_W, TARGET_H), interpolation=cv2.INTER_LINEAR)
        # Write multiple frames for each image to simulate continuous CCTV footage
        for _ in range(FRAMES_PER_IMAGE):
            writer.write(resized)
            total_written += 1

    writer.release()
    print(f"[OK] Generated test video: '{OUTPUT_VIDEO}' ({total_written} frames at {FPS} FPS, size: {os.path.getsize(OUTPUT_VIDEO):,} bytes)")
    return OUTPUT_VIDEO


if __name__ == "__main__":
    create_video()
