import argparse
import hashlib
import json
import logging
from pathlib import Path
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("remove_duplicates")


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def compute_dhash(image_path: Path, hash_size: int = 8) -> str:
    try:
        with Image.open(image_path) as img:
            img = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            pixels = list(img.getdata())
            diff = []
            for row in range(hash_size):
                for col in range(hash_size):
                    left = pixels[row * (hash_size + 1) + col]
                    right = pixels[row * (hash_size + 1) + col + 1]
                    diff.append(left > right)
            return "".join("1" if b else "0" for b in diff)
    except Exception:
        return ""


def find_duplicates(images_dir: Path, output_report: Path):
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images = [f for f in images_dir.rglob("*") if f.suffix.lower() in image_exts]

    sha_map = {}
    dhash_map = {}
    exact_duplicates = []
    near_duplicates = []

    logger.info("Scanning %d images for duplicates...", len(images))

    for img in images:
        sha = compute_sha256(img)
        if sha in sha_map:
            exact_duplicates.append({"original": str(sha_map[sha]), "duplicate": str(img), "sha256": sha})
        else:
            sha_map[sha] = img

        dh = compute_dhash(img)
        if dh:
            if dh in dhash_map:
                near_duplicates.append({"original": str(dhash_map[dh]), "near_duplicate": str(img)})
            else:
                dhash_map[dh] = img

    output_report.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "scanned_images": len(images),
        "exact_duplicates_count": len(exact_duplicates),
        "exact_duplicates": exact_duplicates,
        "near_duplicates_count": len(near_duplicates),
        "near_duplicates": near_duplicates
    }

    with open(output_report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Duplicate check complete. Found %d exact, %d near duplicates. Saved to %s",
                len(exact_duplicates), len(near_duplicates), output_report)


def main():
    parser = argparse.ArgumentParser(description="Find exact and near duplicate images.")
    parser.add_argument("--images", required=True, help="Directory containing images.")
    parser.add_argument("--output", default="datasets/reports/duplicates.json", help="Path to duplicates.json")
    args = parser.parse_args()

    find_duplicates(Path(args.images), Path(args.output))


if __name__ == "__main__":
    main()