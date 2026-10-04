r"""
scripts/dataset/audit_and_organize_master.py — SafeSync Master Dataset Audit & Organization
========================================================================================
1. Discovers and catalogs all datasets across SafeSync and external sources.
2. Safely populates datasets/organized/{helmet, safety_vest, fire, safety_footwear, gloves, construction_ppe}
   using non-destructive hardlinks (or copies), preserving original raw files intact.
3. Audits all annotations, class mappings, coordinate validity, missing/orphan files, and YAML configs.
4. Performs cross-dataset duplicate detection using file hashes.
5. Emits a comprehensive audit report for the user.
"""

import os
import sys
import json
import time
import shutil
import hashlib
from pathlib import Path
from collections import defaultdict, Counter
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = ROOT / "datasets"
ORGANIZED_DIR = DATASETS_DIR / "organized"
RAW_DIR = DATASETS_DIR / "raw"
ND_DIR = Path("D:/Additional/PROJECT/nd")

SAFESYNC_ONTOLOGY = {
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
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
    except Exception:
        shutil.copy2(src, dst)


def sha256_file(path: Path, max_bytes: int = 1048576) -> str:
    """Computes fast SHA-256 hash (or prefix hash for large files)."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            chunk = f.read(max_bytes)
            h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def audit_raw_datasets():
    print("=" * 80)
    print("STEP 1: DISCOVERING & INVENTORYING ALL DATASETS")
    print("=" * 80)

    dataset_inventory = []

    # 1. Inspect datasets in datasets/raw
    if RAW_DIR.exists():
        for d in sorted(RAW_DIR.iterdir()):
            if d.is_dir():
                yamls = list(d.rglob("*.yaml"))
                img_files = list(d.rglob("*.jpg")) + list(d.rglob("*.png")) + list(d.rglob("*.jpeg"))
                lbl_files = list(d.rglob("*.txt"))

                splits = set()
                for p in img_files:
                    for part in p.parts:
                        if part.lower() in ["train", "val", "test", "valid"]:
                            splits.add(part.lower())

                # Read YAML if present
                classes = {}
                if yamls:
                    try:
                        with open(yamls[0], "r", encoding="utf-8") as yf:
                            ydata = yaml.safe_load(yf) or {}
                            classes = ydata.get("names", {})
                    except Exception:
                        pass

                # Approximate size in MB
                total_bytes = sum(p.stat().st_size for p in img_files[:200])
                avg_img = (total_bytes / len(img_files[:200])) if img_files else 0
                approx_size_mb = (avg_img * len(img_files)) / (1024 * 1024)

                dataset_inventory.append({
                    "name": d.name,
                    "path": str(d),
                    "type": "raw_directory",
                    "images_count": len(img_files),
                    "labels_count": len(lbl_files),
                    "splits": sorted(list(splits)),
                    "yaml_file": str(yamls[0]) if yamls else "None",
                    "classes": classes,
                    "approx_size_mb": round(approx_size_mb, 1),
                })

    # 2. Inspect NDJSON files in D:\Additional\PROJECT\nd
    if ND_DIR.exists():
        for nd in sorted(ND_DIR.glob("*.ndjson")):
            img_count = 0
            splits = set()
            classes = {}
            with open(nd, "r", encoding="utf-8") as f:
                first = f.readline().strip()
                if first:
                    try:
                        meta = json.loads(first)
                        classes = meta.get("class_names", {})
                    except Exception:
                        pass
                for line in f:
                    if line.strip():
                        img_count += 1
                        try:
                            d = json.loads(line)
                            if "split" in d:
                                splits.add(d["split"])
                        except Exception:
                            pass

            dataset_inventory.append({
                "name": nd.stem,
                "path": str(nd),
                "type": "ndjson_export",
                "images_count": img_count,
                "labels_count": img_count,
                "splits": sorted(list(splits)),
                "yaml_file": "Embedded in NDJSON metadata",
                "classes": classes,
                "approx_size_mb": round(nd.stat().st_size / (1024 * 1024), 1),
            })

    # 3. Inspect datasets/images & datasets/labels (Unified 10k dataset)
    if (DATASETS_DIR / "images").exists():
        img_files = list((DATASETS_DIR / "images").rglob("*.*"))
        lbl_files = list((DATASETS_DIR / "labels").rglob("*.txt"))
        yaml_path = DATASETS_DIR / "data.yaml"
        classes = {}
        if yaml_path.exists():
            try:
                with open(yaml_path, "r", encoding="utf-8") as yf:
                    classes = yaml.safe_load(yf).get("names", {})
            except Exception:
                pass

        dataset_inventory.append({
            "name": "SafeSync_Unified_10k",
            "path": str(DATASETS_DIR),
            "type": "yolo_unified",
            "images_count": len(img_files),
            "labels_count": len(lbl_files),
            "splits": ["train", "val", "test"],
            "yaml_file": str(yaml_path),
            "classes": classes,
            "approx_size_mb": round(len(img_files) * 0.12, 1),
        })

    return dataset_inventory


def populate_organized_structure():
    print("\n" + "=" * 80)
    print("STEP 2: POPULATING CENTRAL datasets/organized DIRECTORY")
    print("=" * 80)
    ORGANIZED_DIR.mkdir(parents=True, exist_ok=True)

    src_img_base = DATASETS_DIR / "images"
    src_lbl_base = DATASETS_DIR / "labels"

    # Category definitions to populate under datasets/organized/
    categories = {
        "helmet": {
            "ids": {1},
            "desc": "Safety Helmet / Hard Hat",
            "yaml_names": {1: "helmet"},
        },
        "safety_vest": {
            "ids": {2},
            "desc": "High-Visibility Safety Vest",
            "yaml_names": {2: "safety_vest"},
        },
        "fire": {
            "ids": {5, 6},
            "desc": "Fire & Smoke Combustion Hazards",
            "yaml_names": {5: "fire", 6: "smoke"},
        },
        "safety_footwear": {
            "ids": {4},
            "desc": "Safety Footwear / Boots",
            "yaml_names": {4: "safety_footwear"},
        },
        "gloves": {
            "ids": {3},
            "desc": "Industrial Safety Gloves",
            "yaml_names": {3: "gloves"},
        },
    }

    splits = ["train", "val", "test"]
    organized_counts = defaultdict(lambda: defaultdict(int))

    # 1. Populate category folders from the unified dataset
    for cat_name, cat_info in categories.items():
        cat_dir = ORGANIZED_DIR / cat_name
        target_ids = cat_info["ids"]
        print(f"Organizing [{cat_name}] ...")

        for s in splits:
            lbl_dir = src_lbl_base / s
            img_dir = src_img_base / s
            if not lbl_dir.exists():
                continue

            dst_img_dir = cat_dir / "images" / s
            dst_lbl_dir = cat_dir / "labels" / s
            dst_img_dir.mkdir(parents=True, exist_ok=True)
            dst_lbl_dir.mkdir(parents=True, exist_ok=True)

            for lbl_file in lbl_dir.glob("*.txt"):
                matching_lines = []
                with open(lbl_file, "r", encoding="utf-8") as fp:
                    for line in fp:
                        parts = line.strip().split()
                        if parts and int(parts[0]) in target_ids:
                            matching_lines.append(line)

                if matching_lines:
                    stem = lbl_file.stem
                    img_match = None
                    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
                        cand = img_dir / f"{stem}{ext}"
                        if cand.exists():
                            img_match = cand
                            break

                    if img_match:
                        link_or_copy(img_match, dst_img_dir / img_match.name)
                        dst_lbl = dst_lbl_dir / lbl_file.name
                        if not dst_lbl.exists():
                            with open(dst_lbl, "w", encoding="utf-8") as out_fp:
                                out_fp.writelines(matching_lines)

                        organized_counts[cat_name][s] += 1

        # Write data.yaml for this organized category
        yaml_path = cat_dir / "data.yaml"
        ydata = {
            "path": str(cat_dir.resolve()).replace("\\", "/"),
            "train": "images/train",
            "val": "images/val",
            "test": "images/test",
            "nc": 7,
            "names": SAFESYNC_ONTOLOGY,
        }
        with open(yaml_path, "w", encoding="utf-8") as yf:
            yaml.dump(ydata, yf, sort_keys=False)

    # 2. Populate construction_ppe under datasets/organized/construction_ppe
    print("Organizing [construction_ppe] ...")
    cppe_dir = ORGANIZED_DIR / "construction_ppe"
    cppe_dir.mkdir(parents=True, exist_ok=True)

    src_cppe = DATASETS_DIR / "normalized" / "construction_ppe"
    if src_cppe.exists():
        for s in splits:
            c_img_src = src_cppe / "images" / s
            c_lbl_src = src_cppe / "labels" / s
            c_img_dst = cppe_dir / "images" / s
            c_lbl_dst = cppe_dir / "labels" / s
            c_img_dst.mkdir(parents=True, exist_ok=True)
            c_lbl_dst.mkdir(parents=True, exist_ok=True)

            if c_img_src.exists():
                for im in c_img_src.glob("*.*"):
                    link_or_copy(im, c_img_dst / im.name)
                    organized_counts["construction_ppe"][s] += 1
            if c_lbl_src.exists():
                for lb in c_lbl_src.glob("*.txt"):
                    link_or_copy(lb, c_lbl_dst / lb.name)

        yaml_path = cppe_dir / "data.yaml"
        ydata = {
            "path": str(cppe_dir.resolve()).replace("\\", "/"),
            "train": "images/train",
            "val": "images/val",
            "test": "images/test",
            "nc": 7,
            "names": SAFESYNC_ONTOLOGY,
        }
        with open(yaml_path, "w", encoding="utf-8") as yf:
            yaml.dump(ydata, yf, sort_keys=False)

    return organized_counts


def audit_organized_datasets():
    print("\n" + "=" * 80)
    print("STEP 3: ANNOTATION & INTEGRITY AUDIT")
    print("=" * 80)

    audit_results = {}

    for cat_dir in sorted(ORGANIZED_DIR.iterdir()):
        if not cat_dir.is_dir():
            continue

        cat_name = cat_dir.name
        img_base = cat_dir / "images"
        lbl_base = cat_dir / "labels"

        total_images = 0
        total_labels = 0
        missing_images = 0
        missing_labels = 0
        empty_labels = 0
        corrupt_images = 0
        invalid_boxes = 0
        class_id_distribution = Counter()

        for s in ["train", "val", "test"]:
            s_img = img_base / s
            s_lbl = lbl_base / s

            if not s_img.exists() or not s_lbl.exists():
                continue

            img_stems = {p.stem: p for p in s_img.glob("*.*") if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]}
            lbl_stems = {p.stem: p for p in s_lbl.glob("*.txt")}

            total_images += len(img_stems)
            total_labels += len(lbl_stems)

            # Check missing labels
            for stem in img_stems:
                if stem not in lbl_stems:
                    missing_labels += 1

            # Check missing images & audit label content
            for stem, lbl_path in lbl_stems.items():
                if stem not in img_stems:
                    missing_images += 1

                # Check label file content
                try:
                    with open(lbl_path, "r", encoding="utf-8") as fp:
                        lines = fp.readlines()
                        if not lines:
                            empty_labels += 1
                        for line in lines:
                            parts = line.strip().split()
                            if len(parts) >= 5:
                                cid = int(float(parts[0]))
                                class_id_distribution[cid] += 1
                                x, y, w, h = [float(v) for v in parts[1:5]]
                                if x < 0.0 or x > 1.0 or y < 0.0 or y > 1.0 or w <= 0.0 or w > 1.0 or h <= 0.0 or h > 1.0:
                                    invalid_boxes += 1
                            else:
                                invalid_boxes += 1
                except Exception:
                    invalid_boxes += 1

        yaml_path = cat_dir / "data.yaml"
        yaml_valid = yaml_path.exists()

        audit_results[cat_name] = {
            "total_images": total_images,
            "total_labels": total_labels,
            "missing_labels": missing_labels,
            "missing_images": missing_images,
            "empty_labels": empty_labels,
            "invalid_boxes": invalid_boxes,
            "corrupt_images": corrupt_images,
            "yaml_valid": yaml_valid,
            "class_distribution": dict(class_id_distribution),
        }

    return audit_results


def detect_duplicates():
    print("\n" + "=" * 80)
    print("STEP 4: DUPLICATE DETECTION ACROSS DATASETS")
    print("=" * 80)

    # Check cross-duplicates between organized folders
    hash_to_datasets = defaultdict(list)

    for cat_dir in sorted(ORGANIZED_DIR.iterdir()):
        if not cat_dir.is_dir():
            continue
        cat_name = cat_dir.name
        img_files = list(cat_dir.rglob("*.jpg")) + list(cat_dir.rglob("*.png"))
        # Sample or check all
        for im in img_files:
            h = sha256_file(im, max_bytes=65536)
            if h:
                hash_to_datasets[h].append((cat_name, im.name))

    # Cross-dataset duplicates count
    cross_dups = Counter()
    for h, occurrences in hash_to_datasets.items():
        datasets_involved = sorted(list(set(d for d, fname in occurrences)))
        if len(datasets_involved) > 1:
            pair = f"{datasets_involved[0]} <-> {datasets_involved[1]}"
            cross_dups[pair] += 1

    return dict(cross_dups)


def main():
    inventory = audit_raw_datasets()
    organized_counts = populate_organized_structure()
    audit_results = audit_organized_datasets()
    cross_dups = detect_duplicates()

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "raw_inventory": inventory,
        "organized_counts": organized_counts,
        "audit_results": audit_results,
        "cross_duplicates": cross_dups,
    }

    report_path = DATASETS_DIR / "MASTER_DATASET_AUDIT_REPORT.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 80)
    print(f"MASTER AUDIT COMPLETE! Full JSON report: {report_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
