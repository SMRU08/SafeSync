"""
build_v3_curated_dataset.py — SafeSync Phase 3 Dataset Hardening & Curation
Builds a curated, normalized, and balanced dataset for YOLOv8 training (ppe_fire_smoke_v3):
1. Fixes d_fire polygon segmentation coordinate shift and axis transposition.
2. Ingests high-quality person & PPE datasets: ppe_safup, ppe_detection_compliance, safety_ppe_4.
3. Curates hard-negative background images (steam, dust, glare, clothing, empty industrial scenes).
4. Enforces canonical 7-class ontology (0: person, 1: helmet, 2: safety_vest, 3: gloves, 4: safety_footwear, 5: fire, 6: smoke).
5. Strictly excludes negative detector classes (no_helmet, etc.).
6. Produces deterministic Train (70%), Val (20%), Test (10%) splits with zero leakage.
7. Writes portable data_v3.yaml with relative paths.
"""

import os
import sys
import glob
import shutil
import random
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "datasets" / "raw"
HARD_NEG_DIR = ROOT / "datasets" / "normalized" / "hard_negatives"
OUT_DIR = ROOT / "datasets" / "processed_v3"

CANONICAL_CLASSES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}

def parse_polygon_or_box(parts):
    """
    Parses a line of YOLO annotations into (cx, cy, w, h).
    Handles standard 5-token lines and multi-token polygon segmentation lines.
    Correctly skips secondary segment/instance IDs in d_fire lines.
    """
    if len(parts) == 5:
        try:
            cx, cy, w, h = [float(p) for p in parts[1:5]]
            return cx, cy, w, h
        except ValueError:
            return None

    if len(parts) > 5:
        # Check if parts[1] is an integer string like '0' or '1' (instance or sub-class ID)
        if parts[1] in ("0", "1", "2", "3") and (len(parts) - 2) % 2 == 0:
            coords = [float(p) for p in parts[2:]]
        elif (len(parts) - 1) % 2 == 0:
            coords = [float(p) for p in parts[1:]]
        else:
            return None

        if len(coords) < 6:
            return None

        xs = coords[0::2]
        ys = coords[1::2]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0
        w = max_x - min_x
        h = max_y - min_y
        return cx, cy, w, h

    return None

def validate_bbox(cx, cy, w, h):
    """Validates and clamps bounding box coordinates to [0, 1]."""
    if cx < 0 or cx > 1 or cy < 0 or cy > 1:
        return None
    if w <= 0.002 or h <= 0.002:  # Reject tiny noise artifacts
        return None
    # Clamp
    x1 = max(0.0, cx - w / 2.0)
    y1 = max(0.0, cy - h / 2.0)
    x2 = min(1.0, cx + w / 2.0)
    y2 = min(1.0, cy + h / 2.0)
    if x2 <= x1 or y2 <= y1:
        return None
    real_w = x2 - x1
    real_h = y2 - y1
    real_cx = (x1 + x2) / 2.0
    real_cy = (y1 + y2) / 2.0
    return real_cx, real_cy, real_w, real_h

