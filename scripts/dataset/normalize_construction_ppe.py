"""
scripts/dataset/normalize_construction_ppe.py — SafeSync
Normalizes the Ultralytics Construction-PPE dataset into SafeSync's canonical 7-class ontology:
- 6 (Person)        -> 0 (person)
- 0 (helmet)        -> 1 (helmet)
- 2 (vest)          -> 2 (safety_vest)
- 1 (gloves)        -> 3 (gloves)
- 3 (boots)         -> 4 (safety_footwear)
- Strips: 4 (goggles), 5 (none), 7 (no_helmet), 8 (no_goggle), 9 (no_gloves), 10 (no_boots)
"""

import os
import shutil
from pathlib import Path
from collections import Counter
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT / "datasets" / "raw" / "ultralytics_construction_ppe"
DST_DIR = ROOT / "datasets" / "normalized" / "construction_ppe"

CANONICAL_CLASSES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}

MAPPING = {
    6: 0,  # Person -> person
    0: 1,  # helmet -> helmet
    2: 2,  # vest -> safety_vest
    1: 3,  # gloves -> gloves
    3: 4,  # boots -> safety_footwear
}

DROPPED_CLASSES = {4, 5, 7, 8, 9, 10}


def normalize():
    print(f"Normalizing Construction-PPE from {SRC_DIR} to {DST_DIR} ...")
    if not SRC_DIR.exists():
        raise FileNotFoundError(f"Source directory not found: {SRC_DIR}")

    splits = ["train", "val", "test"]
    stats = {s: Counter() for s in splits}
    dropped_counts = {s: Counter() for s in splits}
    img_counts = {s: 0 for s in splits}

    for s in splits:
        src_img_dir = SRC_DIR / "images" / s
        src_lbl_dir = SRC_DIR / "labels" / s
        dst_img_dir = DST_DIR / "images" / s
        dst_lbl_dir = DST_DIR / "labels" / s

        dst_img_dir.mkdir(parents=True, exist_ok=True)
        dst_lbl_dir.mkdir(parents=True, exist_ok=True)

        if not src_img_dir.exists():
            print(f"Warning: {src_img_dir} does not exist, skipping.")
            continue

        for img_file in src_img_dir.glob("*.*"):
            if img_file.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                continue

            # Link or copy image
            dst_img_path = dst_img_dir / img_file.name
            if not dst_img_path.exists():
                try:
                    os.link(img_file, dst_img_path)
                except Exception:
                    shutil.copy2(img_file, dst_img_path)

            img_counts[s] += 1

            # Process label file
            lbl_file = src_lbl_dir / f"{img_file.stem}.txt"
            dst_lbl_path = dst_lbl_dir / f"{img_file.stem}.txt"

            valid_lines = []
            if lbl_file.exists():
                with open(lbl_file, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            raw_cls = int(float(parts[0]))
                            if raw_cls in MAPPING:
                                target_cls = MAPPING[raw_cls]
                                valid_lines.append(f"{target_cls} {' '.join(parts[1:5])}\n")
                                stats[s][target_cls] += 1
                            elif raw_cls in DROPPED_CLASSES:
                                dropped_counts[s][raw_cls] += 1

            with open(dst_lbl_path, "w", encoding="utf-8") as f:
                f.writelines(valid_lines)

    # Generate data.yaml
    data_yaml = {
        "path": str(DST_DIR.resolve()).replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": 7,
        "names": CANONICAL_CLASSES,
    }

    yaml_path = DST_DIR / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data_yaml, f, sort_keys=False)

    print("\n--- Normalization Complete ---")
    print(f"Data config written to: {yaml_path}")
    for s in splits:
        print(f"\n[{s.upper()}] Images: {img_counts[s]}")
        print(f"  Canonical BBoxes: {dict(stats[s])}")
        print(f"  Dropped Negative BBoxes: {dict(dropped_counts[s])}")

    return yaml_path


if __name__ == "__main__":
    normalize()
