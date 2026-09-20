import argparse
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("download_dataset")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from adapters.roboflow_adapter import RoboflowAdapter
from adapters.github_adapter import GitHubAdapter
from adapters.d_fire_adapter import DFireAdapter


DATASET_CONFIGS = {
    "construction_ppe": {
        "type": "roboflow",
        "workspace": "skcet-g4h72",
        "project": "construction-ppe-rdhzo",
        "version": 1,
        "target": PROJECT_ROOT / "datasets" / "raw" / "construction_ppe",
    },
    "hard_hat": {
        "type": "roboflow",
        "workspace": "joseph-nelson",
        "project": "hard-hat-workers",
        "version": 10,
        "target": PROJECT_ROOT / "datasets" / "raw" / "hard_hat_workers",
    },
    "ppe_compliance": {
        "type": "roboflow",
        "workspace": "izanagi",
        "project": "ppe-detection-and-compliance",
        "version": 2,
        "target": PROJECT_ROOT / "datasets" / "raw" / "ppe_detection_compliance",
    },
    "d_fire": {
        "type": "github",
        "repo_url": "https://github.com/gaia-solutions-on-demand/DFireDataset.git",
        "target": PROJECT_ROOT / "datasets" / "raw" / "d_fire" / "repo",
    }
}


def download_target(target_name: str, api_key: str = None) -> bool:
    if target_name not in DATASET_CONFIGS:
        logger.error("Unknown dataset identifier: %s", target_name)
        return False

    cfg = DATASET_CONFIGS[target_name]
    logger.info("Initiating download for %s...", target_name)

    if cfg["type"] == "roboflow":
        adapter = RoboflowAdapter(api_key=api_key)
        return adapter.download_dataset(
            workspace=cfg["workspace"],
            project_id=cfg["project"],
            version=cfg["version"],
            target_dir=cfg["target"],
            model_format="yolov8"
        )
    elif cfg["type"] == "github":
        adapter = GitHubAdapter()
        return adapter.clone_repository(
            repo_url=cfg["repo_url"],
            target_dir=cfg["target"]
        )
    return False


def main():
    parser = argparse.ArgumentParser(description="Download approved datasets for RAKSHYA VISION.")
    parser.add_argument(
        "--dataset",
        choices=["construction_ppe", "hard_hat", "ppe_compliance", "d_fire", "all"],
        required=True,
        help="Specify dataset to download."
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Roboflow API key."
    )
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("ROBOFLOW_API_KEY")
    success = download_target(args.dataset, api_key=api_key)
    status_str = "SUCCESS" if success else "FAILED"
    logger.info("Result for %s: %s", args.dataset, status_str)


if __name__ == "__main__":
    main()