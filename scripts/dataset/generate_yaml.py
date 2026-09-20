import argparse
import logging
import yaml
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("generate_yaml")

CANONICAL_NAMES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke"
}


def generate_data_yaml(processed_dir: Path, output_file: Path):
    processed_dir = processed_dir.resolve()
    train_dir = processed_dir / "images" / "train"
    val_dir = processed_dir / "images" / "val"
    test_dir = processed_dir / "images" / "test"

    config = {
        "path": str(processed_dir).replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": CANONICAL_NAMES
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, sort_keys=False)

    logger.info("Generated data.yaml at %s", output_file)
    logger.info("Path verification: train=%s, val=%s, test=%s",
                train_dir.exists(), val_dir.exists(), test_dir.exists())


def main():
    parser = argparse.ArgumentParser(description="Generate YOLO data.yaml configuration.")
    parser.add_argument("--processed-dir", default="datasets/processed", help="Base directory of processed data.")
    parser.add_argument("--output", default="datasets/processed/data.yaml", help="Destination data.yaml path.")
    args = parser.parse_args()

    generate_data_yaml(Path(args.processed_dir), Path(args.output))


if __name__ == "__main__":
    main()