r"""
download_and_prepare_ndjson.py — SafeSync Dataset Pipeline
==========================================================
Parses .ndjson dataset exports from D:\Additional\PROJECT\nd, downloads images
concurrently via ThreadPoolExecutor with retry logic, maps labels to YOLO format,
organizes standard YOLO directory structure (train / val / test), and generates data.yaml.

Default Ontology (SafeSync 7-Class Canonical):
  0: person
  1: helmet
  2: safety_vest
  3: gloves
  4: safety_footwear
  5: fire
  6: smoke
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm
import yaml

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ndjson_processor")

# ---------------------------------------------------------------------------
# SafeSync Canonical 7-Class Ontology
# ---------------------------------------------------------------------------
SAFESYNC_CANONICAL_CLASSES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}

# Source dataset class name normalization mapping into SafeSync ontology
CANONICAL_NAME_MAPPING = {
    # Person
    "person": 0,
    "Person": 0,
    # Head protection
    "helmet": 1,
    "hard_hat": 1,
    "hardhat": 1,
    # High-vis body protection
    "vest": 2,
    "safety_vest": 2,
    # Distal limb protection
    "gloves": 3,
    "glove": 3,
    # Lower limb protection
    "boots": 4,
    "boot": 4,
    "safety_footwear": 4,
    "footwear": 4,
    # Combustion hazards
    "fire": 5,
    "flame": 5,
    "smoke": 6,
}

# Negative and unsupported classes to exclude from SafeSync positive detector
DROPPED_CLASSES = {
    "goggles",
    "none",
    "no_helmet",
    "no_goggle",
    "no_gloves",
    "no_boots",
}


def create_robust_session(pool_size: int = 64) -> requests.Session:
    """Creates a requests Session with automated exponential backoff retries."""
    session = requests.Session()
    retries = Retry(
        total=4,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(
        max_retries=retries,
        pool_connections=pool_size,
        pool_maxsize=pool_size,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "SafeSync-Dataset-Ingest/1.0 (+https://github.com/SMRU08/SafeSync)"
    })
    return session


def download_single_image(
    task: Dict[str, Any],
    session: requests.Session,
    timeout: Tuple[int, int] = (6, 18),
) -> Tuple[bool, str, str]:
    """
    Downloads an image and writes its corresponding YOLO .txt label.

    Returns:
        (success: bool, status_message: str, image_filename: str)
    """
    img_url = task["url"]
    img_dest = task["img_dest"]
    lbl_dest = task["lbl_dest"]
    labels_content = task["labels_content"]
    file_name = task["file_name"]

    # 1. Skip download if already exists and non-empty (resume capability)
    if img_dest.is_file() and img_dest.stat().st_size > 512:
        # Ensure label file is also in sync
        with open(lbl_dest, "w", encoding="utf-8") as f:
            f.write(labels_content)
        return True, "EXISTS", file_name

    # 2. Download image
    try:
        resp = session.get(img_url, timeout=timeout, stream=True)
        if resp.status_code != 200:
            return False, f"HTTP_{resp.status_code}", file_name

        content = resp.content
        if len(content) < 512:
            return False, "EMPTY_OR_CORRUPT", file_name

        # Write image atomically
        temp_img = img_dest.with_suffix(".tmp")
        with open(temp_img, "wb") as f:
            f.write(content)
        temp_img.replace(img_dest)

        # Write YOLO label .txt
        with open(lbl_dest, "w", encoding="utf-8") as f:
            f.write(labels_content)

        return True, "DOWNLOADED", file_name

    except requests.exceptions.Timeout:
        return False, "TIMEOUT", file_name
    except requests.exceptions.RequestException as e:
        return False, f"REQ_ERR_{type(e).__name__}", file_name
    except Exception as e:
        return False, f"ERR_{str(e)[:30]}", file_name


def parse_ndjson_file(
    ndjson_path: Path,
    mode: str = "safesync",
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Parses a single .ndjson file.
    Line 0 contains dataset metadata with class_names.
    Lines 1..N contain image objects with URL, split, and bounding box annotations.
    """
    logger.info(f"Parsing {ndjson_path.name} ...")
    metadata = {}
    items = []

    with open(ndjson_path, "r", encoding="utf-8") as f:
        # First line is dataset metadata
        first_line = f.readline().strip()
        if not first_line:
            logger.warning(f"File {ndjson_path.name} is empty.")
            return metadata, items

        metadata = json.loads(first_line)
        src_classes = metadata.get("class_names", {})

        # Process remaining image lines
        for line_num, line in enumerate(f, start=2):
            line = line.strip()
            if not line:
                continue
            try:
                img_data = json.loads(line)
                items.append((src_classes, img_data))
            except json.JSONDecodeError as err:
                logger.warning(f"Malformed JSON at line {line_num} in {ndjson_path.name}: {err}")

    logger.info(f"Loaded {len(items)} image records from {ndjson_path.name}")
    return metadata, items


