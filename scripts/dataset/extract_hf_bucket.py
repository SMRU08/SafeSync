"""
scripts/dataset/extract_hf_bucket.py — SafeSync
Safely extracts PPE.zip using Windows extended-length paths (\\\\?\\) to bypass MAX_PATH 260 limit.
"""

import os
import sys
import zipfile
from pathlib import Path
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent.parent
ZIP_PATH = ROOT / "data" / "raw" / "huggingface" / "PPE_Detection-bucket" / "PPE.zip"
EXTRACT_DIR = ROOT / "data" / "raw" / "huggingface" / "PPE_Detection-bucket" / "extracted"
EXTRACT_DIR.mkdir(parents=True, exist_ok=True)


def extract_with_long_paths():
    long_prefix = "\\\\?\\" + str(EXTRACT_DIR.resolve())
    print(f"Extracting {ZIP_PATH.name} to {long_prefix} ...")

    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        members = zf.infolist()
        print(f"Total entries to extract: {len(members)}")

        for member in tqdm(members, desc="Extracting PPE.zip"):
            # Ensure target directory exists with long path (strictly backslashes for \\\\?\\)
            rel_path = member.filename.replace("/", "\\")
            target_path = os.path.join(long_prefix, rel_path)
            if member.is_dir() or member.filename.endswith("/"):
                os.makedirs(target_path, exist_ok=True)
                continue

            target_dir = os.path.dirname(target_path)
            os.makedirs(target_dir, exist_ok=True)

            with zf.open(member) as source, open(target_path, "wb") as target:
                target.write(source.read())

    print("\nExtraction finished successfully!")


if __name__ == "__main__":
    extract_with_long_paths()
