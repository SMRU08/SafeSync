r"""
scripts/dataset/separate_categories.py — SafeSync Category Separator
====================================================================
Separates the unified SafeSync dataset into domain-specific sub-datasets:
  1. fire       (Fire & Smoke)
  2. vest       (Safety Vest)
  3. helmet     (Safety Helmet / Hard Hat)
  4. footwear   (Safety Footwear / Boots)

Uses fast OS hardlinks (or file copy fallback) to preserve train / val / test
splits and generate a self-contained data.yaml for each category.
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = ROOT / "datasets"
CATEGORIES_DIR = DATASETS_DIR / "categories"

# Mapping of target category to canonical SafeSync class IDs
CATEGORY_DEFINITIONS = {
    "fire": {
        "class_ids": [5, 6],  # fire, smoke
        "description": "Fire & Smoke Combustion Hazards",
        "names": {5: "fire", 6: "smoke"},
    },
    "vest": {
        "class_ids": [2],     # safety_vest
        "description": "High-Visibility Safety Vests",
        "names": {2: "safety_vest"},
    },
    "helmet": {
        "class_ids": [1],     # helmet
        "description": "Industrial Helmets & Hard Hats",
        "names": {1: "helmet"},
    },
    "footwear": {
        "class_ids": [4],     # safety_footwear
        "description": "Steel-Toe Safety Footwear & Boots",
        "names": {4: "safety_footwear"},
    },
}

ALL_CANONICAL_NAMES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}


def link_or_copy(src: Path, dst: Path):
    """Creates a hardlink to avoid duplicating disk space; falls back to copy."""
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except Exception:
        shutil.copy2(src, dst)


def separate_categories():
    print("=" * 70)
    print("SafeSync: Separating Dataset into Categories (Fire, Vest, Helmet, Footwear)")
    print("=" * 70)

    src_img_base = DATASETS_DIR / "images"
    src_lbl_base = DATASETS_DIR / "labels"

    if not src_img_base.exists() or not src_lbl_base.exists():
        raise FileNotFoundError(f"Source dataset not found at {DATASETS_DIR}")

    splits = ["train", "val", "test"]
    stats = defaultdict(lambda: defaultdict(int))

    for cat_name, cat_meta in CATEGORY_DEFINITIONS.items():
        cat_dir = CATEGORIES_DIR / cat_name
        cat_target_ids = set(cat_meta["class_ids"])

        print(f"\nProcessing Category: [{cat_name.upper()}] ({cat_meta['description']})")

        for split in splits:
            src_lbl_dir = src_lbl_base / split
            src_img_dir = src_img_base / split

            dst_lbl_dir = cat_dir / "labels" / split
            dst_img_dir = cat_dir / "images" / split
            dst_lbl_dir.mkdir(parents=True, exist_ok=True)
            dst_img_dir.mkdir(parents=True, exist_ok=True)

            if not src_lbl_dir.exists():
                continue

            for lbl_file in src_lbl_dir.glob("*.txt"):
                # Read annotations to check if this image contains target category classes
                matching_lines = []
                with open(lbl_file, "r", encoding="utf-8") as fp:
                    for line in fp:
                        parts = line.strip().split()
                        if parts and int(parts[0]) in cat_target_ids:
                            matching_lines.append(line)

                if matching_lines:
                    stem = lbl_file.stem
                    # Find corresponding image file (try .jpg, .jpeg, .png)
                    img_match = None
                    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
                        cand = src_img_dir / f"{stem}{ext}"
                        if cand.exists():
                            img_match = cand
                            break

                    if img_match:
                        # 1. Link image
                        dst_img = dst_img_dir / img_match.name
                        link_or_copy(img_match, dst_img)

                        # 2. Write category-specific label file
                        dst_lbl = dst_lbl_dir / lbl_file.name
                        with open(dst_lbl, "w", encoding="utf-8") as out_fp:
                            out_fp.writelines(matching_lines)

                        stats[cat_name][split] += 1

        # Write data.yaml for this specific category
        cat_yaml_path = cat_dir / "data.yaml"
        cat_data_dict = {
            "path": str(cat_dir.resolve()).replace("\\", "/"),
            "train": "images/train",
            "val": "images/val",
            "test": "images/test",
            "nc": 7,
            "names": ALL_CANONICAL_NAMES,  # Keep canonical IDs for model compatibility
        }
        with open(cat_yaml_path, "w", encoding="utf-8") as yfp:
            yaml.dump(cat_data_dict, yfp, sort_keys=False)

        total_cat = sum(stats[cat_name].values())
        print(f"  -> Created {cat_dir}")
        print(f"  -> Total: {total_cat} images (train={stats[cat_name]['train']}, val={stats[cat_name]['val']}, test={stats[cat_name]['test']})")
        print(f"  -> Config: {cat_yaml_path}")

    print("\n" + "=" * 70)
    print("Category Separation Summary:")
    print("=" * 70)
    for cat_name in CATEGORY_DEFINITIONS:
        s = stats[cat_name]
        tot = sum(s.values())
        print(f"  {cat_name.upper():<12}: total={tot:<5} | train={s['train']:<5} | val={s['val']:<4} | test={s['test']:<4}")
    print("=" * 70)


if __name__ == "__main__":
    separate_categories()
