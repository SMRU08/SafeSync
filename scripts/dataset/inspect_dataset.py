import argparse
import logging
from pathlib import Path
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("inspect_dataset")


def inspect_directory(directory_path: Path) -> dict:
    if not directory_path.exists():
        logger.warning("Directory does not exist: %s", directory_path)
        return {"exists": False}

    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images = [f for f in directory_path.rglob("*") if f.suffix.lower() in image_extensions]
    labels = list(directory_path.rglob("*.txt"))

    resolutions = set()
    corrupted = 0

    for img_path in images[:100]:  # Sample first 100 images for dimension checks
        try:
            with Image.open(img_path) as img:
                resolutions.add(img.size)
        except Exception:
            corrupted += 1

    class_histogram = {}
    for lbl_path in labels:
        try:
            with open(lbl_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        cls_id = parts[0]
                        class_histogram[cls_id] = class_histogram.get(cls_id, 0) + 1
        except Exception:
            pass

    return {
        "exists": True,
        "path": str(directory_path),
        "image_count": len(images),
        "label_count": len(labels),
        "sample_resolutions": [list(r) for r in resolutions],
        "corrupted_samples": corrupted,
        "class_histogram": class_histogram
    }


def main():
    parser = argparse.ArgumentParser(description="Inspect dataset directory structure and contents.")
    parser.add_argument("path", type=str, help="Path to the dataset directory to inspect.")
    args = parser.parse_args()

    result = inspect_directory(Path(args.path))
    logger.info("Inspection Result for %s:", args.path)
    for k, v in result.items():
        logger.info("  %s: %s", k, v)


if __name__ == "__main__":
    main()