def convert_boxes_to_yolo(
    raw_boxes: List[List[Any]],
    src_classes: Dict[str, str],
    mode: str = "safesync",
    raw_class_map: Optional[Dict[str, int]] = None,
) -> Tuple[List[str], Counter, Counter]:
    """
    Converts raw bounding boxes [class_id, x, y, w, h] to YOLO formatted text lines.
    Clamps coordinates strictly to [0.0, 1.0].
    """
    yolo_lines = []
    class_counter = Counter()
    dropped_counter = Counter()

    for box in raw_boxes:
        if len(box) < 5:
            continue

        raw_id = str(box[0])
        x_c, y_c, w, h = float(box[1]), float(box[2]), float(box[3]), float(box[4])

        # Ensure normalized bounding box bounds
        x_c = max(0.0, min(1.0, x_c))
        y_c = max(0.0, min(1.0, y_c))
        w = max(0.001, min(1.0, w))
        h = max(0.001, min(1.0, h))

        cname = src_classes.get(raw_id, "")

        if mode == "safesync":
            # Map into SafeSync 7 canonical classes
            if cname in CANONICAL_NAME_MAPPING:
                target_cls = CANONICAL_NAME_MAPPING[cname]
                yolo_lines.append(f"{target_cls} {x_c:.6f} {y_c:.6f} {w:.6f} {h:.6f}")
                class_counter[target_cls] += 1
            else:
                dropped_counter[cname or f"id_{raw_id}"] += 1
        else:
            # Raw mode: preserve extracted class names
            if raw_class_map and cname in raw_class_map:
                target_cls = raw_class_map[cname]
                yolo_lines.append(f"{target_cls} {x_c:.6f} {y_c:.6f} {w:.6f} {h:.6f}")
                class_counter[target_cls] += 1

    return yolo_lines, class_counter, dropped_counter


