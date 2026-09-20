import argparse
import logging
import os
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("download_dataset")

# Add scripts directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from adapters.roboflow_adapter import RoboflowAdapter
from adapters.github_adapter import GitHubAdapter
from adapters.d_fire_adapter import DFireAdapter


DATASET_CONFIGS = {
    "ppe_compliance": {
        "type": "roboflow",
        "workspace": "izanagi",
        "project": "ppe-detection-and-compliance",
        "version": 1,
        "target": PROJECT_ROOT / "datasets" / "raw" / "ppe_detection_compliance",
    },
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
        "version": 2,
        "target": PROJECT_ROOT / "datasets" / "raw" / "hard_hat_workers",
    },
    "d_fire": {
        "type": "github",
        "repo_url": "https://github.com/gaia-solutions-on-demand/DFireDataset.git",
        "target": PROJECT_ROOT / "datasets" / "raw" / "d_fire",
    }
}


def download_target(target_name: str, api_key: str = None) -> bool:
    if target_name not in DATASET_CONFIGS:
        logger.error("Unknown dataset identifier: %s", target_name)
        return False

    cfg = DATASET_CONFIGS[target_name]
    logger.info("Initiating download process for: %s", target_name)

    if cfg["type"] == "roboflow":
        adapter = RoboflowAdapter(api_key=api_key)
        return adapter.download_dataset(
            workspace=cfg["workspace"],
            project_id=cfg["project"],
            version=cfg["version"],
            target_dir=cfg["target"]
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
        choices=["ppe_compliance", "construction_ppe", "hard_hat", "d_fire", "all"],
        default="all",
        help="Specify which dataset to download."
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Roboflow API key (or set ROBOFLOW_API_KEY environment variable)."
    )
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("ROBOFLOW_API_KEY")
    targets = list(DATASET_CONFIGS.keys()) if args.dataset == "all" else [args.dataset]

    results = {}
    for t in targets:
        success = download_target(t, api_key=api_key)
        results[t] = "SUCCESS" if success else "FAILED/AUTH_REQUIRED"

    logger.info("=== Download Summary ===")
    for k, v in results.items():
        logger.info("%s: %s", k, v)


if __name__ == "__main__":
    main()