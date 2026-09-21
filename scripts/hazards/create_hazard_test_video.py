"""
create_hazard_test_video.py — RAKSHYA VISION Phase 6
Creates a multi-scene realistic CCTV hazard test video (test_hazard_video.mp4)
combining real held-out test frames of:
  - Active industrial fire
  - Heavy smoke plume
  - Safe worker environment (no hazard)
  - Combined fire + smoke
"""

import os
import cv2

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEST_IMG_DIR = os.path.join(ROOT, "datasets", "processed", "images", "test")
OUTPUT_VIDEO = os.path.join(ROOT, "datasets", "test_hazard_video.mp4")

TARGET_W, TARGET_H = 640, 480
FPS = 15
FRAMES_PER_SCENE = 15


def create_hazard_video():
    scenes = [
        # Scene 1: Active fire
        "fs_abc055_jpg.rf.287911bfe98a5c962a64dfb67ef8e322.jpg",
        # Scene 2: Dense smoke
        "fs_24480_png_jpg.rf.4d48a391ee55c5e066e3a4ea18feabc7.jpg",
        # Scene 3: Safe worker environment (clearing period)
        "cppe_00000070_jpg.rf.00daeaf9d7220853beba957400594103.jpg",
        # Scene 4: Another fire scene
        "fs_abc074_jpg.rf.dc867d4b3985cb877ca54cb83de5c5bf.jpg",
        # Scene 5: Smoke scene
        "fs_22360_png_jpg.rf.ee2d689db9cacc7c925bfb9041d7affa.jpg",
    ]

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, FPS, (TARGET_W, TARGET_H))

    total_written = 0
    for img_name in scenes:
        p = os.path.join(TEST_IMG_DIR, img_name)
        if not os.path.isfile(p):
            continue
        img = cv2.imread(p)
        if img is None:
            continue
        resized = cv2.resize(img, (TARGET_W, TARGET_H), interpolation=cv2.INTER_LINEAR)
        for _ in range(FRAMES_PER_SCENE):
            writer.write(resized)
            total_written += 1

    writer.release()
    print(f"[OK] Created hazard test video: {OUTPUT_VIDEO} ({total_written} frames at {FPS} FPS)")
    return OUTPUT_VIDEO


if __name__ == "__main__":
    create_hazard_video()
