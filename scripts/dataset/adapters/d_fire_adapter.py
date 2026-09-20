import logging
import zipfile
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DFireAdapter:
    """Adapter for importing and validating D-Fire dataset from official archives."""

    @staticmethod
    def unpack_archive(archive_path: Path, target_dir: Path) -> bool:
        if not archive_path.exists():
            logger.error("Archive not found at %s", archive_path)
            return False

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Unpacking D-Fire archive: %s -> %s", archive_path, target_dir)
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            logger.info("Successfully extracted D-Fire archive.")
            return True
        except Exception as exc:
            logger.error("Error unpacking D-Fire archive: %s", exc)
            return False

    @staticmethod
    def verify_structure(raw_dir: Path) -> dict:
        """Verifies D-Fire images and annotation files."""
        images = list(raw_dir.rglob("*.jpg")) + list(raw_dir.rglob("*.png"))
        labels = list(raw_dir.rglob("*.txt"))
        return {
            "total_images": len(images),
            "total_labels": len(labels),
            "directory": str(raw_dir)
        }