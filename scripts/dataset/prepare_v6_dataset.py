r"""
scripts/dataset/prepare_v6_dataset.py — SafeSync V6 Curated Dataset Preparation Engine
======================================================================================
Prepares a balanced, leakage-free dataset for candidate V6 training:
1. Filters out ~3,500 unannotated empty background images caused by no_helmet drops.
2. Injects the verified 300 curated hard-negative images (hneg_) from datasets/processed_v3/
   (steam pipes, sunlight glare, yellow excavators, dust clouds, machinery).
3. Achieves an optimal background image ratio of approximately 3–5%.
4. Uses SHA-256 deduplication to guarantee zero data leakage between Train, Val, and Test splits.
5. Preserves all legitimate positive PPE and fire/smoke annotations without alteration.
6. Generates datasets/v6_candidate/data_v6.yaml and a pre-training audit checkpoint report.
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path
from collections import Counter, defaultdict
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
SRC_UNIFIED = ROOT / "datasets"
SRC_PROCESSED_V3 = ROOT / "datasets" / "processed_v3"
DEST_DIR = ROOT / "datasets" / "v6_candidate"

CLASS_NAMES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}


def sha256_file(filepath: Path) -> str:
    """Computes SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def link_or_copy(src: Path, dst: Path):
    """Creates a hardlink to avoid duplicating disk space; falls back to copy."""
    if dst.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
    except Exception:
        shutil.copy2(src, dst)


