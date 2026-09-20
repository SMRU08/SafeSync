import logging
import subprocess
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class GitHubAdapter:
    """Adapter for cloning and downloading datasets hosted on GitHub."""

    @staticmethod
    def clone_repository(repo_url: str, target_dir: Path, branch: Optional[str] = None) -> bool:
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            cmd = ["git", "clone"]
            if branch:
                cmd.extend(["-b", branch])
            cmd.extend([repo_url, str(target_dir)])

            logger.info("Cloning GitHub repository: %s into %s", repo_url, target_dir)
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Cloned repository successfully: %s", repo_url)
            return True
        except subprocess.CalledProcessError as exc:
            logger.error("Git clone failed: %s\nStderr: %s", exc, exc.stderr)
            return False
        except Exception as exc:
            logger.error("Unexpected error cloning repository: %s", exc)
            return False