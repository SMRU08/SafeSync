"""
scripts/dataset/audit_gloves_annotations.py — SafeSync Gloves Annotation Audit
Inspects existing dataset and external candidate datasets to audit:
- Coordinate validity (x, y, w, h within [0, 1])
- Glove instances count and distribution (single, pair, multi-worker)
- Small (<32x32), Medium, Large glove instance categorization
- Bare hand (no_gloves) co-occurrence vs glove instances
- Missing labels, malformed lines, or out-of-bound boxes
Outputs: reports/gloves_detection/annotation_audit.json
"""

import os
import sys
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def audit_yolo_labels(labels_dir, glove_class_ids, bare_hand_class_ids=None):
    if bare_hand_class_ids is None:
        bare_hand_class_ids = set()
    if isinstance(glove_class_ids, int):
        glove_class_ids = {glove_class_ids}

    stats = {
        "total_files": 0,
        "files_with_gloves": 0,
        "files_without_gloves": 0,
        "files_with_single_glove": 0,
        "files_with_pair_gloves": 0,
        "files_with_multi_gloves": 0,  # > 2
        "files_with_bare_hands": 0,
        "total_glove_instances": 0,
        "total_bare_hand_instances": 0,
        "scale_distribution": {
            "small_area_under_0_0025": 0,
            "medium_area_0_0025_to_0_0225": 0,
            "large_area_above_0_0225": 0,
        },
        "malformed_lines": 0,
        "out_of_bounds_boxes": 0,
        "invalid_coords": 0,
    }

    if not os.path.exists(labels_dir):
        return stats

    for root, _, files in os.walk(labels_dir):
        for fname in files:
            if not fname.endswith(".txt"):
                continue
            stats["total_files"] += 1
            fpath = os.path.join(root, fname)

            glove_boxes = []
            bare_hand_boxes = []

            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for line_idx, line in enumerate(f):
                    parts = line.strip().split()
                    if not parts:
                        continue
                    if len(parts) < 5:
                        stats["malformed_lines"] += 1
                        continue

                    try:
                        cid = int(parts[0])
                        x, y, w, h = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                    except ValueError:
                        stats["malformed_lines"] += 1
                        continue

                    # Validate coordinates
                    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and w > 0.0 and h > 0.0):
                        stats["invalid_coords"] += 1
                        continue

                    # Check bounding box boundaries
                    x1, y1 = x - w / 2.0, y - h / 2.0
                    x2, y2 = x + w / 2.0, y + h / 2.0
                    if x1 < -0.05 or y1 < -0.05 or x2 > 1.05 or y2 > 1.05:
                        stats["out_of_bounds_boxes"] += 1

                    if cid in glove_class_ids:
                        area = w * h
                        glove_boxes.append((x, y, w, h, area))
                        if area < 0.0025:
                            stats["scale_distribution"]["small_area_under_0_0025"] += 1
                        elif area < 0.0225:
                            stats["scale_distribution"]["medium_area_0_0025_to_0_0225"] += 1
                        else:
                            stats["scale_distribution"]["large_area_above_0_0225"] += 1

                    elif cid in bare_hand_class_ids:
                        bare_hand_boxes.append((x, y, w, h))

            n_gloves = len(glove_boxes)
            stats["total_glove_instances"] += n_gloves
            stats["total_bare_hand_instances"] += len(bare_hand_boxes)

            if n_gloves == 0:
                stats["files_without_gloves"] += 1
            elif n_gloves == 1:
                stats["files_with_gloves"] += 1
                stats["files_with_single_glove"] += 1
            elif n_gloves == 2:
                stats["files_with_gloves"] += 1
                stats["files_with_pair_gloves"] += 1
            else:
                stats["files_with_gloves"] += 1
                stats["files_with_multi_gloves"] += 1

            if len(bare_hand_boxes) > 0:
                stats["files_with_bare_hands"] += 1

    return stats


def main():
    print("Running SafeSync Gloves Annotation Audit across datasets...")

    datasets_to_audit = {
        "production_safesync_train": {
            "path": ROOT / "data" / "processed" / "safesync" / "labels" / "train",
            "glove_cids": {3},
            "bare_hand_cids": set(),
            "notes": "Current baseline training dataset (7-class canonical: 3=gloves)",
        },
        "production_safesync_val": {
            "path": ROOT / "data" / "processed" / "safesync" / "labels" / "val",
            "glove_cids": {3},
            "bare_hand_cids": set(),
            "notes": "Frozen evaluation validation split",
        },
        "production_safesync_test": {
            "path": ROOT / "data" / "processed" / "safesync" / "labels" / "test",
            "glove_cids": {3},
            "bare_hand_cids": set(),
            "notes": "Frozen evaluation test split",
        },
        "ultralytics_construction_ppe": {
            "path": ROOT / "datasets" / "raw" / "ultralytics_construction_ppe" / "labels",
            "glove_cids": {1},
            "bare_hand_cids": {9},  # 9 is no_gloves
            "notes": "Ultralytics construction PPE (1=gloves, 9=no_gloves)",
        },
        "ppe_detection_compliance": {
            "path": ROOT / "datasets" / "raw" / "ppe_detection_compliance",
            "glove_cids": {1},      # 1=Gloves
            "bare_hand_cids": {6},  # 6=NO-Gloves
            "notes": "Roboflow PPE Detection & Compliance (1=Gloves, 6=NO-Gloves)",
        },
        "safety_ppe_4": {
            "path": ROOT / "datasets" / "raw" / "safety_ppe_4",
            "glove_cids": {1},      # 1=gloves
            "bare_hand_cids": {5},  # 5=no-gloves
            "notes": "Roboflow Safety PPE 4 (1=gloves, 5=no-gloves)",
        },
    }

    results = {}
    for dname, info in datasets_to_audit.items():
        print(f"Auditing: {dname} ...")
        stats = audit_yolo_labels(
            labels_dir=info["path"],
            glove_class_ids=info["glove_cids"],
            bare_hand_class_ids=info["bare_hand_cids"],
        )
        stats["notes"] = info["notes"]
        results[dname] = stats

    out_file = ROOT / "reports" / "gloves_detection" / "annotation_audit.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "audit_version": "1.0.0",
                "timestamp": "2026-10-09T10:55:00Z",
                "summary": "Annotation audit evaluating glove coordinates, scale, and negative class co-occurrence",
                "datasets": results,
            },
            f,
            indent=2,
        )

    print(f"\nAudit complete! Report saved to {out_file}")


if __name__ == "__main__":
    main()
