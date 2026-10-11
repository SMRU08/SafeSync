"""
p0_video_analyzer.py — SafeSync P0 Recorded CCTV Video Analysis Pipeline
Authoritative implementation for processing industrial safety / CCTV footage
using the existing SafeSync production V3 model and compliance pipeline.

Canonical SafeSync Classes:
    0: person
    1: helmet
    2: safety_vest
    3: gloves
    4: safety_footwear
    5: fire
    6: smoke

Features:
- Sequential video processing with clean resource cleanup
- Batched YOLO inference for maximum CPU performance
- Real ByteTrack tracking, Spatial PPE association, and Temporal validation
- Non-punitive UNKNOWN handling (UNKNOWN != ABSENT)
- Independent Fire and Smoke detection overlays with P0 Emergency classification
- High-contrast industrial HUD preserving native video resolution and FPS
- Output verification and per-video JSON summary reports
"""

import os
import sys
import glob
import time
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Callable

import cv2
import numpy as np
import torch

# Ensure SafeSync backend root is accessible
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.ai.detection.model_loader import ModelLoader
from app.ai.detection.detector import Detector
from app.ai.compliance.tracker import ByteTrack
from app.ai.compliance.association import SpatialPPEAssociator
from app.ai.compliance.temporal import TemporalComplianceTracker
from app.ai.compliance.schemas import (
    PPEItemType,
    PPEState,
    OverallComplianceState,
    WorkerTrack,
)

logger = logging.getLogger("p0_video_analyzer")

# Color palette (BGR format for OpenCV)
COLOR_BG_DARK = (20, 16, 10)            # Deep Industrial Navy #0A1014
COLOR_CYAN_ACCENT = (248, 189, 56)       # Bright Sky/Cyan #38BDF8
COLOR_COMPLIANT = (94, 197, 34)          # Emerald Green #22C55E
COLOR_NON_COMPLIANT = (68, 68, 239)      # Rose Red #EF4444
COLOR_UNKNOWN = (11, 158, 245)           # Amber / Yellow #F59E0B
COLOR_WHITE = (255, 255, 255)
COLOR_SLATE_TEXT = (184, 163, 143)       # Slate Gray
COLOR_FIRE = (0, 0, 240)                 # Crimson Red for Flame
COLOR_SMOKE = (0, 140, 255)              # Bright Amber for Smoke

PPE_COLORS = {
    "helmet": (0, 215, 255),             # Gold / Yellow
    "safety_vest": (0, 255, 127),        # Spring Green
    "gloves": (255, 191, 0),             # Cyan
    "safety_footwear": (238, 130, 238),  # Violet
}

PPE_LABELS = {
    "helmet": "HELMET",
    "safety_vest": "SAFETY VEST",
    "gloves": "GLOVES",
    "safety_footwear": "SAFETY FOOTWEAR",
}


