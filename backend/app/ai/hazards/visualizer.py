"""
visualizer.py — SafeSync Phase 6
Visualizer for Fire and Smoke Hazards with State Badges and Camera/Zone Metadata.
Strictly decoupled from risk scoring (no CRITICAL/HIGH/MEDIUM/LOW).
"""

import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict, Any

try:
    from app.ai.hazards.schemas import HazardState, HazardType, HazardEventDetail
except ImportError:
    from backend.app.ai.hazards.schemas import HazardState, HazardType, HazardEventDetail


# High-visibility BGR color palettes
COLOR_FIRE = (0, 69, 255)      # Bright Orange-Red for Fire
COLOR_SMOKE = (169, 169, 169)  # Slate Gray for Smoke

STATE_COLORS = {
    HazardState.CONFIRMED: (0, 0, 230),     # Vivid Red
    HazardState.ACTIVE: (0, 0, 255),        # Bright Red
    HazardState.DETECTING: (0, 140, 255),   # Orange
    HazardState.CANDIDATE: (0, 215, 255),   # Amber/Yellow
    HazardState.CLEARING: (160, 160, 160),  # Muted Gray
    HazardState.CLEARED: (100, 100, 100),   # Dark Muted Gray
    HazardState.NO_HAZARD: (0, 200, 0),     # Green
}


class HazardVisualizer:
    """
    Renders non-destructive bounding boxes, HUD status badges, and scene banners.
    Displays clear visual distinction between candidate/detecting and confirmed hazards.
    """

    def __init__(self, show_hud: bool = True):
        self.show_hud = show_hud

    def draw_hazards(
        self,
        frame: np.ndarray,
        hazard_events: List[HazardEventDetail],
        scene_state: HazardState,
        camera_name: str = "Camera 01",
        zone_name: str = "UNKNOWN",
        relationship: str = "NO_HAZARD",
        fps: Optional[float] = None,
        latency_ms: Optional[float] = None,
    ) -> np.ndarray:
        """
        Draws active hazard bounding boxes, tracking IDs, state labels, and camera/zone HUD.
        """
        canvas = frame.copy()
        h, w = canvas.shape[:2]

        # 1. Top HUD Banner
        if self.show_hud:
            banner_h = 36
            overlay = canvas.copy()
            cv2.rectangle(overlay, (0, 0), (w, banner_h), (20, 20, 20), -1)
            cv2.addWeighted(overlay, 0.75, canvas, 0.25, 0, canvas)

            # Title
            title_text = f"SafeSync — HAZARD MONITOR | {camera_name} ({zone_name})"
            cv2.putText(
                canvas, title_text, (12, 23),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 240, 240), 1, cv2.LINE_AA
            )

            # Scene State Badge
            state_color = STATE_COLORS.get(scene_state, (200, 200, 200))
            badge_text = f"SCENE: {scene_state.value} [{relationship}]"
            t_size = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.50, 1)[0]
            badge_x = w - t_size[0] - 16
            cv2.rectangle(canvas, (badge_x - 6, 6), (w - 10, 30), state_color, -1)
            cv2.putText(
                canvas, badge_text, (badge_x, 23),
                cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1, cv2.LINE_AA
            )

        # 2. Draw each hazard event
        for ev in hazard_events:
            if ev.state in (HazardState.CLEARED, HazardState.NO_HAZARD):
                continue

            base_color = COLOR_FIRE if ev.hazard_type == HazardType.FIRE else COLOR_SMOKE
            st_color = STATE_COLORS.get(ev.state, base_color)

            x1 = max(0, min(int(round(ev.bbox.x1)), w - 1))
            y1 = max(0, min(int(round(ev.bbox.y1)), h - 1))
            x2 = max(0, min(int(round(ev.bbox.x2)), w - 1))
            y2 = max(0, min(int(round(ev.bbox.y2)), h - 1))

            # Bounding box thickness based on state: bold for confirmed/active, thin for candidate
            if ev.state in (HazardState.CONFIRMED, HazardState.ACTIVE):
                thickness = 3
            elif ev.state == HazardState.DETECTING:
                thickness = 2
            else:
                thickness = 1

            cv2.rectangle(canvas, (x1, y1), (x2, y2), st_color, thickness)

            # Header Badge with state explanation
            state_prefix = ""
            if ev.state == HazardState.CANDIDATE:
                state_prefix = " [CANDIDATE - EVAL]"
            elif ev.state == HazardState.DETECTING:
                state_prefix = " [DETECTING - CONFIRMING]"
            elif ev.state in (HazardState.CONFIRMED, HazardState.ACTIVE):
                state_prefix = " [CONFIRMED]"
            elif ev.state == HazardState.CLEARING:
                state_prefix = " [CLEARING]"

            label = (
                f"{ev.event_id} {ev.hazard_type.value.upper()} {ev.confidence:.2f}"
                f"{state_prefix} | Zone: {ev.zone_id}"
            )
            font_scale = 0.42
            font_thickness = 1
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)[0]
            tag_w = text_size[0] + 10
            tag_h = text_size[1] + 8

            tag_y1 = max(0, y1 - tag_h)
            tag_y2 = y1 if y1 >= tag_h else tag_h
            tag_x2 = min(w - 1, x1 + tag_w)

            # Background badge
            cv2.rectangle(canvas, (x1, tag_y1), (tag_x2, tag_y2), (25, 25, 25), -1)
            cv2.rectangle(canvas, (x1, tag_y1), (tag_x2, tag_y2), st_color, 1)

            # Text
            text_pos = (x1 + 5, tag_y2 - 5)
            cv2.putText(
                canvas, label, text_pos,
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA
            )

        # 3. Bottom Performance Overlay (FPS & Latency)
        if fps is not None or latency_ms is not None:
            perf_text = ""
            if fps is not None:
                perf_text += f"FPS: {fps:.1f}  "
            if latency_ms is not None:
                perf_text += f"Latency: {latency_ms:.1f} ms"

            if perf_text:
                cv2.putText(
                    canvas, perf_text, (12, h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA
                )

        return canvas
