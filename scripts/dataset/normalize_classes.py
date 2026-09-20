import argparse
import json
import logging
import shutil
import yaml
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("normalize_classes")


def load_mapping(mapping_file: Path) -> tuple[dict, set]:
    with open(mapping_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    name_to_id = {name.lower(): int(cid) for cid, name in config.get("canonical_classes", {}).items()}
    alias_to_id = {}

    for canon_name, aliases in config.get("mappings", {}).items():
        cid = name_to_id.get(canon_name.lower())
        if cid is not None:
            alias_to_id[canon_name.lower()] = cid
            for alias in aliases:
                alias_to_id[alias.lower()] = cid

    ignored = {name.lower() for name in config.get("ignored_in_detector", [])}
    return alias_to_id, ignored


def polygon_to_bbox(coords: list[float]) -> tuple[float, float, float, float]:
    xs = coords[0::2]
    ys = coords[1::2]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    w = max_x - min_x
    h = max_y - min_y
    return cx, cy, w, h


def process_dataset(
    dataset_name: str,
    prefix: str,
    raw_dir: Path,
    staging_images_dir: Path,
    staging_labels_dir: Path,
    alias_to_id: dict,
    ignored: set,
    unmapped_counts: dict
) -> tuple[int, int]:
    yaml_candidates = list(raw_dir.glob("*.yaml")) + list(raw_dir.glob("*.yml"))
    if not yaml_candidates:
        logger.warning("No data.yaml found in %s, skipping.", raw_dir)
        return 0, 0

    with open(yaml_candidates[0], "r", encoding="utf-8") as f:
        raw_cfg = yaml.safe_load(f)

    raw_names = raw_cfg.get("names", [])
    if isinstance(raw_names, dict):
        raw_names = [raw_names[k] for k in sorted(raw_names.keys())]

    logger.info("Processing %s with classes: %s", dataset_name, raw_names)

    img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images = [f for f in raw_dir.rglob("*") if f.suffix.lower() in img_exts]

    copied_images = 0
    generated_labels = 0

    for img_file in images:
        dest_stem = f"{prefix}_{img_file.stem}"
        dest_img = staging_images_dir / f"{dest_stem}{img_file.suffix}"

        # Find corresponding label
        label_candidate = img_file.parent.parent / "labels" / f"{img_file.stem}.txt"
        if not label_candidate.exists():
            label_candidate = img_file.parent / f"{img_file.stem}.txt"

        new_lines = []
        if label_candidate.exists():
            try:
                with open(label_candidate, "r", encoding="utf-8") as lf:
                    for line in lf:
                        parts = line.strip().split()
                        if not parts:
                            continue
                        try:
                            orig_cls_id = int(parts[0])
                            if orig_cls_id < len(raw_names):
                                orig_name = str(raw_names[orig_cls_id]).lower()
                            else:
                                orig_name = f"unknown_{orig_cls_id}"
                        except ValueError:
                            continue

                        if orig_name in ignored:
                            continue

                        if orig_name in alias_to_id:
                            canon_id = alias_to_id[orig_name]
                            
                            # Standard bounding box
                            if len(parts) == 5:
                                cx, cy, w, h = map(float, parts[1:])
                            # Polygon segmentation to bounding box
                            elif len(parts) > 5 and len(parts) % 2 == 1:
                                coords = [float(p) for p in parts[1:]]
                                cx, cy, w, h = polygon_to_bbox(coords)
                            else:
                                continue

                            # Clamp coordinates within [0, 1]
                            cx = max(0.0, min(1.0, cx))
                            cy = max(0.0, min(1.0, cy))
                            w = max(0.001, min(1.0, w))
                            h = max(0.001, min(1.0, h))

                            new_lines.append(f"{canon_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
                        else:
                            unmapped_counts[orig_name] = unmapped_counts.get(orig_name, 0) + 1
            except Exception as e:
                logger.error("Error reading %s: %s", label_candidate, e)

        # Copy image
        shutil.copy2(img_file, dest_img)
        copied_images += 1

        # Write normalized label
        dest_lbl = staging_labels_dir / f"{dest_stem}.txt"
        with open(dest_lbl, "w", encoding="utf-8") as out_f:
            for nl in new_lines:
                out_f.write(nl + "\n")
        generated_labels += 1

    return copied_images, generated_labels


def main():
    parser = argparse.ArgumentParser(description="Normalize multiple raw datasets into canonical YOLO format.")
    parser.add_argument("--raw-base", default="datasets/raw", help="Base raw datasets directory.")
    parser.add_argument("--staging-dir", default="datasets/staging", help="Staging output directory.")
    parser.add_argument("--mapping", default="datasets/manifests/class_mapping.yaml", help="Class mapping YAML.")
    parser.add_argument("--unmapped-report", default="datasets/reports/unmapped_classes.json", help="Report path.")
    args = parser.parse_args()

    raw_base = Path(args.raw_base)
    staging_dir = Path(args.staging_dir)
    staging_images = staging_dir / "images"
    staging_labels = staging_dir / "labels"

    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_images.mkdir(parents=True, exist_ok=True)
    staging_labels.mkdir(parents=True, exist_ok=True)

    alias_to_id, ignored = load_mapping(Path(args.mapping))
    unmapped_counts = {}

    targets = [
        ("construction_ppe", "cppe", raw_base / "construction_ppe"),
        ("hard_hat_workers", "hhw", raw_base / "hard_hat_workers"),
        ("ppe_detection_compliance", "ppec", raw_base / "ppe_detection_compliance"),
        ("d_fire_smoke", "fs", raw_base / "d_fire" / "fire_smoke"),
    ]

    total_images = 0
    total_labels = 0

    for name, prefix, path in targets:
        if path.exists():
            n_img, n_lbl = process_dataset(
                name, prefix, path, staging_images, staging_labels, alias_to_id, ignored, unmapped_counts
            )
            logger.info("Dataset %s: %d images, %d labels staged.", name, n_img, n_lbl)
            total_images += n_img
            total_labels += n_lbl

    unmapped_path = Path(args.unmapped_report)
    unmapped_path.parent.mkdir(parents=True, exist_ok=True)
    unmapped_list = [
        {"class_name": k, "count": v, "reason_not_mapped": "Ignored or absent from canonical schema"}
        for k, v in sorted(unmapped_counts.items(), key=lambda x: -x[1])
    ]
    with open(unmapped_path, "w", encoding="utf-8") as uf:
        json.dump(unmapped_list, uf, indent=2)

    logger.info("Normalization complete. Staged %d images, %d labels. Unmapped classes saved to %s",
                total_images, total_labels, unmapped_path)


if __name__ == "__main__":
    main()