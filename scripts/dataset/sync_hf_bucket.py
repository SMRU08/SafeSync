"""
scripts/dataset/sync_hf_bucket.py — SafeSync
Resumable sync of smrutiranjannayakcs/PPE_Detection-bucket into data/raw/huggingface/PPE_Detection-bucket/
Supports HTTP 206 Partial Content resume and automatic retry on connection timeout.
"""

import os
import sys
import time
import zipfile
import requests
from pathlib import Path
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent.parent
TARGET_DIR = ROOT / "data" / "raw" / "huggingface" / "PPE_Detection-bucket"
TARGET_DIR.mkdir(parents=True, exist_ok=True)

BUCKET_NAME = "smrutiranjannayakcs/PPE_Detection-bucket"
TOTAL_SIZE = 667690668  # PPE.zip exact bytes
URL_ZIP = f"https://huggingface.co/buckets/{BUCKET_NAME}/resolve/PPE.zip"


def download_resumable(url: str, dest_path: Path, expected_size: int, max_retries: int = 20):
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    while True:
        current_size = dest_path.stat().st_size if dest_path.exists() else 0
        if current_size >= expected_size:
            print(f"[VERIFIED] {dest_path.name} already fully downloaded ({current_size / (1024*1024):.2f} MB)")
            return True

        headers = {}
        if current_size > 0:
            headers["Range"] = f"bytes={current_size}-"
            print(f"[RESUMING] {dest_path.name} from {current_size / (1024*1024):.2f} MB / {expected_size / (1024*1024):.2f} MB ...")
        else:
            print(f"[STARTING] {dest_path.name} (Total: {expected_size / (1024*1024):.2f} MB) ...")

        for attempt in range(1, max_retries + 1):
            try:
                with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                    if r.status_code not in (200, 206):
                        print(f"Server returned status {r.status_code}, retrying...")
                        time.sleep(2)
                        continue

                    mode = "ab" if current_size > 0 else "wb"
                    with open(dest_path, mode) as f:
                        with tqdm(
                            total=expected_size,
                            initial=current_size,
                            unit="B",
                            unit_scale=True,
                            desc=dest_path.name,
                        ) as pbar:
                            for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1MB
                                if chunk:
                                    f.write(chunk)
                                    pbar.update(len(chunk))
                break
            except Exception as e:
                print(f"Network glitch ({e}), retrying in 3s (attempt {attempt}/{max_retries})...")
                time.sleep(3)
                break  # Break retry loop to recompute current_size and re-issue Range header


def sync_all():
    zip_path = TARGET_DIR / "PPE.zip"
    download_resumable(URL_ZIP, zip_path, TOTAL_SIZE)

    # Verify zip integrity
    print(f"\nVerifying {zip_path.name} integrity...")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            bad_file = zf.testzip()
            if bad_file:
                print(f"ERROR: Corrupt file in zip: {bad_file}")
                return False
            namelist = zf.namelist()
            print(f"SUCCESS! Valid zip file with {len(namelist)} items.")
            print(f"Sample entries: {namelist[:10]}")

            # Check if extracted
            extract_dir = TARGET_DIR / "extracted"
            if not extract_dir.exists() or len(list(extract_dir.glob("*"))) == 0:
                print(f"Extracting {zip_path.name} into {extract_dir} ...")
                extract_dir.mkdir(parents=True, exist_ok=True)
                zf.extractall(extract_dir)
                print("Extraction complete!")
            else:
                print(f"Already extracted in {extract_dir}.")
    except Exception as e:
        print(f"Zip validation error: {e}")
        return False

    return True


if __name__ == "__main__":
    sync_all()