def build_v6_dataset():
    print("=" * 80)
    print("SAFESYNC: PREPARING V6 BALANCED & CURATED DATASET (PHASE 1)")
    print("=" * 80)

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    dest_images = DEST_DIR / "images"
    dest_labels = DEST_DIR / "labels"

    # Step 1: Collect Test & Val hashes first to prevent any leakage into Train
    val_hashes = {}
    test_hashes = {}
    train_hashes = {}

    splits_data = {
        "train": {"images": [], "labels": []},
        "val": {"images": [], "labels": []},
        "test": {"images": [], "labels": []},
    }

    # Track statistics
    class_box_counts = defaultdict(lambda: Counter())
    class_image_counts = defaultdict(lambda: Counter())
    empty_label_counts = Counter()
    hneg_counts = Counter()

    # 1. Process Val Split first
    print("\n[1/3] Curating Validation Split ...")
    val_img_src = SRC_UNIFIED / "images" / "val"
    val_lbl_src = SRC_UNIFIED / "labels" / "val"
    val_hneg_img_src = SRC_PROCESSED_V3 / "images" / "val"

    # A. Annotated positive val images
    for lbl_p in val_lbl_src.glob("*.txt"):
        content = lbl_p.read_text(encoding="utf-8").strip()
        if content:
            img_p = val_img_src / f"{lbl_p.stem}.jpg"
            if not img_p.exists():
                for ext in [".png", ".jpeg", ".webp"]:
                    c = val_img_src / f"{lbl_p.stem}{ext}"
                    if c.exists():
                        img_p = c
                        break
            if img_p.exists():
                h = sha256_file(img_p)
                val_hashes[h] = img_p.name
                splits_data["val"]["images"].append((img_p, content, False))

    # B. Curated val hneg_ images
    for hneg_p in val_hneg_img_src.glob("*hneg*"):
        h = sha256_file(hneg_p)
        if h not in val_hashes:
            val_hashes[h] = hneg_p.name
            splits_data["val"]["images"].append((hneg_p, "", True))

    # 2. Process Test Split
    print("[2/3] Curating Test Split ...")
    test_img_src = SRC_UNIFIED / "images" / "test"
    test_lbl_src = SRC_UNIFIED / "labels" / "test"
    test_hneg_img_src = SRC_PROCESSED_V3 / "images" / "test"

    for lbl_p in test_lbl_src.glob("*.txt"):
        content = lbl_p.read_text(encoding="utf-8").strip()
        if content:
            img_p = test_img_src / f"{lbl_p.stem}.jpg"
            if not img_p.exists():
                for ext in [".png", ".jpeg", ".webp"]:
                    c = test_img_src / f"{lbl_p.stem}{ext}"
                    if c.exists():
                        img_p = c
                        break
            if img_p.exists():
                h = sha256_file(img_p)
                if h not in val_hashes:
                    test_hashes[h] = img_p.name
                    splits_data["test"]["images"].append((img_p, content, False))

    for hneg_p in test_hneg_img_src.glob("*hneg*"):
        h = sha256_file(hneg_p)
        if h not in val_hashes and h not in test_hashes:
            test_hashes[h] = hneg_p.name
            splits_data["test"]["images"].append((hneg_p, "", True))

    # 3. Process Train Split (Strictly excluding Val and Test hashes)
    print("[3/3] Curating Training Split (with Leakage Filtering) ...")
    train_img_src = SRC_UNIFIED / "images" / "train"
    train_lbl_src = SRC_UNIFIED / "labels" / "train"
    train_hneg_img_src = SRC_PROCESSED_V3 / "images" / "train"

    leakages_prevented = 0
    internal_duplicates_prevented = 0

    for lbl_p in train_lbl_src.glob("*.txt"):
        content = lbl_p.read_text(encoding="utf-8").strip()
        # Keep only annotated images (excludes ~3,500 unannotated empty background frames)
        if content:
            img_p = train_img_src / f"{lbl_p.stem}.jpg"
            if not img_p.exists():
                for ext in [".png", ".jpeg", ".webp"]:
                    c = train_img_src / f"{lbl_p.stem}{ext}"
                    if c.exists():
                        img_p = c
                        break
            if img_p.exists():
                h = sha256_file(img_p)
                # Leakage protection check
                if h in val_hashes or h in test_hashes:
                    leakages_prevented += 1
                    continue
                if h in train_hashes:
                    internal_duplicates_prevented += 1
                    continue

                train_hashes[h] = img_p.name
                splits_data["train"]["images"].append((img_p, content, False))

    # Inject verified train hneg_ images
    hneg_injected_train = 0
    for hneg_p in train_hneg_img_src.glob("*hneg*"):
        h = sha256_file(hneg_p)
        if h in val_hashes or h in test_hashes:
            leakages_prevented += 1
            continue
        if h in train_hashes:
            internal_duplicates_prevented += 1
            continue

        train_hashes[h] = hneg_p.name
        splits_data["train"]["images"].append((hneg_p, "", True))
        hneg_injected_train += 1

    # 4. Materialize destination files using non-destructive hardlinks
    print("\nMaterializing files into datasets/v6_candidate ...")
    for split_name in ["train", "val", "test"]:
        dst_img_dir = dest_images / split_name
        dst_lbl_dir = dest_labels / split_name
        dst_img_dir.mkdir(parents=True, exist_ok=True)
        dst_lbl_dir.mkdir(parents=True, exist_ok=True)

        for src_img_path, lbl_content, is_hneg in splits_data[split_name]["images"]:
            dst_img = dst_img_dir / src_img_path.name
            dst_lbl = dst_lbl_dir / f"{src_img_path.stem}.txt"

            link_or_copy(src_img_path, dst_img)

            # Write label
            with open(dst_lbl, "w", encoding="utf-8") as fp:
                fp.write(lbl_content + ("\n" if lbl_content and not lbl_content.endswith("\n") else ""))

            # Compute stats
            if is_hneg:
                hneg_counts[split_name] += 1
                empty_label_counts[split_name] += 1
            elif not lbl_content:
                empty_label_counts[split_name] += 1
            else:
                classes_in_frame = set()
                for line in lbl_content.splitlines():
                    parts = line.strip().split()
                    if parts:
                        cid = int(parts[0])
                        cname = CLASS_NAMES.get(cid, str(cid))
                        class_box_counts[split_name][cname] += 1
                        classes_in_frame.add(cname)
                for cname in classes_in_frame:
                    class_image_counts[split_name][cname] += 1

    # 5. Generate data_v6.yaml
    yaml_dict = {
        "path": str(DEST_DIR.resolve()).replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": 7,
        "names": CLASS_NAMES,
    }
    yaml_path = DEST_DIR / "data_v6.yaml"
    with open(yaml_path, "w", encoding="utf-8") as yf:
        yaml.dump(yaml_dict, yf, sort_keys=False)

    # 6. Verify zero leakage post-creation
    final_train_hashes = {sha256_file(p) for p in (dest_images / "train").glob("*.*")}
    final_val_hashes = {sha256_file(p) for p in (dest_images / "val").glob("*.*")}
    final_test_hashes = {sha256_file(p) for p in (dest_images / "test").glob("*.*")}

    actual_leakage_tv = len(final_train_hashes & final_val_hashes)
    actual_leakage_tt = len(final_train_hashes & final_test_hashes)
    actual_leakage_vt = len(final_val_hashes & final_test_hashes)

    train_total = len(final_train_hashes)
    val_total = len(final_val_hashes)
    test_total = len(final_test_hashes)
    grand_total = train_total + val_total + test_total

    empty_train_pct = round((empty_label_counts["train"] / train_total) * 100.0, 2)
    empty_overall_pct = round((sum(empty_label_counts.values()) / grand_total) * 100.0, 2)

    # Sum class counts
    total_class_images = Counter()
    total_class_boxes = Counter()
    for s in ["train", "val", "test"]:
        total_class_images.update(class_image_counts[s])
        total_class_boxes.update(class_box_counts[s])

    report = {
        "dataset_name": "safesync_v6_candidate",
        "dataset_path": str(DEST_DIR),
        "data_yaml": str(yaml_path),
        "total_images": grand_total,
        "train_count": train_total,
        "val_count": val_total,
        "test_count": test_total,
        "hard_negatives": {
            "train": hneg_counts["train"],
            "val": hneg_counts["val"],
            "test": hneg_counts["test"],
            "total": sum(hneg_counts.values()),
        },
        "empty_labels": {
            "train_count": empty_label_counts["train"],
            "train_percentage": empty_train_pct,
            "overall_count": sum(empty_label_counts.values()),
            "overall_percentage": empty_overall_pct,
        },
        "leakage_audit": {
            "train_vs_val_leakage": actual_leakage_tv,
            "train_vs_test_leakage": actual_leakage_tt,
            "val_vs_test_leakage": actual_leakage_vt,
            "leakages_prevented_at_source": leakages_prevented,
            "internal_duplicates_prevented": internal_duplicates_prevented,
        },
        "class_image_counts": dict(total_class_images),
        "class_box_counts": dict(total_class_boxes),
        "per_split_image_counts": {s: dict(class_image_counts[s]) for s in ["train", "val", "test"]},
    }

    report_path = DEST_DIR / "v6_pretraining_checkpoint_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 80)
    print("V6 CURATED DATASET PREPARATION COMPLETE!")
    print(f"Report written to: {report_path}")
    print(f"Data YAML:         {yaml_path}")
    print("=" * 80)

    return report


if __name__ == "__main__":
    build_v6_dataset()
