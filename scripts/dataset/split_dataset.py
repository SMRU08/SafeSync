import argparse
import json
import logging
import random
import shutil
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("split_dataset")


def build_leakage_groups(images: list[Path], duplicates_file: Path) -> list[list[Path]]:
    """Groups duplicate and near-duplicate images together to prevent train/val/test leakage."""
    stem_to_path = {p.stem: p for p in images}
    parent_map = {p.stem: p.stem for p in images}

    def find(x):
        if parent_map[x] != x:
            parent_map[x] = find(parent_map[x])
        return parent_map[x]

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent_map[rx] = ry

    if duplicates_file.exists():
        with open(duplicates_file, "r", encoding="utf-8") as f:
            dup_data = json.load(f)

        for item in dup_data.get("exact_duplicates", []):
            stem1 = Path(item["original"]).stem
            stem2 = Path(item["duplicate"]).stem
            if stem1 in parent_map and stem2 in parent_map:
                union(stem1, stem2)

        for item in dup_data.get("near_duplicates", []):
            stem1 = Path(item["original"]).stem
            stem2 = Path(item["near_duplicate"]).stem
            if stem1 in parent_map and stem2 in parent_map:
                union(stem1, stem2)

    groups_dict = {}
    for p in images:
        root = find(p.stem)
        groups_dict.setdefault(root, []).append(p)

    return list(groups_dict.values())


def split_data(
    source_images_dir: Path,
    source_labels_dir: Path,
    output_base_dir: Path,
    duplicates_file: Path,
    train_ratio: float = 0.70,
    val_ratio: float = 0.20,
    test_ratio: float = 0.10,
    seed: int = 42
):
    random.seed(seed)
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images = [f for f in source_images_dir.rglob("*") if f.suffix.lower() in image_exts]

    groups = build_leakage_groups(images, duplicates_file)
    logger.info("Found %d images clustered into %d leakage-safe groups.", len(images), len(groups))

    # Shuffle groups deterministically
    random.shuffle(groups)

    train_set, val_set, test_set = [], [], []
    total_imgs = len(images)
    target_train = int(total_imgs * train_ratio)
    target_val = int(total_imgs * val_ratio)

    current_train = 0
    current_val = 0

    for grp in groups:
        if current_train < target_train:
            train_set.extend(grp)
            current_train += len(grp)
        elif current_val < target_val:
            val_set.extend(grp)
            current_val += len(grp)
        else:
            test_set.extend(grp)

    splits = {
        "train": train_set,
        "val": val_set,
        "test": test_set
    }

    logger.info("Allocated: Train=%d (%.1f%%), Val=%d (%.1f%%), Test=%d (%.1f%%)",
                len(train_set), len(train_set)/total_imgs*100,
                len(val_set), len(val_set)/total_imgs*100,
                len(test_set), len(test_set)/total_imgs*100)

    # Clean destination directories
    for s in ["train", "val", "test"]:
        img_dest = output_base_dir / "images" / s
        lbl_dest = output_base_dir / "labels" / s
        if img_dest.exists():
            shutil.rmtree(img_dest)
        if lbl_dest.exists():
            shutil.rmtree(lbl_dest)
        img_dest.mkdir(parents=True, exist_ok=True)
        lbl_dest.mkdir(parents=True, exist_ok=True)

    for split_name, img_list in splits.items():
        img_dest_dir = output_base_dir / "images" / split_name
        lbl_dest_dir = output_base_dir / "labels" / split_name

        for img_path in img_list:
            shutil.copy2(img_path, img_dest_dir / img_path.name)
            lbl_candidate = source_labels_dir / f"{img_path.stem}.txt"
            if lbl_candidate.exists():
                shutil.copy2(lbl_candidate, lbl_dest_dir / lbl_candidate.name)
            else:
                (lbl_dest_dir / f"{img_path.stem}.txt").touch()

    logger.info("Dataset split complete in %s", output_base_dir)


def main():
    parser = argparse.ArgumentParser(description="Leakage-safe reproducible dataset splitting.")
    parser.add_argument("--images-in", default="datasets/staging/images")
    parser.add_argument("--labels-in", default="datasets/staging/labels")
    parser.add_argument("--output-base", default="datasets/processed")
    parser.add_argument("--duplicates", default="datasets/reports/duplicates.json")
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.20)
    parser.add_argument("--test-ratio", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    split_data(
        Path(args.images_in),
        Path(args.labels_in),
        Path(args.output_base),
        Path(args.duplicates),
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed
    )


if __name__ == "__main__":
    main()