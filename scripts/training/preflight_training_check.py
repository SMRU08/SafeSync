"""
preflight_training_check.py — RAKSHYA VISION Phase 3
Validates data.yaml, all 3 splits (images + labels), label integrity,
and verifies the 7 canonical class IDs before training begins.
Exits with code 0 on success, 1 on any failure.
"""

import os
import sys
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_YAML = os.path.join(ROOT, "datasets", "processed", "data.yaml")
CANONICAL_CLASSES = {0, 1, 2, 3, 4, 5, 6}
CANONICAL_NAMES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}

errors = []
warnings = []


def fail(msg):
    errors.append(msg)
    print(f"  [FAIL]  {msg}")


def warn(msg):
    warnings.append(msg)
    print(f"  [WARN]  {msg}")


def ok(msg):
    print(f"  [ OK ]  {msg}")


def check_data_yaml():
    print("\n[1] Checking data.yaml ...")
    if not os.path.isfile(DATA_YAML):
        fail(f"data.yaml not found at: {DATA_YAML}")
        return None

    with open(DATA_YAML) as f:
        cfg = yaml.safe_load(f)

    base_path = cfg.get("path", "")
    if not os.path.isabs(base_path):
        fail(f"data.yaml 'path' is relative: {base_path}  (must be absolute)")
    elif not os.path.isdir(base_path):
        fail(f"data.yaml 'path' does not exist: {base_path}")
    else:
        ok(f"base path exists: {base_path}")

    names = cfg.get("names", {})
    for cls_id, cls_name in CANONICAL_NAMES.items():
        if names.get(cls_id) != cls_name:
            fail(f"Class mismatch: expected names[{cls_id}]='{cls_name}', got '{names.get(cls_id)}'")
        else:
            ok(f"Class {cls_id}: {cls_name}")

    return cfg


def check_split(cfg, split):
    print(f"\n[2] Checking split: {split} ...")
    base = cfg.get("path", "")
    split_key = {"train": "train", "val": "val", "test": "test"}.get(split, split)
    rel = cfg.get(split_key, f"images/{split}")
    img_dir = os.path.join(base, rel)
    lbl_dir = img_dir.replace("images", "labels")

    if not os.path.isdir(img_dir):
        fail(f"Image directory missing: {img_dir}")
        return
    if not os.path.isdir(lbl_dir):
        fail(f"Label directory missing: {lbl_dir}")
        return

    img_exts = {".jpg", ".jpeg", ".png", ".bmp"}
    images = [f for f in os.listdir(img_dir)
              if os.path.splitext(f)[1].lower() in img_exts]
    labels = [f for f in os.listdir(lbl_dir) if f.endswith(".txt")]
    ok(f"{split}: {len(images)} images, {len(labels)} label files")

    if len(images) == 0:
        fail(f"{split}: no images found")

    # Verify label integrity (sample up to 2000 files)
    invalid_boxes = 0
    invalid_class = 0
    empty_labels = 0
    checked = 0
    sample = labels[:2000]

    for lf in sample:
        lp = os.path.join(lbl_dir, lf)
        with open(lp) as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        if not lines:
            empty_labels += 1
            continue
        for line in lines:
            parts = line.split()
            if len(parts) < 5:
                invalid_boxes += 1
                continue
            try:
                cls_id = int(parts[0])
                cx, cy, w, h = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
            except ValueError:
                invalid_boxes += 1
                continue
            if cls_id not in CANONICAL_CLASSES:
                invalid_class += 1
            if not (0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0 and
                    0.0 < w <= 1.0 and 0.0 < h <= 1.0):
                invalid_boxes += 1
        checked += 1

    ok(f"{split}: {checked}/{len(sample)} labels checked")
    if empty_labels:
        warn(f"{split}: {empty_labels} empty label files (background images — OK if expected)")
    if invalid_boxes:
        fail(f"{split}: {invalid_boxes} invalid bounding boxes found")
    else:
        ok(f"{split}: all bounding boxes valid")
    if invalid_class:
        fail(f"{split}: {invalid_class} annotations with out-of-range class IDs")
    else:
        ok(f"{split}: all class IDs in valid range [0..6]")


def check_model_output_dir():
    print("\n[3] Checking model output directory ...")
    model_dir = os.path.join(ROOT, "models", "detection", "ppe_fire_smoke_v1")
    os.makedirs(model_dir, exist_ok=True)
    ok(f"Model output directory ready: {model_dir}")


def main():
    print("=" * 60)
    print("  RAKSHYA VISION — Phase 3 Pre-flight Training Check")
    print("=" * 60)

    cfg = check_data_yaml()
    if cfg is None:
        print("\n[ABORT] data.yaml check failed. Cannot proceed.")
        sys.exit(1)

    for split in ["train", "val", "test"]:
        check_split(cfg, split)

    check_model_output_dir()

    print("\n" + "=" * 60)
    if errors:
        print(f"  PRE-FLIGHT FAILED — {len(errors)} error(s), {len(warnings)} warning(s)")
        for e in errors:
            print(f"    ERROR: {e}")
        sys.exit(1)
    else:
        print(f"  PRE-FLIGHT PASSED — {len(warnings)} warning(s)")
        for w in warnings:
            print(f"    WARN: {w}")
        print("  Training may proceed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