def process_and_download(
    nd_dir: Path,
    output_root: Path,
    mode: str = "safesync",
    max_workers: int = 32,
    single_split: Optional[str] = None,
):
    """
    Main orchestration function:
    1. Parses all .ndjson files in nd_dir.
    2. Builds YOLO label files and download task queue.
    3. Executes multi-threaded image downloads with progress reporting.
    4. Automatically generates data.yaml.
    """
    nd_files = sorted(list(nd_dir.glob("*.ndjson")))
    if not nd_files:
        logger.error(f"No .ndjson files found in {nd_dir}")
        return

    logger.info(f"Found {len(nd_files)} .ndjson files in {nd_dir}:")
    for f in nd_files:
        logger.info(f" - {f.name}")

    # Build raw class mapping if in raw mode
    raw_class_map = {}
    if mode == "raw":
        unique_classes = set()
        for f in nd_files:
            with open(f, "r", encoding="utf-8") as fp:
                meta = json.loads(fp.readline())
                for name in meta.get("class_names", {}).values():
                    unique_classes.add(name)
        raw_class_map = {name: idx for idx, name in enumerate(sorted(unique_classes))}
        logger.info(f"Raw mode unique classes ({len(raw_class_map)}): {raw_class_map}")

    # Setup directories
    datasets_dir = output_root / "datasets"
    images_base = datasets_dir / "images"
    labels_base = datasets_dir / "labels"

    tasks = []
    total_class_counts = Counter()
    total_dropped_counts = Counter()
    seen_files = set()

    for nd_file in nd_files:
        _, items = parse_ndjson_file(nd_file, mode=mode)

        for src_classes, img_data in items:
            file_name = img_data.get("file", "").strip()
            url = img_data.get("url", "").strip()
            if not file_name or not url:
                continue

            # Deduplicate by filename
            if file_name in seen_files:
                continue
            seen_files.add(file_name)

            # Determine split (train, val, test)
            split = single_split if single_split else img_data.get("split", "train").lower()
            if split not in ["train", "val", "test"]:
                split = "train"

            img_dir = images_base / split
            lbl_dir = labels_base / split
            img_dir.mkdir(parents=True, exist_ok=True)
            lbl_dir.mkdir(parents=True, exist_ok=True)

            img_dest = img_dir / file_name
            lbl_dest = lbl_dir / f"{Path(file_name).stem}.txt"

            raw_boxes = img_data.get("annotations", {}).get("boxes", [])
            yolo_lines, cls_counts, dropped_counts = convert_boxes_to_yolo(
                raw_boxes, src_classes, mode=mode, raw_class_map=raw_class_map
            )

            total_class_counts.update(cls_counts)
            total_dropped_counts.update(dropped_counts)

            tasks.append({
                "url": url,
                "file_name": file_name,
                "img_dest": img_dest,
                "lbl_dest": lbl_dest,
                "labels_content": "\n".join(yolo_lines) + ("\n" if yolo_lines else ""),
                "split": split,
            })

    total_tasks = len(tasks)
    logger.info(f"\nPrepared {total_tasks} image download tasks.")
    logger.info("Class distribution in annotations:")
    if mode == "safesync":
        for cid, cname in SAFESYNC_CANONICAL_CLASSES.items():
            logger.info(f"  Class {cid} ({cname}): {total_class_counts[cid]} boxes")
        logger.info(f"  Dropped non-target boxes: {sum(total_dropped_counts.values())}")
    else:
        for cname, cid in raw_class_map.items():
            logger.info(f"  Class {cid} ({cname}): {total_class_counts[cid]} boxes")

    # Execute concurrent downloads
    logger.info(f"\nStarting downloads with {max_workers} worker threads ...")
    session = create_robust_session(pool_size=max_workers * 2)

    status_counts = Counter()
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(download_single_image, task, session): task for task in tasks
        }

        with tqdm(total=total_tasks, desc="Downloading Dataset", unit="img") as pbar:
            for future in as_completed(future_to_task):
                success, status, fname = future.result()
                status_counts[status] += 1
                pbar.update(1)
                pbar.set_postfix({
                    "ok": status_counts["DOWNLOADED"] + status_counts["EXISTS"],
                    "failed": sum(v for k, v in status_counts.items() if k not in ["DOWNLOADED", "EXISTS"]),
                })

    elapsed = time.time() - start_time
    logger.info(f"\nCompleted in {elapsed:.1f}s ({total_tasks / max(1.0, elapsed):.1f} img/s)")
    logger.info("Download Status Summary:")
    for status, count in status_counts.most_common():
        logger.info(f"  {status}: {count}")

    # Generate data.yaml
    logger.info("\nGenerating data.yaml ...")
    val_split_exists = (images_base / "val").is_dir() and any((images_base / "val").iterdir())
    test_split_exists = (images_base / "test").is_dir() and any((images_base / "test").iterdir())

    dataset_path_str = str(datasets_dir.resolve()).replace("\\", "/")

    if mode == "safesync":
        yaml_classes = SAFESYNC_CANONICAL_CLASSES
    else:
        yaml_classes = {idx: name for name, idx in raw_class_map.items()}

    data_yaml_dict = {
        "path": dataset_path_str,
        "train": "images/train",
        "val": "images/val" if val_split_exists else "images/train",
        "nc": len(yaml_classes),
        "names": yaml_classes,
    }
    if test_split_exists:
        data_yaml_dict["test"] = "images/test"

    # Write data.yaml to SafeSync root and datasets/ folder
    root_yaml_path = output_root / "data.yaml"
    datasets_yaml_path = datasets_dir / "data.yaml"

    with open(root_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data_yaml_dict, f, sort_keys=False)

    with open(datasets_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data_yaml_dict, f, sort_keys=False)

    logger.info(f"Generated root data.yaml -> {root_yaml_path}")
    logger.info(f"Generated datasets/ data.yaml -> {datasets_yaml_path}")
    logger.info("Dataset preparation complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Download and format YOLO dataset from Ultralytics .ndjson exports."
    )
    parser.add_argument(
        "--nd-dir",
        type=str,
        default=r"D:\Additional\PROJECT\nd",
        help="Directory containing the .ndjson files.",
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default=r"D:\Additional\PROJECT\SafeSync",
        help="Root SafeSync project directory.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["safesync", "raw"],
        default="safesync",
        help="safesync: 7-class canonical ontology (default); raw: extract all raw classes.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=32,
        help="Number of concurrent worker threads for downloading (default: 32).",
    )
    parser.add_argument(
        "--single-split",
        type=str,
        default=None,
        choices=["train", "val", "test"],
        help="If set, routes all images into this single split (e.g. 'train').",
    )

    args = parser.parse_args()

    process_and_download(
        nd_dir=Path(args.nd_dir),
        output_root=Path(args.output_root),
        mode=args.mode,
        max_workers=args.workers,
        single_split=args.single_split,
    )


if __name__ == "__main__":
    main()