def format_timestamp(seconds: float) -> str:
    """Formats seconds into HH:MM:SS or MM:SS string."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def render_p0_frame_overlay(
    frame: np.ndarray,
    video_name: str,
    frame_idx: int,
    total_frames: int,
    fps: float,
    tracked_workers: List[WorkerTrack],
    raw_ppe_detections: List[Dict[str, Any]],
    raw_hazard_detections: List[Dict[str, Any]],
    active_violations_count: int,
) -> np.ndarray:
    """
    Renders high-visibility industrial HUD overlays directly onto the frame:
    1. Top Status Banner (SAFESYNC P0 VIDEO ANALYSIS, Source, Time, Telemetry)
    2. Tracked Worker person bounding boxes in status color (Green=Safe, Red=Violation, Amber=Unknown)
    3. Individual PPE bounding boxes with labels and exact model confidence
    4. Compact Worker PPE status checklist panels (Helmet, Vest, Gloves, Footwear)
    5. Environmental Fire and Smoke detection boxes with confidence and P0 Emergency tags
    """
    out = frame.copy()
    h, w = out.shape[:2]

    # Calculate scale factor for responsive UI at different resolutions (360p, 720p, 1080p)
    scale = max(0.65, min(w / 1280.0, 1.2))
    font_scale = 0.38 * (scale if scale >= 0.8 else 0.85)

    # ─────────────────────────────────────────────────────────────────────────────
    # 1. RENDER TOP STATUS BAR (Section 14, 15, 16)
    # ─────────────────────────────────────────────────────────────────────────────
    fire_count = sum(1 for hz in raw_hazard_detections if hz.get("class_name") == "fire")
    smoke_count = sum(1 for hz in raw_hazard_detections if hz.get("class_name") == "smoke")
    workers_count = len(tracked_workers)
    curr_time_sec = frame_idx / max(1.0, fps)
    time_str = format_timestamp(curr_time_sec)

    is_portrait = (w < 500)
    bar_height = 42 if is_portrait else 34

    header_overlay = out[0:bar_height, 0:w].copy()
    cv2.rectangle(out, (0, 0), (w, bar_height), (12, 16, 26), -1)
    cv2.addWeighted(out[0:bar_height, 0:w], 0.88, header_overlay, 0.12, 0, out[0:bar_height, 0:w])
    cv2.line(out, (0, bar_height), (w, bar_height), (40, 52, 74), 1)

    v_col = COLOR_NON_COMPLIANT if active_violations_count > 0 else COLOR_COMPLIANT
    f_col = COLOR_FIRE if fire_count > 0 else (130, 140, 150)
    s_col = COLOR_SMOKE if smoke_count > 0 else (130, 140, 150)

    if is_portrait:
        # Row 1: Brand (left) & Time (right)
        cv2.putText(
            out, "SAFESYNC | P0 ANALYSIS", (8, 16),
            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 255), 1, cv2.LINE_AA
        )
        t_txt = f"TIME: {time_str}"
        (tw, _), _ = cv2.getTextSize(t_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.36, 1)
        cv2.putText(
            out, t_txt, (w - tw - 8, 16),
            cv2.FONT_HERSHEY_SIMPLEX, 0.36, (220, 225, 230), 1, cv2.LINE_AA
        )
        # Row 2: Telemetry
        cv2.putText(out, f"W:{workers_count}", (8, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (0, 220, 255), 1, cv2.LINE_AA)
        cv2.putText(out, f"VIOL:{active_violations_count}", (60, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.34, v_col, 1, cv2.LINE_AA)
        cv2.putText(out, f"FIRE:{fire_count}", (160, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.34, f_col, 1, cv2.LINE_AA)
        cv2.putText(out, f"SMK:{smoke_count}", (250, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.34, s_col, 1, cv2.LINE_AA)
    else:
        # Landscape: Single clean row
        brand_text = "SAFESYNC | P0 VIDEO ANALYSIS"
        cv2.putText(
            out, brand_text, (10, 22),
            cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 220, 255), 1, cv2.LINE_AA
        )
        clean_vname = video_name[:24] + "..." if len(video_name) > 27 else video_name
        info_text = f"SRC: {clean_vname} | TIME: {time_str}"
        cv2.putText(
            out, info_text, (230, 22),
            cv2.FONT_HERSHEY_SIMPLEX, 0.36, (220, 225, 230), 1, cv2.LINE_AA
        )
        # Telemetry right side
        rx = w - 10
        smk_s = f"SMK:{smoke_count}"
        (sw, _), _ = cv2.getTextSize(smk_s, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
        rx -= (sw + 6)
        cv2.putText(out, smk_s, (rx, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.35, s_col, 1, cv2.LINE_AA)

        fir_s = f"FIRE:{fire_count}"
        (fw, _), _ = cv2.getTextSize(fir_s, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
        rx -= (fw + 8)
        cv2.putText(out, fir_s, (rx, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.35, f_col, 1, cv2.LINE_AA)

        vio_s = f"VIOL:{active_violations_count}"
        (vw, _), _ = cv2.getTextSize(vio_s, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
        rx -= (vw + 8)
        cv2.putText(out, vio_s, (rx, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.35, v_col, 1, cv2.LINE_AA)

        wrk_s = f"WORKERS:{workers_count}"
        (ww, _), _ = cv2.getTextSize(wrk_s, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
        rx -= (ww + 8)
        cv2.putText(out, wrk_s, (rx, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 220, 255), 1, cv2.LINE_AA)

    # ─────────────────────────────────────────────────────────────────────────────
    # 2. RENDER ENVIRONMENTAL HAZARDS (FIRE & SMOKE) (Section 11, 12, 13)
    # ─────────────────────────────────────────────────────────────────────────────
    for hzd in raw_hazard_detections:
        cname = hzd.get("class_name", "hazard").lower()
        conf = float(hzd.get("confidence", 0.0))
        b = hzd.get("bbox", [0, 0, 0, 0])
        bx1, by1, bx2, by2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
        if bx2 <= bx1 or by2 <= by1:
            continue

        hzd_col = COLOR_FIRE if cname == "fire" else COLOR_SMOKE
        cv2.rectangle(out, (bx1, by1), (bx2, by2), hzd_col, 2)

        p0_tag = " [P0 EMERGENCY]" if cname == "fire" and conf >= 0.35 else ""
        lbl = f"{cname.upper()}{p0_tag} {conf:.2f}"
        (lw, lh), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.40, 1)
        lbl_x = max(2, min(bx1, w - lw - 6))
        lbl_y = max(bar_height + lh + 4, by1 - 4)
        cv2.rectangle(out, (lbl_x, lbl_y - lh - 4), (lbl_x + lw + 6, lbl_y + 2), (0, 0, 0), -1)
        cv2.rectangle(out, (lbl_x, lbl_y - lh - 4), (lbl_x + lw + 6, lbl_y + 2), hzd_col, 1)
        cv2.putText(out, lbl, (lbl_x + 3, lbl_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.40, COLOR_WHITE, 1, cv2.LINE_AA)

    # ─────────────────────────────────────────────────────────────────────────────
    # 3. RENDER INDIVIDUAL PPE BOUNDING BOXES (Section 7)
    # ─────────────────────────────────────────────────────────────────────────────
    for ppe in raw_ppe_detections:
        cname = ppe.get("class_name", "").lower()
        conf = float(ppe.get("confidence", 0.0))
        b = ppe.get("bbox", [0, 0, 0, 0])
        px1, py1, px2, py2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
        if px2 <= px1 or py2 <= py1:
            continue

        item_color = PPE_COLORS.get(cname, (200, 200, 200))
        item_tag = PPE_LABELS.get(cname, cname.upper())

        # Draw PPE box with thickness 2
        cv2.rectangle(out, (px1, py1), (px2, py2), item_color, 2)

        # Label pill: e.g. "HELMET 0.91"
        lbl = f"{item_tag} {conf:.2f}"
        (lw, lh), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
        lbl_x = max(2, min(px1, w - lw - 4))
        lbl_y = max(bar_height + lh + 4, py1 - 3)
        cv2.rectangle(out, (lbl_x, lbl_y - lh - 3), (lbl_x + lw + 4, lbl_y + 2), item_color, -1)
        cv2.putText(out, lbl, (lbl_x + 2, lbl_y - 1), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1, cv2.LINE_AA)

    # ─────────────────────────────────────────────────────────────────────────────
    # 4. RENDER TRACKED WORKERS & PPE CHECKLIST PANELS (Section 6, 8, 9, 10)
    # ─────────────────────────────────────────────────────────────────────────────
    for worker in tracked_workers:
        wb = worker.bbox
        x1, y1, x2, y2 = int(wb.x1), int(wb.y1), int(wb.x2), int(wb.y2)
        if x2 <= x1 or y2 <= y1:
            continue

        # Map compliance state to visual styling (Section 8, 9, 10)
        # Priority: NON_COMPLIANT (Red) > UNKNOWN (Amber) > COMPLIANT (Green)
        st = worker.overall_status
        if st == OverallComplianceState.NON_COMPLIANT:
            badge_color = COLOR_NON_COMPLIANT
            status_tag = "CONFIRMED VIOLATION"
            box_thick = 3
        elif st == OverallComplianceState.UNKNOWN:
            badge_color = COLOR_UNKNOWN
            status_tag = "UNKNOWN"
            box_thick = 2
        else:
            badge_color = COLOR_COMPLIANT
            status_tag = "SAFE"
            box_thick = 2

        # Draw Person Bounding Box
        cv2.rectangle(out, (x1, y1), (x2, y2), badge_color, box_thick)

        # Header tag on box: "Worker #01 [SAFE]"
        tag_str = f"Worker #{worker.track_id:02d} [{status_tag}]"
        (tw, th), _ = cv2.getTextSize(tag_str, cv2.FONT_HERSHEY_SIMPLEX, 0.38, 1)
        tag_y = max(bar_height + th + 4, y1 - 4)
        cv2.rectangle(out, (x1, tag_y - th - 4), (x1 + tw + 6, tag_y + 2), (10, 10, 15), -1)
        cv2.rectangle(out, (x1, tag_y - th - 4), (x1 + tw + 6, tag_y + 2), badge_color, 1)
        cv2.putText(out, tag_str, (x1 + 3, tag_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.38, badge_color, 1, cv2.LINE_AA)

        # ── Compact Worker Status Panel (Section 8, 9, 10) ───────────────────
        # Display 4-point PPE state: Helmet, Vest, Gloves, Footwear
        # Semantic: PRESENT = Safe (Green), ABSENT = Violation (Red), UNKNOWN = Pending/Insufficient (Amber)
        ppe_states = worker.ppe or {}
        items = [
            ("H", ppe_states.get("helmet", PPEState.UNKNOWN)),
            ("V", ppe_states.get("safety_vest", PPEState.UNKNOWN)),
            ("G", ppe_states.get("gloves", PPEState.UNKNOWN)),
            ("F", ppe_states.get("safety_footwear", PPEState.UNKNOWN)),
        ]

        hud_w = 160
        hud_h = 32
        hud_x1 = max(4, min(x1, w - hud_w - 4))
        hud_x2 = hud_x1 + hud_w

        # Position status card to avoid occluding face/helmet:
        # Prefer below feet (y2 + 2) if it fits inside frame
        # Otherwise, prefer above head (y1 - hud_h - 4) if above top bar
        # Otherwise, place inside at bottom near feet/ground
        if y2 + hud_h + 2 <= h:
            hud_y1 = y2 + 2
        elif y1 - hud_h - (th + 6) >= bar_height:
            hud_y1 = y1 - hud_h - (th + 6)
        else:
            hud_y1 = max(bar_height + 2, y2 - hud_h - 4)
        hud_y2 = hud_y1 + hud_h

        if hud_y2 <= h and hud_x2 <= w and hud_y1 >= bar_height:
            hud_bg = out[hud_y1:hud_y2, hud_x1:hud_x2].copy()
            cv2.rectangle(out, (hud_x1, hud_y1), (hud_x2, hud_y2), (12, 16, 26), -1)
            cv2.addWeighted(out[hud_y1:hud_y2, hud_x1:hud_x2], 0.82, hud_bg, 0.18, 0, out[hud_y1:hud_y2, hud_x1:hud_x2])
            cv2.rectangle(out, (hud_x1, hud_y1), (hud_x2, hud_y2), badge_color, 1)

            def get_state_info(item_state):
                s = getattr(item_state, "value", str(item_state)).upper()
                if s == "PRESENT":
                    return "PRESENT", COLOR_COMPLIANT
                elif s == "ABSENT":
                    return "ABSENT", COLOR_NON_COMPLIANT
                return "UNKNOWN", COLOR_UNKNOWN

            h_lbl, h_col = get_state_info(items[0][1])
            v_lbl, v_col = get_state_info(items[1][1])
            cv2.putText(out, f"H:{h_lbl}", (hud_x1 + 4, hud_y1 + 13), cv2.FONT_HERSHEY_SIMPLEX, 0.30, h_col, 1, cv2.LINE_AA)
            cv2.putText(out, f"V:{v_lbl}", (hud_x1 + 82, hud_y1 + 13), cv2.FONT_HERSHEY_SIMPLEX, 0.30, v_col, 1, cv2.LINE_AA)

            g_lbl, g_col = get_state_info(items[2][1])
            f_lbl, f_col = get_state_info(items[3][1])
            cv2.putText(out, f"G:{g_lbl}", (hud_x1 + 4, hud_y1 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.30, g_col, 1, cv2.LINE_AA)
            cv2.putText(out, f"F:{f_lbl}", (hud_x1 + 82, hud_y1 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.30, f_col, 1, cv2.LINE_AA)

    return out


class P0VideoAnalyzer:
    """
    Production batch processor for recorded CCTV and industrial safety videos.
    Reuses existing SafeSync production V3 model, ByteTrack tracking, PPE association,
    and temporal compliance validation.
    """

    SUPPORTED_EXTENSIONS = (".mp4", ".avi", ".mov", ".mkv", ".webm")

    def __init__(self, batch_size: int = 8):
        self.batch_size = batch_size
        logger.info("Initializing P0VideoAnalyzer with production V3 model...")
        self.model_loader = ModelLoader.get_instance()
        self.model = self.model_loader.model
        self.classes = self.model_loader.model.names
        logger.info("Loaded YOLO model classes (%d): %s", len(self.classes), self.classes)

    def scan_videos(self, input_dir: str) -> List[str]:
        """Scans input directory for supported videos, excluding output directory."""
        if not os.path.isdir(input_dir):
            logger.error("Input directory does not exist: %s", input_dir)
            return []

        out_canonical = os.path.abspath(os.path.join(input_dir, "output"))
        candidates = []

        for item in os.listdir(input_dir):
            full_path = os.path.join(input_dir, item)
            if not os.path.isfile(full_path):
                continue
            if item.lower().endswith(self.SUPPORTED_EXTENSIONS):
                # Ignore previously generated *_annotated videos
                if "_annotated" in item.lower():
                    continue
                # Ensure not inside output folder
                if os.path.abspath(full_path).startswith(out_canonical):
                    continue
                candidates.append(full_path)

        candidates.sort()
        return candidates

    def process_video(
        self,
        video_path: str,
        output_dir: str,
        progress_callback: Optional[Callable[[int, int, float, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end frame-by-frame inference on a single video file.
        Produces <video_name>_annotated.mp4 and <video_name>_summary.json.
        """
        t_start = time.perf_counter()
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_mp4_path = os.path.join(output_dir, f"{base_name}_annotated.mp4")
        summary_json_path = os.path.join(output_dir, f"{base_name}_summary.json")

        os.makedirs(output_dir, exist_ok=True)

        logger.info("Starting processing: %s -> %s", os.path.basename(video_path), os.path.basename(output_mp4_path))

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            err_msg = f"Failed to open video file: {video_path}"
            logger.error(err_msg)
            return {
                "video_name": os.path.basename(video_path),
                "status": "FAILED",
                "error": err_msg,
            }

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        input_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if width <= 0 or height <= 0 or total_frames <= 0:
            cap.release()
            err_msg = f"Invalid video dimensions or frame count: {width}x{height}, {total_frames} frames"
            logger.error(err_msg)
            return {
                "video_name": os.path.basename(video_path),
                "status": "FAILED",
                "error": err_msg,
            }

        # Initialize VideoWriter using standard mp4v codec
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_mp4_path, fourcc, input_fps, (width, height))
        if not writer.isOpened():
            cap.release()
            err_msg = f"Failed to initialize VideoWriter for: {output_mp4_path}"
            logger.error(err_msg)
            return {
                "video_name": os.path.basename(video_path),
                "status": "FAILED",
                "error": err_msg,
            }

        # Initialize sequential tracking and compliance state machines
        tracker = ByteTrack(
            track_high_thresh=0.20,
            track_low_thresh=0.08,
            new_track_thresh=0.22,
            track_buffer=30,
            match_thresh=0.70,
            confirmation_frames=2,
            lost_tolerance_frames=20,
        )
        associator = SpatialPPEAssociator()
        temporal_tracker = TemporalComplianceTracker()

        # Telemetry aggregators
        frames_processed = 0
        metrics_acc = {
            "persons": 0,
            "helmets": 0,
            "vests": 0,
            "gloves": 0,
            "footwear": 0,
            "fire": 0,
            "smoke": 0,
            "violations": 0,
            "unknowns": 0,
        }

        frame_buffer: List[np.ndarray] = []

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    # End of stream or broken frame
                    break

                frames_processed += 1
                frame_buffer.append(frame)

                # Execute batched inference when buffer fills or video ends
                if len(frame_buffer) >= self.batch_size:
                    self._process_frame_batch(
                        frame_buffer=frame_buffer,
                        start_frame_idx=frames_processed - len(frame_buffer) + 1,
                        total_frames=total_frames,
                        fps=input_fps,
                        video_name=base_name,
                        tracker=tracker,
                        associator=associator,
                        temporal_tracker=temporal_tracker,
                        writer=writer,
                        metrics_acc=metrics_acc,
                    )
                    frame_buffer.clear()

                    if progress_callback:
                        progress_callback(frames_processed, total_frames, input_fps, base_name)

            # Process any remaining frames in trailing buffer
            if len(frame_buffer) > 0:
                self._process_frame_batch(
                    frame_buffer=frame_buffer,
                    start_frame_idx=frames_processed - len(frame_buffer) + 1,
                    total_frames=total_frames,
                    fps=input_fps,
                    video_name=base_name,
                    tracker=tracker,
                    associator=associator,
                    temporal_tracker=temporal_tracker,
                    writer=writer,
                    metrics_acc=metrics_acc,
                )
                frame_buffer.clear()

        finally:
            cap.release()
            writer.release()

        duration_sec = frames_processed / max(1.0, input_fps)
        total_time_sec = time.perf_counter() - t_start

        # Validate generated video output
        output_valid = os.path.isfile(output_mp4_path) and os.path.getsize(output_mp4_path) > 1000
        check_cap = cv2.VideoCapture(output_mp4_path)
        written_frames = int(check_cap.get(cv2.CAP_PROP_FRAME_COUNT)) if check_cap.isOpened() else 0
        check_cap.release()

        summary_data = {
            "video_name": os.path.basename(video_path),
            "input_path": video_path,
            "output_path": output_mp4_path,
            "duration": round(duration_sec, 2),
            "fps": round(input_fps, 2),
            "resolution": f"{width}x{height}",
            "frames_processed": frames_processed,
            "output_frames_verified": written_frames,
            "persons_detected": metrics_acc["persons"],
            "helmet_detections": metrics_acc["helmets"],
            "vest_detections": metrics_acc["vests"],
            "glove_detections": metrics_acc["gloves"],
            "footwear_detections": metrics_acc["footwear"],
            "fire_detections": metrics_acc["fire"],
            "smoke_detections": metrics_acc["smoke"],
            "confirmed_ppe_violations": metrics_acc["violations"],
            "unknown_states": metrics_acc["unknowns"],
            "processing_time": round(total_time_sec, 2),
            "effective_processing_fps": round(frames_processed / max(0.1, total_time_sec), 2),
            "status": "COMPLETED" if output_valid and written_frames > 0 else "FAILED",
        }

        # Write summary JSON
        with open(summary_json_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)

        logger.info(
            "Completed %s: %d frames processed in %.1fs (%.1f fps) -> %s",
            os.path.basename(video_path), frames_processed, total_time_sec,
            summary_data["effective_processing_fps"], os.path.basename(output_mp4_path)
        )
        return summary_data

    def _process_frame_batch(
        self,
        frame_buffer: List[np.ndarray],
        start_frame_idx: int,
        total_frames: int,
        fps: float,
        video_name: str,
        tracker: ByteTrack,
        associator: SpatialPPEAssociator,
        temporal_tracker: TemporalComplianceTracker,
        writer: cv2.VideoWriter,
        metrics_acc: Dict[str, int],
    ):
        """Batched GPU/CPU vector inference + sequential tracking/overlay rendering."""
        # Run batched YOLO prediction (leveraging OpenMP SIMD speedup)
        results = self.model.predict(
            source=frame_buffer,
            imgsz=384,
            conf=0.20,
            iou=0.45,
            verbose=False,
        )

        for i, (frame, res) in enumerate(zip(frame_buffer, results)):
            f_idx = start_frame_idx + i
            temporal_tracker.current_frame = f_idx

            person_dets = []
            ppe_dets = []
            hazard_dets = []

            if res.boxes is not None and len(res.boxes) > 0:
                for b_item in res.boxes:
                    cls_id = int(b_item.cls[0].item())
                    cname = self.classes.get(cls_id, f"class_{cls_id}").lower()
                    conf = float(b_item.conf[0].item())
                    coords = b_item.xyxy[0].tolist()

                    if cname == "person":
                        bw = max(0.0, coords[2] - coords[0])
                        bh = max(0.0, coords[3] - coords[1])
                        if (bw * bh) >= 200:
                            person_dets.append([coords[0], coords[1], coords[2], coords[3], conf])
                            metrics_acc["persons"] += 1
                    elif cname in ("helmet", "safety_vest", "gloves", "safety_footwear"):
                        ppe_dets.append({
                            "class_name": cname,
                            "bbox": coords,
                            "confidence": round(conf, 4),
                        })
                        if cname == "helmet": metrics_acc["helmets"] += 1
                        elif cname == "safety_vest": metrics_acc["vests"] += 1
                        elif cname == "gloves": metrics_acc["gloves"] += 1
                        elif cname == "safety_footwear": metrics_acc["footwear"] += 1
                    elif cname in ("fire", "smoke"):
                        hazard_dets.append({
                            "class_name": cname,
                            "bbox": coords,
                            "confidence": round(conf, 4),
                        })
                        if cname == "fire": metrics_acc["fire"] += 1
                        elif cname == "smoke": metrics_acc["smoke"] += 1

            # 1. ByteTrack Person Tracking
            person_arr = np.array(person_dets) if person_dets else np.empty((0, 5))
            tracked_workers_raw = tracker.update(person_arr)

            # 2. Spatial PPE Association
            img_shape = frame.shape[:2]
            associations, unassociated_ppe = associator.associate(
                tracked_workers_raw, ppe_dets, img_shape=img_shape, frame=frame
            )

            # 3. Temporal Compliance State Machine
            worker_tracks: List[WorkerTrack] = []
            worker_boxes = [wb for _, wb, _ in tracked_workers_raw]

            for w_idx, (tid, wb, wconf) in enumerate(tracked_workers_raw):
                occl_flags = {}
                for item_t in PPEItemType:
                    occl_flags[item_t] = associator.detect_occlusion(
                        w_idx, worker_boxes, item_t, img_shape
                    )

                w_obj = temporal_tracker.update_worker(
                    track_id=tid,
                    worker_bbox=wb,
                    confidence=wconf,
                    associations=associations.get(tid, {}),
                    is_occluded_flags=occl_flags,
                )
                worker_tracks.append(w_obj)

                if w_obj.overall_status == OverallComplianceState.NON_COMPLIANT:
                    metrics_acc["violations"] += 1
                elif w_obj.overall_status == OverallComplianceState.UNKNOWN:
                    metrics_acc["unknowns"] += 1

            temporal_tracker.prune_stale_tracks()

            active_viols = sum(
                1 for w in worker_tracks if w.overall_status == OverallComplianceState.NON_COMPLIANT
            )

            # 4. Render Non-Obstructive Industrial HUD Overlay
            annotated_frame = render_p0_frame_overlay(
                frame=frame,
                video_name=video_name,
                frame_idx=f_idx,
                total_frames=total_frames,
                fps=fps,
                tracked_workers=worker_tracks,
                raw_ppe_detections=ppe_dets,
                raw_hazard_detections=hazard_dets,
                active_violations_count=active_viols,
            )

            # 5. Write to output video
            writer.write(annotated_frame)
