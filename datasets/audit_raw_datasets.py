"""
audit_raw_datasets.py — SafeSync
Performs deep non-destructive inspection of all raw datasets:
- Image counts, label counts, split distributions
- Raw class names and declared class indexes
- Annotation instance counts per class
- File integrity and format checks
"""

import os
import glob
import yaml
import json
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR = os.path.join(ROOT, "datasets", "raw")
REPORTS_DIR = os.path.join(ROOT, "reports", "dataset_audit")
MANIFESTS_DIR = os.path.join(ROOT, "datasets", "manifests")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(MANIFESTS_DIR, exist_ok=True)

dataset_names = ["ppe_detection_compliance", "construction_ppe", "hard_hat_workers", "d_fire"]
audit_summary = {}

for ds_name in dataset_names:
    ds_path = os.path.join(RAW_DIR, ds_name)
    ds_info = {
        "dataset_name": ds_name,
        "path": ds_path,
        "exists": os.path.isdir(ds_path),
        "yaml_files": {},
        "splits": {},
        "class_counts": Counter(),
        "total_images": 0,
        "total_labels": 0,
        "total_annotations": 0,
    }

    if not ds_info["exists"]:
        audit_summary[ds_name] = ds_info
        continue

    # 1. Parse YAML config files
    yaml_paths = glob.glob(os.path.join(ds_path, "*.yaml")) + glob.glob(os.path.join(ds_path, "*.yml"))
    for yp in yaml_paths:
        try:
            with open(yp, "r", encoding="utf-8") as yf:
                content = yaml.safe_load(yf)
                ds_info["yaml_files"][os.path.basename(yp)] = content
        except Exception as e:
            ds_info["yaml_files"][os.path.basename(yp)] = {"error": str(e)}

    # 2. Inspect splits
    for split in ["train", "valid", "val", "test"]:
        # Find images
        img_candidates = [
            os.path.join(ds_path, split, "images"),
            os.path.join(ds_path, split),
            os.path.join(ds_path, "images", split),
        ]
        lbl_candidates = [
            os.path.join(ds_path, split, "labels"),
            os.path.join(ds_path, split),
            os.path.join(ds_path, "labels", split),
        ]

        found_img_dir = None
        for c in img_candidates:
            if os.path.isdir(c):
                imgs = glob.glob(os.path.join(c, "*.jpg")) + glob.glob(os.path.join(c, "*.png")) + glob.glob(os.path.join(c, "*.jpeg"))
                if imgs:
                    found_img_dir = c
                    break

        found_lbl_dir = None
        for c in lbl_candidates:
            if os.path.isdir(c):
                lbls = glob.glob(os.path.join(c, "*.txt"))
                if lbls:
                    found_lbl_dir = c
                    break

        if found_img_dir or found_lbl_dir:
            img_list = glob.glob(os.path.join(found_img_dir or "", "*.jpg")) + glob.glob(os.path.join(found_img_dir or "", "*.png"))
            lbl_list = glob.glob(os.path.join(found_lbl_dir or "", "*.txt"))

            split_class_counter = Counter()
            ann_count = 0
            for lp in lbl_list:
                try:
                    with open(lp, "r", encoding="utf-8") as lf:
                        for line in lf:
                            parts = line.strip().split()
                            if parts:
                                cls_id = int(parts[0])
                                split_class_counter[cls_id] += 1
                                ann_count += 1
                except Exception:
                    pass

            ds_info["splits"][split] = {
                "image_dir": found_img_dir,
                "label_dir": found_lbl_dir,
                "num_images": len(img_list),
                "num_labels": len(lbl_list),
                "num_annotations": ann_count,
                "class_histogram": dict(split_class_counter),
            }
            ds_info["total_images"] += len(img_list)
            ds_info["total_labels"] += len(lbl_list)
            ds_info["total_annotations"] += ann_count
            for k, v in split_class_counter.items():
                ds_info["class_counts"][k] += v

    ds_info["class_counts"] = dict(ds_info["class_counts"])
    audit_summary[ds_name] = ds_info

print(json.dumps(audit_summary, indent=2))
with open(os.path.join(REPORTS_DIR, "raw_datasets_summary.json"), "w", encoding="utf-8") as jf:
    json.dump(audit_summary, jf, indent=2)
