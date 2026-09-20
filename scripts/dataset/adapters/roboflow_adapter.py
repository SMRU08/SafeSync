import os
import shutil
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class RoboflowAdapter:
    """Adapter for downloading and inspecting Roboflow Universe / Public datasets."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ROBOFLOW_API_KEY")

    def download_dataset(
        self,
        workspace: str,
        project_id: str,
        version: int,
        target_dir: Path,
        model_format: str = "yolov8"
    ) -> bool:
        if not self.api_key:
            logger.error("ROBOFLOW_API_KEY is not set. An API key is required to export from Roboflow.")
            return False

        try:
            from roboflow import Roboflow
            rf = Roboflow(api_key=self.api_key)
            project = rf.workspace(workspace).project(project_id)
            version_obj = project.version(version)

            target_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Downloading %s/%s v%s...", workspace, project_id, version)

            dataset = version_obj.download(model_format)
            download_loc = Path(dataset.location)

            # Move contents into target_dir if downloaded to a subfolder
            if download_loc.resolve() != target_dir.resolve():
                logger.info("Moving downloaded files from %s to %s...", download_loc, target_dir)
                for item in download_loc.iterdir():
                    dest = target_dir / item.name
                    if dest.exists():
                        if dest.is_dir():
                            shutil.rmtree(dest)
                        else:
                            dest.unlink()
                    shutil.move(str(item), str(target_dir))
                shutil.rmtree(download_loc, ignore_errors=True)

            logger.info("Roboflow download completed successfully for %s into %s", project_id, target_dir)
            return True
        except Exception as exc:
            logger.error("Failed to download %s/%s via Roboflow SDK: %s", workspace, project_id, exc)
            return False