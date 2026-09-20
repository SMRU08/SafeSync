import argparse
import logging
import random
import shutil
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("split_dataset")


def split_data(
    source_images_dir: Path,
    source_labels_dir: Path,
    output_base_dir: Path,
    train_ratio: float = 0.70,
    val_ratio: float = 0.20,
    test_ratio: float = 0.10,
    seed: int = 42
):
    random.seed(seed)
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images = [f for f in source_images_dir.rglob("*") if f.suffix.lower() in image_exts]

    # Shuffle deterministically
    random.shuffle(images)

    total = len(images)
    n_train = int(total * train_ratio)
    n_val = int(total * val_ratio)

    train_set = images[:n_train]
    val_set = images[n_train:n_train + n_val]
    test_set = images[n_train + n_val:]

    splits = {
        "train": train_set,
        "val": val_set,
        "test": test_set
    }

    logger.info("Splitting %d images into Train: %d, Val: %d, Test: %d (Seed: %d)",
                total, len(train_set), len(val_set), len(test_set), seed)

    for split_name, img_list in splits.items():
        img_dest_dir = output_base_dir / "images" / split_name
        lbl_dest_dir = output_base_dir / "labels" / split_name
        img_dest_dir.mkdir(parents=True, exist_ok=True)
        lbl_dest_dir.mkdir(parents=True, exist_ok=True)

        for img_path in img_list:
            shutil.copy2(img_path, img_dest_dir / img_path.name)
            lbl_candidate = source_labels_dir / f"{img_path.stem}.txt"
            if lbl_candidate.exists():
                shutil.copy2(lbl_candidate, lbl_dest_dir / lbl_candidate.name)
            else:
                # Negative background image: create empty label file
                (lbl_dest_dir / f"{img_path.stem}.txt").touch()

    logger.info("Dataset split complete in %s", output_base_dir)


def main():
    parser = argparse.ArgumentParser(description="Split dataset into train, val, and test subsets.")
    parser.add_argument("--images-in", required=True, help="Input images directory.")
    parser.add_argument("--labels-in", required=True, help="Input labels directory.")
    parser.add_argument("--output-base", default="datasets/processed", help="Target processed directory.")
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.20)
    parser.add_argument("--test-ratio", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    split_data(
        Path(args.images_in),
        Path(args.labels_in),
        Path(args.output_base),
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed
    )


if __name__ == "__main__":
    main()