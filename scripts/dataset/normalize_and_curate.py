"""
normalize_and_curate.py — SafeSync Normalization & Hard-Negative Curator
Normalizes raw datasets into canonical YOLO representations and curates dedicated hard negatives:
- Target PPE: 0: person, 1: helmet, 2: safety_vest, 3: gloves, 4: safety_footwear
- Target Hazard: 0: fire, 1: smoke
- Dedicated Hard Negatives: unhelmeted heads (Hair != Helmet) and unvested torsos (Shirt != Vest).
"""

import os
import shutil
import yaml
from collections import defaultdict
from typing import Dict, Any, List

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_PATH = os.path.join(ROOT, "configs", "dataset", "class_mapping.yaml")
RAW_DIR = os.path.join(ROOT, "datasets", "raw")
NORM_DIR = os.path.join(ROOT, "datasets", "normalized")
NORM_PPE = os.path.join(NORM_DIR, "ppe")
NORM_HAZARD = os.path.join(NORM_DIR, "fire_smoke")
HARD_NEG_DIR = os.path.join(NORM_DIR, "hard_negatives")


def load_mapping_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_all_datasets():
    cfg = load_mapping_config()
    os.makedirs(os.path.join(NORM_PPE, "images", "train"), exist_ok=True)
    os.makedirs(os.path.join(NORM_PPE, "images", "val"), exist_ok=True)
    os.makedirs(os.path.join(NORM_PPE, "images", "test"), exist_ok=True)
    os.makedirs(os.path.join(NORM_PPE, "labels", "train"), exist_ok=True)
    os.makedirs(os.path.join(NORM_PPE, "labels", "val"), exist_ok=True)
    os.makedirs(os.path.join(NORM_PPE, "labels", "test"), exist_ok=True)

    os.makedirs(os.path.join(NORM_HAZARD, "images", "train"), exist_ok=True)
    os.makedirs(os.path.join(NORM_HAZARD, "images", "val"), exist_ok=True)
    os.makedirs(os.path.join(NORM_HAZARD, "images", "test"), exist_ok=True)
    os.makedirs(os.path.join(NORM_HAZARD, "labels", "train"), exist_ok=True)
    os.makedirs(os.path.join(NORM_HAZARD, "labels", "val"), exist_ok=True)
    os.makedirs(os.path.join(NORM_HAZARD, "labels", "test"), exist_ok=True)

    os.makedirs(os.path.join(HARD_NEG_DIR, "hair_vs_helmet"), exist_ok=True)
    os.makedirs(os.path.join(HARD_NEG_DIR, "shirt_vs_vest"), exist_ok=True)

    dataset_configs = cfg.get("datasets", {})
    subdirs = [d for d in os.listdir(RAW_DIR) if os.path.isdir(os.path.join(RAW_DIR, d))]

    stats = {
        "ppe": {"train": 0, "val": 0, "test": 0, "boxes": defaultdict(int)},
        "hazard": {"train": 0, "val": 0, "test": 0, "boxes": defaultdict(int)},
        "hard_negatives": {"unhelmeted_head": 0, "unvested_torso": 0, "unbooted_foot": 0, "ungloved_hand": 0},
    }

    for d_name in subdirs:
        d_path = os.path.join(RAW_DIR, d_name)
        # Skip incomplete downloads
        if not os.path.isfile(os.path.join(d_path, "data.yaml")):
            has_imgs = any(f.lower().endswith((".jpg", ".png", ".jpeg")) for _, _, files in os.walk(d_path) for f in files)
            if not has_imgs:
                print(f"Skipping {d_name}: download in progress or no images found.")
                continue

        d_cfg = dataset_configs.get(d_name, {}).get("raw_classes", {})
        data_yaml = os.path.join(d_path, "data.yaml")
        raw_names = []
        if os.path.isfile(data_yaml):
            try:
                with open(data_yaml, "r", encoding="utf-8") as f:
                    ydata = yaml.safe_load(f) or {}
                    raw_names = ydata.get("names", [])
                    if isinstance(raw_names, dict):
                        raw_names = [raw_names[k] for k in sorted(raw_names.keys())]
            except Exception:
                pass

        print(f"Normalizing dataset: {d_name} (found {len(raw_names)} raw classes)...")

        # Process each image and label
        for root, _, files in os.walk(d_path):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
                    continue

                img_path = os.path.join(root, f)
                rel = os.path.relpath(img_path, d_path).replace("\\", "/")
                split = "train" if "train" in rel.lower() else ("val" if any(x in rel.lower() for x in ["val", "valid"]) else ("test" if "test" in rel.lower() else "train"))

                # Locate label
                base_name = os.path.splitext(f)[0]
                cand_lbl = img_path.replace("/images/", "/labels/").replace("\\images\\", "\\labels\\")
                cand_lbl = os.path.splitext(cand_lbl)[0] + ".txt"
                if not os.path.isfile(cand_lbl):
                    alt = os.path.join(root, base_name + ".txt")
                    if os.path.isfile(alt):
                        cand_lbl = alt
                    else:
                        continue

                # Read annotations
                try:
                    with open(cand_lbl, "r", encoding="utf-8") as lf:
                        lines = [l.strip() for l in lf if l.strip()]
                except Exception:
                    continue

                is_hazard = (d_name == "d_fire")
                norm_lines = []
                has_hard_neg = False
                has_hair_neg = False
                has_shirt_neg = False

                for line in lines:
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    try:
                        cls_idx = int(parts[0])
                        cx, cy, w, h = parts[1], parts[2], parts[3], parts[4]
                    except ValueError:
                        continue

                    if cls_idx >= len(raw_names):
                        continue
                    cls_name = raw_names[cls_idx]
                    mapping = d_cfg.get(cls_name)
                    if not mapping:
                        # Auto-matching heuristics
                        low = cls_name.lower().replace("-", " ").replace("_", " ")
                        if "helmet" in low and "no" not in low:
                            mapping = {"action": "REMAP", "target": "helmet", "target_id": 1}
                        elif "vest" in low and "no" not in low:
                            mapping = {"action": "REMAP", "target": "safety_vest", "target_id": 2}
                        elif "person" in low or "worker" in low:
                            mapping = {"action": "REMAP", "target": "person", "target_id": 0}
                        elif "glove" in low and "no" not in low:
                            mapping = {"action": "REMAP", "target": "gloves", "target_id": 3}
                        elif ("boot" in low or "shoe" in low or "foot" in low) and "no" not in low:
                            mapping = {"action": "REMAP", "target": "safety_footwear", "target_id": 4}
                        elif "no helmet" in low or "no hat" in low or "head" == low:
                            mapping = {"action": "HARD_NEGATIVE", "target": "unhelmeted_head"}
                        elif "no vest" in low:
                            mapping = {"action": "HARD_NEGATIVE", "target": "unvested_torso"}
                        else:
                            mapping = {"action": "IGNORE"}

                    action = mapping.get("action")
                    if action == "REMAP":
                        tid = mapping.get("target_id")
                        tname = mapping.get("target")
                        norm_lines.append(f"{tid} {cx} {cy} {w} {h}")
                        if is_hazard:
                            stats["hazard"]["boxes"][tname] += 1
                        else:
                            stats["ppe"]["boxes"][tname] += 1
                    elif action == "HARD_NEGATIVE":
                        tneg = mapping.get("target", "unhelmeted_head")
                        stats["hard_negatives"][tneg] += 1
                        has_hard_neg = True
                        if tneg == "unhelmeted_head":
                            has_hair_neg = True
                        elif tneg == "unvested_torso":
                            has_shirt_neg = True

                # Write out normalized files if there are valid detections
                if norm_lines:
                    prefix = f"{d_name}_"
                    out_img_name = prefix + f
                    out_lbl_name = prefix + base_name + ".txt"

                    target_dir = NORM_HAZARD if is_hazard else NORM_PPE
                    dest_img = os.path.join(target_dir, "images", split, out_img_name)
                    dest_lbl = os.path.join(target_dir, "labels", split, out_lbl_name)

                    os.makedirs(os.path.dirname(dest_img), exist_ok=True)
                    os.makedirs(os.path.dirname(dest_lbl), exist_ok=True)

                    if not os.path.exists(dest_img):
                        try:
                            shutil.copy2(img_path, dest_img)
                        except Exception:
                            shutil.copy2("\\\\?\\" + os.path.abspath(img_path), "\\\\?\\" + os.path.abspath(dest_img))
                    with open(dest_lbl, "w", encoding="utf-8") as out_f:
                        out_f.write("\n".join(norm_lines) + "\n")

                    if is_hazard:
                        stats["hazard"][split] += 1
                    else:
                        stats["ppe"][split] += 1

                # If contains verified hard negative (e.g. unhelmeted head or unvested torso)
                if has_hair_neg:
                    dest_neg = os.path.join(HARD_NEG_DIR, "hair_vs_helmet", f"{d_name}_{f}")
                    os.makedirs(os.path.dirname(dest_neg), exist_ok=True)
                    if not os.path.exists(dest_neg):
                        try:
                            shutil.copy2(img_path, dest_neg)
                        except Exception:
                            shutil.copy2("\\\\?\\" + os.path.abspath(img_path), "\\\\?\\" + os.path.abspath(dest_neg))
                if has_shirt_neg:
                    dest_neg = os.path.join(HARD_NEG_DIR, "shirt_vs_vest", f"{d_name}_{f}")
                    os.makedirs(os.path.dirname(dest_neg), exist_ok=True)
                    if not os.path.exists(dest_neg):
                        try:
                            shutil.copy2(img_path, dest_neg)
                        except Exception:
                            shutil.copy2("\\\\?\\" + os.path.abspath(img_path), "\\\\?\\" + os.path.abspath(dest_neg))

    # Write normalized yaml configs
    ppe_yaml = {
        "path": NORM_PPE.replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {
            0: "person",
            1: "helmet",
            2: "safety_vest",
            3: "gloves",
            4: "safety_footwear",
        },
    }
    with open(os.path.join(NORM_PPE, "data.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(ppe_yaml, f, sort_keys=False)

    hazard_yaml = {
        "path": NORM_HAZARD.replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {
            0: "fire",
            1: "smoke",
        },
    }
    with open(os.path.join(NORM_HAZARD, "data.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(hazard_yaml, f, sort_keys=False)

    print("\n" + "="*50)
    print("NORMALIZATION COMPLETE!")
    print("PPE Dataset Splits:", {k: stats["ppe"][k] for k in ["train", "val", "test"]})
    print("PPE Class Distribution:", dict(stats["ppe"]["boxes"]))
    print("Hazard Dataset Splits:", {k: stats["hazard"][k] for k in ["train", "val", "test"]})
    print("Hazard Class Distribution:", dict(stats["hazard"]["boxes"]))
    print("Hard Negatives Tracked:", stats["hard_negatives"])
    return stats


if __name__ == "__main__":
    normalize_all_datasets()
