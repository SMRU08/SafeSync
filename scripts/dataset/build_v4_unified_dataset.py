"""
scripts/dataset/build_v4_unified_dataset.py — SafeSync Unified Dataset Builder v4
Integrates verified existing datasets + NEW Hugging Face bucket + NEW Ultralytics Construction-PPE + NEW Kaggle DataCluster Fire & Smoke.
Features:
1. Normalizes all bounding boxes to canonical 7-class ontology.
2. Strips invalid polygons and bad boxes.
3. Cryptographic SHA-256 deduplication across all sources.
4. Curates hard-negative background images.
5. Generates deterministic 70% Train / 20% Val / 10% Test split with zero leakage.
6. Produces dataset.yaml, manifest.csv, and dataset_stats.json.
7. Renders visual QA sample previews with annotated bounding boxes.
"""

import os
import sys
import glob
import json
import csv
import shutil
import random
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter, defaultdict
from tqdm import tqdm
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "datasets" / "raw"
DATA_RAW_DIR = ROOT / "data" / "raw"
HARD_NEG_DIR = ROOT / "datasets" / "normalized" / "hard_negatives"
OUT_DIR = ROOT / "data" / "processed" / "safesync"
PREVIEW_DIR = ROOT / "reports" / "dataset_preview"

CANONICAL_CLASSES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}

CLASS_COLORS = {
    0: "#3B82F6",  # person: blue
    1: "#F59E0B",  # helmet: amber
    2: "#10B981",  # safety_vest: emerald
    3: "#8B5CF6",  # gloves: purple
    4: "#EC4899",  # safety_footwear: pink
    5: "#EF4444",  # fire: red
    6: "#94A3B8",  # smoke: gray
}


