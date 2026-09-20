import argparse
import json
import logging
import math
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("validate_annotations")


def validate_dataset(images_dir: Path, labels_dir: Path, max_class_id: int = 6) -> dict:
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images = {f.stem: f for f in images_dir.rglob("*") if f.suffix.lower() in image_exts}
    labels = {f.stem: f for f in labels_dir.rglob("*.txt")}

    total_images = len(images)
    total_labels = len(labels)

    valid_images = 0
    invalid_images = 0
    valid_labels = 0
    invalid_labels = 0
    missing_labels = 0
    invalid_class_ids = 0
    invalid_boxes = 0

    for stem, img_path in images.items():
        if stem not in labels:
            # Negative image or missing label
            missing_labels += 1
            continue

        lbl_path = labels[stem]
        has_error = False

        try:
            with open(lbl_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line_idx, line in enumerate(lines, 1):
                parts = line.strip().split()
                if not parts:
                    continue
                if len(parts) != 5:
                    invalid_boxes += 1
                    has_error = True
                    continue

                try:
                    cls_id = int(parts[0])
                    cx = float(parts[1])
                    cy = float(parts[2])
                    w = float(parts[3])
                    h = float(parts[4])
                except ValueError:
                    invalid_boxes += 1
                    has_error = True
                    continue

                if any(math.isnan(v) or math.isinf(v) for v in [cx, cy, w, h]):
                    invalid_boxes += 1
                    has_error = True
                    continue

                if cls_id < 0 or cls_id > max_class_id:
                    invalid_class_ids += 1
                    has_error = True

                if not (0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0):
                    invalid_boxes += 1
                    has_error = True

            if has_error:
                invalid_labels += 1
                invalid_images += 1
            else:
                valid_labels += 1
                valid_images += 1

        except Exception as exc:
            logger.error("Error reading label %s: %s", lbl_path, exc)
            invalid_labels += 1
            invalid_images += 1

    report = {
        "total_images": total_images,
        "valid_images": valid_images,
        "invalid_images": invalid_images,
        "total_labels": total_labels,
        "valid_labels": valid_labels,
        "invalid_labels": invalid_labels,
        "missing_labels": missing_labels,
        "invalid_class_ids": invalid_class_ids,
        "invalid_boxes": invalid_boxes,
        "unknown_classes": invalid_class_ids
    }
    return report


def main():
    parser = argparse.ArgumentParser(description="Validate YOLO format annotations.")
    parser.add_argument("--images", required=True, help="Directory containing images.")
    parser.add_argument("--labels", required=True, help="Directory containing labels.")
    parser.add_argument("--output", default="datasets/reports/annotation_validation.json", help="Path to save report.")
    args = parser.parse_args()

    report = validate_dataset(Path(args.images), Path(args.labels))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Annotation validation finished. Report written to %s", out_path)


if __name__ == "__main__":
    main()