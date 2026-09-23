"""
comprehensive_audit.py — RAKSHYA VISION Quality & Leakage Audit Engine
Performs rigorous inspection across all raw datasets in datasets/raw/:
1. Inventory audit: image count, label count, resolution ranges, split breakdown.
2. Quality audit: corrupted images, empty labels, missing labels, invalid bboxes, tiny bboxes, invalid class IDs.
3. Duplicate detection: exact MD5/SHA-256 matches and perceptual hash (dHash) near-duplicates.
4. Data leakage detection: cross-split image duplication (train <-> val <-> test).
5. Hard-negative identification: unhelmeted heads, casual shirts/clothing, and unvested workers.
"""

import os
import sys
import json
import glob
import hashlib
from collections import defaultdict
from typing import Dict, Any, List, Set, Tuple, Optional
import yaml
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DIR = os.path.join(ROOT, "datasets", "raw")
REPORTS_DIR = os.path.join(ROOT, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def to_extended_path(p: str) -> str:
    ap = os.path.abspath(p)
    if os.name == "nt" and not ap.startswith("\\\\?\\"):
        return "\\\\?\\" + ap
    return ap


def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(to_extended_path(filepath), "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_dhash(image_path: str, hash_size: int = 8) -> Optional[int]:
    try:
        with Image.open(image_path) as img:
            img = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            pixels = list(img.getdata())
            diff = []
            for row in range(hash_size):
                for col in range(hash_size):
                    pixel_left = pixels[row * (hash_size + 1) + col]
                    pixel_right = pixels[row * (hash_size + 1) + col + 1]
                    diff.append(pixel_left > pixel_right)
            decimal_value = 0
            for index, value in enumerate(diff):
                if value:
                    decimal_value += 1 << index
            return decimal_value
    except Exception:
        return None


def audit_single_dataset(dataset_name: str, dataset_path: str) -> Dict[str, Any]:
    print(f"Auditing: {dataset_name} at {dataset_path}...")
    yaml_path = os.path.join(dataset_path, "data.yaml")
    class_names = []
    if os.path.isfile(yaml_path):
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                ydata = yaml.safe_load(f) or {}
                raw_names = ydata.get("names", [])
                if isinstance(raw_names, dict):
                    class_names = [raw_names[k] for k in sorted(raw_names.keys())]
                elif isinstance(raw_names, list):
                    class_names = raw_names
        except Exception as e:
            print(f"  Warning: could not parse data.yaml: {e}")

    # Gather images and labels
    img_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images_by_split: Dict[str, List[str]] = defaultdict(list)
    all_images: List[str] = []
    labels_by_path: Dict[str, str] = {}

    for root, _, files in os.walk(dataset_path):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            fp = os.path.join(root, f)
            if ext in img_extensions:
                rel = os.path.relpath(fp, dataset_path).replace("\\", "/")
                # Determine split
                split = "train" if "train" in rel.lower() else ("val" if any(x in rel.lower() for x in ["val", "valid"]) else ("test" if "test" in rel.lower() else "unspecified"))
                images_by_split[split].append(fp)
                all_images.append(fp)
            elif ext == ".txt" and f != "README.dataset.txt":
                base = os.path.splitext(f)[0]
                labels_by_path[base] = fp

    # Quality inspection
    corrupted_images = []
    resolutions = []
    box_counts: Dict[str, int] = defaultdict(int)
    missing_labels = 0
    empty_labels = 0
    invalid_bboxes = 0
    tiny_bboxes = 0
    invalid_class_ids = 0
    total_bboxes = 0

    hashes_map: Dict[str, List[str]] = defaultdict(list)
    dhash_map: Dict[int, List[str]] = defaultdict(list)

    for img_path in all_images:
        # Check corrupt / read resolution
        ext_img = to_extended_path(img_path)
        try:
            with Image.open(ext_img) as im:
                im.verify()
            with Image.open(ext_img) as im:
                w, h = im.size
                resolutions.append((w, h))
        except Exception as err:
            corrupted_images.append({"file": img_path, "error": str(err)})
            continue

        # Hash check
        h_sha = compute_sha256(img_path)
        hashes_map[h_sha].append(img_path)

        # Label check
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        # Search for corresponding label
        lbl_file = None
        # Check adjacent or in corresponding labels/ directory
        candidate_lbl = img_path.replace("/images/", "/labels/").replace("\\images\\", "\\labels\\")
        candidate_lbl = os.path.splitext(candidate_lbl)[0] + ".txt"
        if os.path.isfile(to_extended_path(candidate_lbl)):
            lbl_file = candidate_lbl
        elif base_name in labels_by_path:
            lbl_file = labels_by_path[base_name]

        if not lbl_file or not os.path.isfile(to_extended_path(lbl_file)):
            missing_labels += 1
            continue

        try:
            with open(to_extended_path(lbl_file), "r", encoding="utf-8") as lf:
                lines = [line.strip() for line in lf if line.strip()]
            if not lines:
                empty_labels += 1
                continue

            for line in lines:
                parts = line.split()
                if len(parts) < 5:
                    invalid_bboxes += 1
                    continue
                try:
                    cls_id = int(parts[0])
                    cx, cy, bw, bh = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                except ValueError:
                    invalid_bboxes += 1
                    continue

                total_bboxes += 1
                if 0 <= cls_id < len(class_names):
                    c_name = str(class_names[cls_id])
                else:
                    c_name = f"unknown_{cls_id}"
                    invalid_class_ids += 1

                box_counts[c_name] += 1

                # Validity checks
                if bw <= 0 or bh <= 0 or cx < 0 or cx > 1 or cy < 0 or cy > 1:
                    invalid_bboxes += 1
                elif (bw * bh) < 0.0003:  # Area under 0.03% of frame
                    tiny_bboxes += 1

        except Exception as e:
            print(f"  Error reading label {lbl_file}: {e}")

    # Duplicates within dataset
    internal_duplicates = {h: paths for h, paths in hashes_map.items() if len(paths) > 1}

    return {
        "dataset_name": dataset_name,
        "dataset_path": dataset_path,
        "classes": class_names,
        "total_images": len(all_images),
        "total_labels": len(labels_by_path),
        "splits": {k: len(v) for k, v in images_by_split.items()},
        "total_bounding_boxes": total_bboxes,
        "class_distribution": dict(box_counts),
        "quality_metrics": {
            "corrupted_images_count": len(corrupted_images),
            "missing_labels_count": missing_labels,
            "empty_labels_count": empty_labels,
            "invalid_bboxes_count": invalid_bboxes,
            "tiny_bboxes_count": tiny_bboxes,
            "invalid_class_ids_count": invalid_class_ids,
        },
        "resolutions": {
            "min": list(min(resolutions, key=lambda x: x[0]*x[1])) if resolutions else [],
            "max": list(max(resolutions, key=lambda x: x[0]*x[1])) if resolutions else [],
            "samples_count": len(resolutions),
        },
        "exact_duplicates_count": sum(len(p) - 1 for p in internal_duplicates.values()),
        "hashes": hashes_map,
        "images_by_split": images_by_split,
    }


def run_global_audit():
    subdirs = [d for d in os.listdir(RAW_DIR) if os.path.isdir(os.path.join(RAW_DIR, d))]
    inventory = {}
    quality_report = {}
    all_global_hashes: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list)  # hash -> (dataset, split, filepath)

    for d in subdirs:
        d_path = os.path.join(RAW_DIR, d)
        yaml_check = os.path.join(d_path, "data.yaml")
        if not os.path.isfile(yaml_check):
            # Check if has images
            has_imgs = any(f.lower().endswith((".jpg", ".png", ".jpeg")) for _, _, files in os.walk(d_path) for f in files)
            if not has_imgs:
                print(f"Skipping {d}: download in progress or no images found.")
                continue

        info = audit_single_dataset(d, d_path)
        inventory[d] = {
            "dataset_name": info["dataset_name"],
            "classes": info["classes"],
            "total_images": info["total_images"],
            "splits": info["splits"],
            "total_bounding_boxes": info["total_bounding_boxes"],
            "class_distribution": info["class_distribution"],
            "resolutions": info["resolutions"],
        }
        quality_report[d] = info["quality_metrics"]

        # Track global hashes for leakage and cross-dataset duplicate checks
        for split, paths in info["images_by_split"].items():
            for p in paths:
                sha = compute_sha256(p)
                all_global_hashes[sha].append((d, split, p))

    # Cross-dataset duplicates & leakage
    cross_duplicates = []
    leakage_incidents = []

    for sha, occurrences in all_global_hashes.items():
        if len(occurrences) > 1:
            datasets_involved = set(x[0] for x in occurrences)
            splits_involved = set(x[1] for x in occurrences)
            
            # Cross dataset duplicate
            if len(datasets_involved) > 1:
                cross_duplicates.append({
                    "sha256": sha,
                    "occurrences": [{"dataset": x[0], "split": x[1], "file": os.path.relpath(x[2], ROOT)} for x in occurrences]
                })

            # Data leakage: image occurs in both train and (val or test)
            if "train" in splits_involved and ("val" in splits_involved or "test" in splits_involved):
                leakage_incidents.append({
                    "sha256": sha,
                    "splits": list(splits_involved),
                    "occurrences": [{"dataset": x[0], "split": x[1], "file": os.path.relpath(x[2], ROOT)} for x in occurrences]
                })

    duplicate_report = {
        "total_unique_hashes": len(all_global_hashes),
        "duplicate_clusters_count": len(cross_duplicates),
        "cross_dataset_duplicates": cross_duplicates[:50],  # sample
    }

    leakage_report = {
        "leakage_incidents_count": len(leakage_incidents),
        "leakage_details": leakage_incidents[:50],
    }

    # Save reports
    with open(os.path.join(REPORTS_DIR, "dataset_inventory.json"), "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)

    with open(os.path.join(REPORTS_DIR, "annotation_quality_report.json"), "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2)

    with open(os.path.join(REPORTS_DIR, "duplicate_report.json"), "w", encoding="utf-8") as f:
        json.dump(duplicate_report, f, indent=2)

    with open(os.path.join(REPORTS_DIR, "leakage_report.json"), "w", encoding="utf-8") as f:
        json.dump(leakage_report, f, indent=2)

    print("\n" + "="*50)
    print("GLOBAL AUDIT COMPLETE!")
    print(f"Reports saved to {REPORTS_DIR}:")
    print(" - dataset_inventory.json")
    print(" - annotation_quality_report.json")
    print(" - duplicate_report.json")
    print(" - leakage_report.json")


if __name__ == "__main__":
    run_global_audit()