def compute_sha256(filepath):
    """Compute SHA-256 hash of file content."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_polygon_or_box(parts):
    """
    Parses a line of YOLO annotations into (cx, cy, w, h).
    Handles standard 5-token lines and multi-token polygon segmentation lines.
    """
    if len(parts) == 5:
        try:
            cx, cy, w, h = [float(p) for p in parts[1:5]]
            return cx, cy, w, h
        except ValueError:
            return None

    if len(parts) > 5:
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
    if w <= 0.002 or h <= 0.002:
        return None
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


def build_v4_dataset():
    random.seed(42)
    print("====================================================================")
    print("  SafeSync v4 Unified Dataset Construction, Normalization & Deduplication")
    print("====================================================================")

    if OUT_DIR.exists():
        print(f"Cleaning existing output directory: {OUT_DIR}")
        shutil.rmtree(OUT_DIR, ignore_errors=True)

    for split in ["train", "val", "test"]:
        (OUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    seen_hashes = {}  # hash -> first_img_path
    duplicates_detected = 0
    curated_samples = []
    source_stats = defaultdict(lambda: Counter())

    # -------------------------------------------------------------------------
    # 1. Existing: ppe_safup
    # -------------------------------------------------------------------------
    safup_dir = RAW_DIR / "ppe_safup"
    if safup_dir.exists():
        print("[1/8] Ingesting ppe_safup (person, helmet, safety_vest)...")
        safup_mapping = {3: 0, 0: 1, 4: 2}
        count = 0
        for img_path in list(safup_dir.rglob("*.jpg")) + list(safup_dir.rglob("*.png")):
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
                    "prefix": "safup",
                })
                count += 1
        print(f"      -> Ingested {count} candidate samples from ppe_safup")

    # -------------------------------------------------------------------------
    # 2. Existing: ppe_detection_compliance (ppec)
    # -------------------------------------------------------------------------
    ppec_dir = RAW_DIR / "ppe_detection_compliance"
    if ppec_dir.exists():
        print("[2/8] Ingesting ppe_detection_compliance (person, helmet, vest, gloves, boots)...")
        ppec_mapping = {11: 0, 3: 1, 12: 2, 1: 3, 0: 4}
        count = 0
        for img_path in list(ppec_dir.rglob("*.jpg")) + list(ppec_dir.rglob("*.png")):
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
                    "prefix": "ppec",
                })
                count += 1
        print(f"      -> Ingested {count} candidate samples from ppe_detection_compliance")

    # -------------------------------------------------------------------------
    # 3. Existing: safety_ppe_4
    # -------------------------------------------------------------------------
    sppe4_dir = RAW_DIR / "safety_ppe_4"
    if sppe4_dir.exists():
        print("[3/8] Ingesting safety_ppe_4 (helmet, vest, gloves, footwear)...")
        sppe4_mapping = {3: 1, 9: 2, 1: 3, 0: 4}
        count = 0
        for img_path in list(sppe4_dir.rglob("*.jpg")) + list(sppe4_dir.rglob("*.png")):
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
                    "prefix": "sppe4",
                })
                count += 1
        print(f"      -> Ingested {count} candidate samples from safety_ppe_4")

    # -------------------------------------------------------------------------
    # 4. Existing: d_fire (Corrected polygon segmentation)
    # -------------------------------------------------------------------------
    dfire_dir = RAW_DIR / "d_fire"
    if dfire_dir.exists():
        print("[4/8] Ingesting d_fire (fire=5, smoke=6)...")
        dfire_mapping = {0: 5, 1: 6}
        count = 0
        for img_path in list(dfire_dir.rglob("*.jpg")) + list(dfire_dir.rglob("*.png")):
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
                    "prefix": "dfire",
                })
                count += 1
        print(f"      -> Ingested {count} candidate samples from d_fire")

    # -------------------------------------------------------------------------
    # 5. NEW: Hugging Face Bucket (smrutiranjannayakcs/PPE_Detection-bucket)
    # -------------------------------------------------------------------------
    hf_dir = DATA_RAW_DIR / "huggingface" / "PPE_Detection-bucket" / "extracted"
    if hf_dir.exists():
        print("[5/8] Ingesting NEW Hugging Face Bucket PPE dataset...")
        # data.yaml names: ['Gloves', 'Vest', 'goggles', 'helmet', 'mask', 'safety_shoe']
        # 0: Gloves -> 3
        # 1: Vest -> 2
        # 2: goggles -> EXCLUDE
        # 3: helmet -> 1
        # 4: mask -> EXCLUDE
        # 5: safety_shoe -> 4
        hf_mapping = {0: 3, 1: 2, 3: 1, 5: 4}
        count = 0
        for img_path in list(hf_dir.rglob("*.jpg")) + list(hf_dir.rglob("*.png")):
            lbl_path = Path(str(img_path).replace(os.sep + "images" + os.sep, os.sep + "labels" + os.sep)).with_suffix(".txt")
            if not lbl_path.is_file():
                lbl_path = img_path.with_suffix(".txt")
            if not lbl_path.is_file():
                continue

            boxes = []
            try:
                with open(lbl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            raw_c = int(float(parts[0]))
                            if raw_c in hf_mapping:
                                c = hf_mapping[raw_c]
                                bbox = parse_polygon_or_box(parts)
                                if bbox:
                                    v_bbox = validate_bbox(*bbox)
                                    if v_bbox:
                                        boxes.append((c, *v_bbox))
                                        source_stats["hf_smruti_ppe_bucket"][c] += 1
            except Exception:
                continue

            if boxes:
                curated_samples.append({
                    "img_path": img_path,
                    "boxes": boxes,
                    "source": "hf_smruti_ppe_bucket",
                    "prefix": "hfbkt",
                })
                count += 1
        print(f"      -> Ingested {count} candidate samples from HF Bucket PPE")

    # -------------------------------------------------------------------------
    # 6. NEW: Ultralytics Construction-PPE
    # -------------------------------------------------------------------------
    cppe_dir = DATA_RAW_DIR / "construction_ppe"
    if cppe_dir.exists():
        print("[6/8] Ingesting NEW Ultralytics Construction-PPE...")
        # 0: helmet -> 1, 1: gloves -> 3, 2: vest -> 2, 3: boots -> 4, 6: Person -> 0
        cppe_mapping = {0: 1, 1: 3, 2: 2, 3: 4, 6: 0}
        count = 0
        for img_path in list(cppe_dir.rglob("*.jpg")) + list(cppe_dir.rglob("*.png")):
            lbl_path = Path(str(img_path).replace(os.sep + "images" + os.sep, os.sep + "labels" + os.sep)).with_suffix(".txt")
            if not lbl_path.is_file():
                lbl_path = img_path.with_suffix(".txt")
            if not lbl_path.is_file():
                continue

            boxes = []
            try:
                with open(lbl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            raw_c = int(float(parts[0]))
                            if raw_c in cppe_mapping:
                                c = cppe_mapping[raw_c]
                                bbox = parse_polygon_or_box(parts)
                                if bbox:
                                    v_bbox = validate_bbox(*bbox)
                                    if v_bbox:
                                        boxes.append((c, *v_bbox))
                                        source_stats["ultralytics_construction_ppe"][c] += 1
            except Exception:
                continue

            if boxes:
                curated_samples.append({
                    "img_path": img_path,
                    "boxes": boxes,
                    "source": "ultralytics_construction_ppe",
                    "prefix": "cppe",
                })
                count += 1
        print(f"      -> Ingested {count} candidate samples from Construction-PPE")

    # -------------------------------------------------------------------------
    # 7. NEW: Kaggle DataCluster Fire and Smoke
    # -------------------------------------------------------------------------
    dc_xml_dir = DATA_RAW_DIR / "datacluster_fire_smoke" / "Annotations"
    dc_img_dir = DATA_RAW_DIR / "datacluster_fire_smoke" / "Datacluster Fire and Smoke Sample"
    if dc_xml_dir.exists():
        print("[7/8] Ingesting NEW Kaggle DataCluster Fire and Smoke Sample...")
        count = 0
        for xf in dc_xml_dir.rglob("*.xml"):
            try:
                tree = ET.parse(xf)
                root = tree.getroot()
                size = root.find("size")
                w = float(size.find("width").text)
                h = float(size.find("height").text)
                if w <= 0 or h <= 0:
                    continue

                boxes = []
                for obj in root.findall("object"):
                    name = obj.find("name").text.strip().lower()
                    if "fire" in name:
                        c = 5
                    elif "smoke" in name:
                        c = 6
                    else:
                        continue

                    bb = obj.find("bndbox")
                    xmin = float(bb.find("xmin").text)
                    ymin = float(bb.find("ymin").text)
                    xmax = float(bb.find("xmax").text)
                    ymax = float(bb.find("ymax").text)
                    cx = ((xmin + xmax) / 2.0) / w
                    cy = ((ymin + ymax) / 2.0) / h
                    bw = (xmax - xmin) / w
                    bh = (ymax - ymin) / h
                    v_bbox = validate_bbox(cx, cy, bw, bh)
                    if v_bbox:
                        boxes.append((c, *v_bbox))
                        source_stats["datacluster_fire_smoke"][c] += 1

                if boxes:
                    matching_imgs = list(dc_img_dir.rglob(f"{xf.stem}.*"))
                    if matching_imgs and matching_imgs[0].is_file():
                        curated_samples.append({
                            "img_path": matching_imgs[0],
                            "boxes": boxes,
                            "source": "datacluster_fire_smoke",
                            "prefix": "dcfir",
                        })
                        count += 1
            except Exception:
                continue
        print(f"      -> Ingested {count} candidate samples from DataCluster Fire & Smoke")

    # -------------------------------------------------------------------------
    # 8. Hard Negatives (Empty annotations for background suppression)
    # -------------------------------------------------------------------------
    hard_neg_samples = []
    if HARD_NEG_DIR.exists():
        print("[8/8] Ingesting hard-negative background samples...")
        all_hn = [p for p in (list(HARD_NEG_DIR.rglob("*.jpg")) + list(HARD_NEG_DIR.rglob("*.png"))) if p.is_file()]
        random.shuffle(all_hn)
        for img_path in all_hn[:450]:
            hard_neg_samples.append({
                "img_path": img_path,
                "boxes": [],
                "source": "hard_negatives",
                "prefix": "hneg",
            })
        print(f"      -> Selected {len(hard_neg_samples)} hard-negative background images.")

    # -------------------------------------------------------------------------
    # Stratified Selection & Quotas
    # -------------------------------------------------------------------------
    by_source = defaultdict(list)
    for s in curated_samples:
        by_source[s["source"]].append(s)

    quotas = {
        "ppe_safup": 1100,
        "ppec": 1100,
        "safety_ppe_4": 550,
        "d_fire": 800,
        "hf_smruti_ppe_bucket": 1400,
        "ultralytics_construction_ppe": 900,
        "datacluster_fire_smoke": 100,
    }

    selected_samples = []
    for src, items in by_source.items():
        random.shuffle(items)
        limit = quotas.get(src, 800)
        chosen = items[:limit]
        selected_samples.extend(chosen)
        print(f"  Source [{src}]: Selected {len(chosen)} / {len(items)} available")

    # Deduplication stage via SHA-256
    print("\n--- Running SHA-256 Deduplication ---")
    deduped_samples = []
    for s in tqdm(selected_samples, desc="Deduplicating positive samples"):
        h = compute_sha256(s["img_path"])
        if h in seen_hashes:
            duplicates_detected += 1
            continue
        seen_hashes[h] = str(s["img_path"])
        s["sha256"] = h
        deduped_samples.append(s)

    deduped_hn = []
    for s in tqdm(hard_neg_samples, desc="Deduplicating hard negatives"):
        h = compute_sha256(s["img_path"])
        if h in seen_hashes:
            duplicates_detected += 1
            continue
        seen_hashes[h] = str(s["img_path"])
        s["sha256"] = h
        deduped_hn.append(s)

    print(f"Deduplication complete. Removed {duplicates_detected} duplicate images.")
    final_dataset = deduped_samples + deduped_hn
    random.shuffle(final_dataset)
    total_imgs = len(final_dataset)
    print(f"Total Unique Images in SafeSync v4 Dataset: {total_imgs}")

    # -------------------------------------------------------------------------
    # Split Assignment: 70% Train, 20% Val, 10% Test
    # -------------------------------------------------------------------------
    n_train = int(total_imgs * 0.70)
    n_val = int(total_imgs * 0.20)

    train_set = final_dataset[:n_train]
    val_set = final_dataset[n_train:n_train + n_val]
    test_set = final_dataset[n_train + n_val:]

    print(f"Splits: Train={len(train_set)}, Val={len(val_set)}, Test={len(test_set)}")

    # -------------------------------------------------------------------------
    # Write splits, copy images, write labels, collect manifest
    # -------------------------------------------------------------------------
    manifest_rows = []
    overall_class_counts = defaultdict(lambda: Counter())

    def process_and_write_split(samples, split_name):
        cls_counter = Counter()
        written = 0
        for idx, item in enumerate(tqdm(samples, desc=f"Writing {split_name} split")):
            img_src = item["img_path"]
            prefix = item["prefix"]
            dst_name = f"{prefix}_{idx:05d}{img_src.suffix.lower()}"
            dst_img = OUT_DIR / "images" / split_name / dst_name
            dst_lbl = OUT_DIR / "labels" / split_name / f"{prefix}_{idx:05d}.txt"

            try:
                shutil.copy2(img_src, dst_img)
                box_classes = []
                with open(dst_lbl, "w", encoding="utf-8") as f:
                    for box in item["boxes"]:
                        c, cx, cy, w, h = box
                        f.write(f"{c} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
                        cls_counter[c] += 1
                        overall_class_counts[split_name][c] += 1
                        box_classes.append(CANONICAL_CLASSES[c])

                manifest_rows.append({
                    "split": split_name,
                    "filename": dst_name,
                    "original_path": str(img_src),
                    "source": item["source"],
                    "sha256": item.get("sha256", ""),
                    "box_count": len(item["boxes"]),
                    "classes": ";".join(sorted(set(box_classes))),
                })
                written += 1
            except Exception as e:
                print(f"Error copying {img_src}: {e}")
                continue

        print(f"\n=== Split: {split_name.upper()} ({written} images) ===")
        for c in sorted(CANONICAL_CLASSES.keys()):
            print(f"  {c} ({CANONICAL_CLASSES[c]}): {cls_counter[c]} boxes")

    process_and_write_split(train_set, "train")
    process_and_write_split(val_set, "val")
    process_and_write_split(test_set, "test")

    # -------------------------------------------------------------------------
    # Generate data/processed/safesync/dataset.yaml
    # -------------------------------------------------------------------------
    yaml_content = f"""# data/processed/safesync/dataset.yaml — SafeSync Unified v4 Dataset
