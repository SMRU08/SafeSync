"""
backend/app/api/p0_analysis.py — SafeSync P0 Recorded Video Analysis API
Provides endpoints to list recorded CCTV videos, monitor analysis status,
stream annotated MP4 videos, and fetch compliance summary telemetry.
"""

import os
import json
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

logger = logging.getLogger("p0_api")
router = APIRouter(prefix="/api/p0", tags=["P0 Recorded Video Analysis"])

INPUT_DIR = r"D:\P0"
OUTPUT_DIR = r"D:\P0\output"
SUPPORTED_EXT = (".mp4", ".avi", ".mov", ".mkv", ".webm")


@router.get("/status")
def get_p0_status() -> Dict[str, Any]:
    """
    Returns full inventory and real status of recorded CCTV videos in D:\\P0,
    including completed annotated videos, summaries, and telemetry.
    """
    if not os.path.isdir(INPUT_DIR):
        return {
            "input_dir": INPUT_DIR,
            "output_dir": OUTPUT_DIR,
            "total_videos": 0,
            "completed_count": 0,
            "videos": [],
        }

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # List all raw video files
    raw_files = [
        f for f in os.listdir(INPUT_DIR)
        if os.path.isfile(os.path.join(INPUT_DIR, f))
        and f.lower().endswith(SUPPORTED_EXT)
        and "_annotated" not in f.lower()
    ]
    raw_files.sort()

    video_items = []
    completed_count = 0

    for f in raw_files:
        fpath = os.path.join(INPUT_DIR, f)
        bname = os.path.splitext(f)[0]
        out_mp4 = os.path.join(OUTPUT_DIR, f"{bname}_annotated.mp4")
        out_sum = os.path.join(OUTPUT_DIR, f"{bname}_summary.json")

        size_mb = round(os.path.getsize(fpath) / (1024 * 1024), 2)
        has_annotated = os.path.isfile(out_mp4) and os.path.getsize(out_mp4) > 1000
        has_summary = os.path.isfile(out_sum)

        summary_data = None
        if has_summary:
            try:
                with open(out_sum, "r", encoding="utf-8") as sf:
                    summary_data = json.load(sf)
            except Exception:
                summary_data = None

        if has_annotated and summary_data and summary_data.get("status") == "COMPLETED":
            item_status = "COMPLETED"
            completed_count += 1
        elif has_annotated:
            item_status = "PROCESSING"
        else:
            item_status = "PENDING"

        video_items.append({
            "name": f,
            "size_mb": size_mb,
            "status": item_status,
            "has_annotated": has_annotated,
            "annotated_name": f"{bname}_annotated.mp4",
            "stream_url": f"/api/p0/stream/{bname}_annotated.mp4" if has_annotated else None,
            "summary": summary_data,
        })

    return {
        "input_dir": INPUT_DIR,
        "output_dir": OUTPUT_DIR,
        "total_videos": len(raw_files),
        "completed_count": completed_count,
        "pending_count": len(raw_files) - completed_count,
        "videos": video_items,
    }


@router.get("/stream/{filename}")
def stream_annotated_video(filename: str):
    """
    Streams the requested annotated MP4 file with byte ranges for HTML5 video playback.
    """
    # Sanitize filename
    clean_name = os.path.basename(filename)
    target_path = os.path.join(OUTPUT_DIR, clean_name)

    if not os.path.isfile(target_path):
        # Check if original was requested without _annotated
        bname = os.path.splitext(clean_name)[0]
        alt_path = os.path.join(OUTPUT_DIR, f"{bname}_annotated.mp4")
        if os.path.isfile(alt_path):
            target_path = alt_path
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Annotated video '{clean_name}' not found in output directory."
            )

    return FileResponse(
        target_path,
        media_type="video/mp4",
        filename=clean_name,
    )


@router.get("/summary/{filename}")
def get_video_summary(filename: str):
    """
    Returns the JSON compliance and detection summary for a specific processed video.
    """
    bname = os.path.splitext(os.path.basename(filename))[0].replace("_annotated", "")
    sum_path = os.path.join(OUTPUT_DIR, f"{bname}_summary.json")

    if not os.path.isfile(sum_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Summary for '{filename}' not found."
        )

    try:
        with open(sum_path, "r", encoding="utf-8") as sf:
            return json.load(sf)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read summary: {e}"
        )