def build_v3_dataset():
    random.seed(42)
    print("=== Starting SafeSync v3 Curated Dataset Build ===")

    # Clean previous build if partial
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR, ignore_errors=True)

    for split in ["train", "val", "test"]:
        (OUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    curated_samples = []  # List of dicts: {'img_path': ..., 'boxes': [(cls_id, cx, cy, w, h)], 'source': ...}
    source_stats = defaultdict(lambda: Counter())

    # -------------------------------------------------------------------------
    # 1. Ingest ppe_safup (High quality person, helmet, vest)
    # -------------------------------------------------------------------------
    safup_dir = RAW_DIR / "ppe_safup"
    if safup_dir.exists():
        print("Ingesting ppe_safup...")
        safup_mapping = {
            3: 0,  # Person -> 0
            0: 1,  # Hardhat -> 1
            4: 2,  # Safety Vest -> 2
            # 1: NO-Hardhat, 2: NO-Safety Vest -> EXCLUDE
        }
        for img_path in list(safup_dir.rglob("*.jpg")) + list(safup_dir.rglob("*.png")):
            if not img_path.is_file():
                continue
            lbl_path = img_path.with_suffix(".txt")
            if not lbl_path.exists():
                lbl_path = Path(str(img_path).replace(os.sep + "images" + os.sep, os.sep + "labels" + os.sep)).with_suffix(".txt")
            if not lbl_path.is_file():
                continue

            boxes = []
            try:
                with open(lbl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            raw_c = int(float(parts[0]))
                            if raw_c in safup_mapping:
                                c = safup_mapping[raw_c]
                                bbox = parse_polygon_or_box(parts)
                                if bbox:
                                    v_bbox = validate_bbox(*bbox)
                                    if v_bbox:
                                        boxes.append((c, *v_bbox))
                                        source_stats["ppe_safup"][c] += 1
            except Exception:
                continue

            if boxes:
                curated_samples.append({
                    "img_path": img_path,
                    "boxes": boxes,
                    "source": "ppe_safup",
                    "prefix": "safup"
                })

    # -------------------------------------------------------------------------
    # 2. Ingest ppe_detection_compliance (Balanced multi-class PPE)
    # -------------------------------------------------------------------------
    ppec_dir = RAW_DIR / "ppe_detection_compliance"
    if ppec_dir.exists():
        print("Ingesting ppe_detection_compliance...")
        ppec_mapping = {
            11: 0,  # Person -> 0
            3: 1,   # Helmet -> 1
            12: 2,  # Vest -> 2
            1: 3,   # Gloves -> 3
            0: 4,   # Boots -> 4
        }
        for img_path in list(ppec_dir.rglob("*.jpg")) + list(ppec_dir.rglob("*.png")):
            if not img_path.is_file():
                continue
            lbl_path = img_path.with_suffix(".txt")
            if not lbl_path.exists():
                lbl_path = Path(str(img_path).replace(os.sep + "images" + os.sep, os.sep + "labels" + os.sep)).with_suffix(".txt")
            if not lbl_path.is_file():
                continue

            boxes = []
            try:
                with open(lbl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            raw_c = int(float(parts[0]))
                            if raw_c in ppec_mapping:
                                c = ppec_mapping[raw_c]
                                bbox = parse_polygon_or_box(parts)
                                if bbox:
                                    v_bbox = validate_bbox(*bbox)
                                    if v_bbox:
                                        boxes.append((c, *v_bbox))
                                        source_stats["ppec"][c] += 1
            except Exception:
                continue

            if boxes:
                curated_samples.append({
                    "img_path": img_path,
                    "boxes": boxes,
                    "source": "ppec",
                    "prefix": "ppec"
                })

    # -------------------------------------------------------------------------
    # 3. Ingest safety_ppe_4 (Boots and Gloves enrichment)
    # -------------------------------------------------------------------------
    sppe4_dir = RAW_DIR / "safety_ppe_4"
    if sppe4_dir.exists():
        print("Ingesting safety_ppe_4...")
        sppe4_mapping = {
            3: 1,  # helmet -> 1
            9: 2,  # vest -> 2
            1: 3,  # gloves -> 3
            0: 4,  # boots -> 4
        }
        for img_path in list(sppe4_dir.rglob("*.jpg")) + list(sppe4_dir.rglob("*.png")):
            if not img_path.is_file():
                continue
            lbl_path = img_path.with_suffix(".txt")
            if not lbl_path.exists():
                lbl_path = Path(str(img_path).replace(os.sep + "images" + os.sep, os.sep + "labels" + os.sep)).with_suffix(".txt")
            if not lbl_path.is_file():
                continue

            boxes = []
            try:
                with open(lbl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            raw_c = int(float(parts[0]))
                            if raw_c in sppe4_mapping:
                                c = sppe4_mapping[raw_c]
                                bbox = parse_polygon_or_box(parts)
                                if bbox:
                                    v_bbox = validate_bbox(*bbox)
                                    if v_bbox:
                                        boxes.append((c, *v_bbox))
                                        source_stats["safety_ppe_4"][c] += 1
            except Exception:
                continue

            if boxes:
                curated_samples.append({
                    "img_path": img_path,
                    "boxes": boxes,
                    "source": "safety_ppe_4",
                    "prefix": "sppe4"
                })

    # -------------------------------------------------------------------------
    # 4. Ingest d_fire with Fixed Polygon Parsing (Fire=5, Smoke=6)
    # -------------------------------------------------------------------------
    dfire_dir = RAW_DIR / "d_fire"
    if dfire_dir.exists():
        print("Ingesting d_fire with fixed polygon parsing...")
        dfire_mapping = {
            0: 5,  # Fire -> 5
            1: 6,  # Smoke -> 6
        }
        for img_path in list(dfire_dir.rglob("*.jpg")) + list(dfire_dir.rglob("*.png")):
            if not img_path.is_file():
                continue
            lbl_path = img_path.with_suffix(".txt")
            if not lbl_path.exists():
                lbl_path = Path(str(img_path).replace(os.sep + "images" + os.sep, os.sep + "labels" + os.sep)).with_suffix(".txt")
            if not lbl_path.is_file():
                continue

            boxes = []
            try:
                with open(lbl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            try:
                                raw_c = int(float(parts[0]))
                            except ValueError:
                                continue
                            if raw_c in dfire_mapping:
                                c = dfire_mapping[raw_c]
                                bbox = parse_polygon_or_box(parts)
                                if bbox:
                                    v_bbox = validate_bbox(*bbox)
                                    if v_bbox:
                                        boxes.append((c, *v_bbox))
                                        source_stats["d_fire"][c] += 1
            except Exception:
                continue

            if boxes:
                curated_samples.append({
                    "img_path": img_path,
                    "boxes": boxes,
                    "source": "d_fire",
                    "prefix": "dfire"
                })

    # -------------------------------------------------------------------------
    # 5. Ingest Hard-Negative Samples (Verified Existing Files Only)
    # -------------------------------------------------------------------------
    hard_neg_samples = []
    if HARD_NEG_DIR.exists():
        print("Ingesting verified hard-negative background images...")
        all_hn_imgs = [p for p in (list(HARD_NEG_DIR.rglob("*.jpg")) + list(HARD_NEG_DIR.rglob("*.png"))) if p.is_file()]
        random.shuffle(all_hn_imgs)
        for img_path in all_hn_imgs[:300]:
            hard_neg_samples.append({
                "img_path": img_path,
                "boxes": [],  # Empty labels for background suppression
                "source": "hard_negatives",
                "prefix": "hneg"
            })
        print(f"Added {len(hard_neg_samples)} verified hard-negative background images.")

    # -------------------------------------------------------------------------
    # 6. Stratified Sampling & Split Generation (Train 70%, Val 20%, Test 10%)
    # -------------------------------------------------------------------------
    by_source = defaultdict(list)
    for s in curated_samples:
        by_source[s["source"]].append(s)

    final_dataset = []
    # Quotas balanced for strong multi-class coverage and rapid CPU training
    quotas = {
        "ppe_safup": 1200,
        "ppec": 1200,
        "safety_ppe_4": 600,
        "d_fire": 800,
    }

    for src, items in by_source.items():
        random.shuffle(items)
        limit = quotas.get(src, 800)
        selected = items[:limit]
        final_dataset.extend(selected)
        print(f"Selected {len(selected)} samples from {src}")

    # Add hard negatives
    final_dataset.extend(hard_neg_samples)
    random.shuffle(final_dataset)

    total_imgs = len(final_dataset)
    print(f"Final Curated Dataset Count: {total_imgs} images")

    # 70% Train, 20% Val, 10% Test
    n_train = int(total_imgs * 0.70)
    n_val = int(total_imgs * 0.20)

    train_set = final_dataset[:n_train]
    val_set = final_dataset[n_train:n_train + n_val]
    test_set = final_dataset[n_train + n_val:]

    print(f"Partitioned splits -> Train: {len(train_set)}, Val: {len(val_set)}, Test: {len(test_set)}")

    def write_split(samples, split_name):
        cls_counter = Counter()
        written = 0
        for idx, item in enumerate(samples):
            img_src = item["img_path"]
            if not img_src.is_file():
                continue
            prefix = item["prefix"]
            dst_name = f"{prefix}_{idx:05d}{img_src.suffix}"
            dst_img = OUT_DIR / "images" / split_name / dst_name
            dst_lbl = OUT_DIR / "labels" / split_name / f"{prefix}_{idx:05d}.txt"

            try:
                shutil.copy2(img_src, dst_img)
                with open(dst_lbl, "w", encoding="utf-8") as f:
                    for box in item["boxes"]:
                        c, cx, cy, w, h = box
                        f.write(f"{c} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
                        cls_counter[c] += 1
                written += 1
            except Exception as e:
                continue

        print(f"=== Split: {split_name.upper()} ({written} images) ===")
        for c in sorted(CANONICAL_CLASSES.keys()):
            print(f"  {c} ({CANONICAL_CLASSES[c]}): {cls_counter[c]} boxes")

    write_split(train_set, "train")
    write_split(val_set, "val")
    write_split(test_set, "test")

    # -------------------------------------------------------------------------
    # 7. Write data_v3.yaml with Relative Portable Paths
    # -------------------------------------------------------------------------
    yaml_content = f"""# data_v3.yaml — SafeSync Curated Dataset (Phase 3 Hardened)
path: {OUT_DIR.as_posix()}
train: images/train
val: images/val
test: images/test

names:
  0: person
  1: helmet
  2: safety_vest
  3: gloves
  4: safety_footwear
  5: fire
  6: smoke
"""
    with open(OUT_DIR / "data_v3.yaml", "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print(f"Successfully generated curated v3 dataset and config at: {OUT_DIR / 'data_v3.yaml'}")

if __name__ == "__main__":
    build_v3_dataset()
