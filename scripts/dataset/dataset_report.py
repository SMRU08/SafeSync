import argparse
import csv
import json
import logging
from pathlib import Path
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("dataset_report")

CANONICAL_NAMES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke"
}


def count_labels_in_split(labels_dir: Path) -> dict:
    counts = {name: 0 for name in CANONICAL_NAMES.values()}
    if not labels_dir.exists():
        return counts

    for f in labels_dir.glob("*.txt"):
        try:
            with open(f, "r", encoding="utf-8") as lf:
                for line in lf:
                    parts = line.strip().split()
                    if parts:
                        cls_id = int(parts[0])
                        if cls_id in CANONICAL_NAMES:
                            counts[CANONICAL_NAMES[cls_id]] += 1
        except Exception:
            pass
    return counts


def analyze_image_quality(images_dir: Path, output_file: Path):
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images = [f for f in images_dir.rglob("*") if f.suffix.lower() in image_exts]

    corrupted = []
    zero_bytes = []
    small_images = []
    valid = 0

    for img_path in images:
        if img_path.stat().st_size == 0:
            zero_bytes.append(str(img_path))
            continue

        try:
            with Image.open(img_path) as img:
                img.verify()
            with Image.open(img_path) as img:
                w, h = img.size
                if w < 64 or h < 64:
                    small_images.append({"file": str(img_path), "width": w, "height": h})
                else:
                    valid += 1
        except Exception as exc:
            corrupted.append({"file": str(img_path), "error": str(exc)})

    report = {
        "scanned_images": len(images),
        "valid_images": valid,
        "corrupted_images_count": len(corrupted),
        "corrupted_images": corrupted,
        "zero_byte_count": len(zero_bytes),
        "zero_byte_images": zero_bytes,
        "extremely_small_images_count": len(small_images),
        "extremely_small_images": small_images
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Image quality report generated at %s", output_file)


def generate_class_distribution_reports(processed_dir: Path, json_out: Path, csv_out: Path):
    splits = ["train", "val", "test"]
    split_counts = {s: count_labels_in_split(processed_dir / "labels" / s) for s in splits}

    total_per_class = {
        name: sum(split_counts[s][name] for s in splits)
        for name in CANONICAL_NAMES.values()
    }
    grand_total = sum(total_per_class.values())

    rows = []
    distribution_json = {}

    for name in CANONICAL_NAMES.values():
        tot = total_per_class[name]
        pct = (tot / grand_total * 100) if grand_total > 0 else 0.0
        row = {
            "class_name": name,
            "train": split_counts["train"][name],
            "validation": split_counts["val"][name],
            "test": split_counts["test"][name],
            "total": tot,
            "percentage": round(pct, 2)
        }
        rows.append(row)
        distribution_json[name] = row

    json_out.parent.mkdir(parents=True, exist_ok=True)
    with open(json_out, "w", encoding="utf-8") as jf:
        json.dump(distribution_json, jf, indent=2)

    with open(csv_out, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=["class_name", "train", "validation", "test", "total", "percentage"])
        writer.writeheader()
        writer.writerows(rows)

    logger.info("Class distribution reports generated: %s and %s", json_out, csv_out)


def main():
    parser = argparse.ArgumentParser(description="Generate dataset reports and metrics.")
    parser.add_argument("--processed-dir", default="datasets/processed")
    parser.add_argument("--reports-dir", default="datasets/reports")
    args = parser.parse_args()

    processed_dir = Path(args.processed_dir)
    reports_dir = Path(args.reports_dir)

    analyze_image_quality(processed_dir / "images", reports_dir / "image_quality.json")
    generate_class_distribution_reports(
        processed_dir,
        reports_dir / "class_distribution.json",
        reports_dir / "class_distribution.csv"
    )


if __name__ == "__main__":
    main()