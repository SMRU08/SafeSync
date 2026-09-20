"""
create_test_video.py — RAKSHYA VISION Phase 4
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
    img_files = glob.glob(os.path.join(TEST_IMG_DIR, "*.jpg")) + glob.glob(os.path.join(TEST_IMG_DIR, "*.png"))
    if not img_files:
        raise FileNotFoundError(f"No test images found in {TEST_IMG_DIR}")

    # Select 8 diverse images
    selected = img_files[:MAX_SCENES]
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