# BPUT Hackathon 2026 — PS06: AI Safety Gear & Hazard Detection
# 7 Canonical Classes: person, helmet, safety_vest, gloves, safety_footwear, fire, smoke

path: {OUT_DIR.as_posix()}
train: images/train
val: images/val
test: images/test

nc: 7
names:
  0: person
  1: helmet
  2: safety_vest
  3: gloves
  4: safety_footwear
  5: fire
  6: smoke
"""
    with open(OUT_DIR / "dataset.yaml", "w", encoding="utf-8") as f:
        f.write(yaml_content)

    # -------------------------------------------------------------------------
    # Generate manifest.csv
    # -------------------------------------------------------------------------
    manifest_path = OUT_DIR / "manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["split", "filename", "original_path", "source", "sha256", "box_count", "classes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    # -------------------------------------------------------------------------
    # Generate dataset_stats.json
    # -------------------------------------------------------------------------
    stats_data = {
        "dataset_name": "safesync_v4_unified",
        "created_at": "2026-09-29T18:50:00Z",
        "total_images": total_imgs,
        "duplicates_removed": duplicates_detected,
        "splits": {
            "train": {
                "images": len(train_set),
                "boxes": dict(overall_class_counts["train"]),
            },
            "val": {
                "images": len(val_set),
                "boxes": dict(overall_class_counts["val"]),
            },
            "test": {
                "images": len(test_set),
                "boxes": dict(overall_class_counts["test"]),
            },
        },
        "canonical_classes": CANONICAL_CLASSES,
        "sources_included": list(quotas.keys()) + ["hard_negatives"],
    }
    stats_path = OUT_DIR / "dataset_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats_data, f, indent=2)

    # -------------------------------------------------------------------------
    # Visual QA Preview Generation
    # -------------------------------------------------------------------------
    generate_visual_qa_previews()

    print("\n====================================================================")
    print("  SafeSync v4 Unified Dataset Generation COMPLETED!")
    print(f"  Config:   {OUT_DIR / 'dataset.yaml'}")
    print(f"  Manifest: {manifest_path}")
    print(f"  Stats:    {stats_path}")
    print(f"  Previews: {PREVIEW_DIR}")
    print("====================================================================")


def generate_visual_qa_previews():
    """Generates visual previews with drawn bounding boxes for validation."""
    print("\n--- Generating Visual QA Previews ---")
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    val_images = list((OUT_DIR / "images" / "val").glob("*.*"))
    if not val_images:
        return

    # Sample images representing each class
    class_representatives = defaultdict(list)
    for img_path in val_images:
        lbl_path = OUT_DIR / "labels" / "val" / f"{img_path.stem}.txt"
        if not lbl_path.exists():
            continue
        with open(lbl_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    c = int(float(parts[0]))
                    class_representatives[c].append(img_path)

    samples_to_render = set()
    for c in sorted(CANONICAL_CLASSES.keys()):
        imgs = class_representatives[c]
        if imgs:
            for img in random.sample(imgs, min(3, len(imgs))):
                samples_to_render.add(img)

    # Add 2 hard negative samples
    hneg_imgs = [p for p in val_images if p.stem.startswith("hneg")]
    if hneg_imgs:
        for img in random.sample(hneg_imgs, min(2, len(hneg_imgs))):
            samples_to_render.add(img)

    for img_path in samples_to_render:
        try:
            img = Image.open(img_path).convert("RGB")
            draw = ImageDraw.Draw(img)
            w_img, h_img = img.size

            lbl_path = OUT_DIR / "labels" / "val" / f"{img_path.stem}.txt"
            if lbl_path.exists():
                with open(lbl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            c = int(float(parts[0]))
                            cx, cy, w, h = [float(p) for p in parts[1:5]]
                            x1 = (cx - w / 2.0) * w_img
                            y1 = (cy - h / 2.0) * h_img
                            x2 = (cx + w / 2.0) * w_img
                            y2 = (cy + h / 2.0) * h_img
                            cls_name = CANONICAL_CLASSES.get(c, str(c))
                            color = CLASS_COLORS.get(c, "#FFFFFF")

                            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                            # Label banner
                            draw.rectangle([x1, max(0, y1 - 18), x1 + len(cls_name) * 9 + 8, y1], fill=color)
                            draw.text((x1 + 4, max(0, y1 - 16)), cls_name, fill="black")

            dst_preview = PREVIEW_DIR / f"preview_{img_path.name}"
            img.save(dst_preview)
        except Exception as e:
            continue

    print(f"Generated {len(list(PREVIEW_DIR.glob('*.jpg')) + list(PREVIEW_DIR.glob('*.png')))} QA preview images in {PREVIEW_DIR}")


if __name__ == "__main__":
    build_v4_dataset()
