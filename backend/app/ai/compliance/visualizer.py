"""
visualizer.py — SafeSync Phase 5
Non-destructive visualization of tracked workers, spatial PPE checklist HUD,
and overall compliance status badges.
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Optional

try:
    from app.ai.compliance.schemas import (
        WorkerTrack,
        PPEState,
        OverallComplianceState,
    )
except ImportError:
    from backend.app.ai.compliance.schemas import (
        WorkerTrack,
        PPEState,
        OverallComplianceState,
    )

# Colors in BGR
COLOR_WORKER_BOX = (255, 200, 0)      # Bright Amber
COLOR_COMPLIANT = (50, 205, 50)       # Lime Green
COLOR_NON_COMPLIANT = (60, 60, 220)   # Crimson Red
COLOR_UNKNOWN = (0, 215, 255)         # Warm Yellow / Orange

# PPE checklist state markers
MARKERS = {
    PPEState.PRESENT: ("[+]", (50, 205, 50)),     # Green check
    PPEState.ABSENT: ("[-]", (60, 60, 220)),      # Red cross
    PPEState.UNKNOWN: ("[?]", (0, 215, 255)),     # Yellow question mark
}


class ComplianceVisualizer:
    """
    Renders worker bounding boxes, track IDs, and PPE compliance checklist cards.
    """

    def __init__(self, show_hud: bool = True):
        self.show_hud = show_hud

    def draw_frame(
        self,
        image: np.ndarray,
        workers: List[WorkerTrack],
        unassociated_ppe: Optional[List[Dict[str, Any]]] = None,
        hazards: Optional[List[Dict[str, Any]]] = None,
    ) -> np.ndarray:
        """
        Renders worker tracking and compliance HUD onto a copy of the input image.
        """
        out = image.copy()

        # 1. Render environmental hazards (fire, smoke) if present (clean pass-through)
        if hazards:
            for h in hazards:
                b = h.get("bbox", [0, 0, 0, 0])
                cname = h.get("class_name", "hazard")
                conf = h.get("confidence", 0.0)
                color = (0, 0, 255) if cname == "fire" else (128, 128, 128)
                cv2.rectangle(out, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), color, 2)
                lbl = f"{cname.upper()} {conf:.2f}"
                cv2.putText(
                    out, lbl, (int(b[0]), max(15, int(b[1]) - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA
                )

        # 2. Render unassociated PPE in thin dashed/gray boxes
        if unassociated_ppe:
            for ppe in unassociated_ppe:
                b = ppe.get("bbox", [0, 0, 0, 0])
                cname = ppe.get("class_name", "ppe")
                cv2.rectangle(out, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (180, 180, 180), 1)

        # 3. Render tracked workers
        for worker in workers:
            wb = worker.bbox
            x1, y1, x2, y2 = wb.x1, wb.y1, wb.x2, wb.y2

            # Determine badge color by overall status
            if worker.overall_status == OverallComplianceState.COMPLIANT:
                badge_color = COLOR_COMPLIANT
            elif worker.overall_status == OverallComplianceState.NON_COMPLIANT:
                badge_color = COLOR_NON_COMPLIANT
            else:
                badge_color = COLOR_UNKNOWN

            # Draw worker person box
            cv2.rectangle(out, (x1, y1), (x2, y2), COLOR_WORKER_BOX, 2)

            if not self.show_hud:
                # Simple track label only
                lbl = f"Worker #{worker.track_id}"
                cv2.putText(out, lbl, (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, badge_color, 2)
                continue

            # ─── Render Information Card (HUD) ───
            header_text = f"Worker #{worker.track_id} [{worker.overall_status.value}]"
            h_text, _ = MARKERS.get(worker.ppe.get("helmet", PPEState.UNKNOWN), ("[?]", COLOR_UNKNOWN))
            v_text, _ = MARKERS.get(worker.ppe.get("safety_vest", PPEState.UNKNOWN), ("[?]", COLOR_UNKNOWN))
            g_text, _ = MARKERS.get(worker.ppe.get("gloves", PPEState.UNKNOWN), ("[?]", COLOR_UNKNOWN))
            f_text, _ = MARKERS.get(worker.ppe.get("safety_footwear", PPEState.UNKNOWN), ("[?]", COLOR_UNKNOWN))

            line1 = header_text
            line2 = f"H:{h_text} V:{v_text} G:{g_text} F:{f_text}"

            # Calculate HUD background dimensions
            card_w = max(190, max(len(line1), len(line2)) * 8 + 10)
            card_h = 42

            # Place card above worker box if space permits, otherwise inside/below
            card_y1 = y1 - card_h - 4
            if card_y1 < 5:
                card_y1 = y1 + 4

            card_x1 = max(5, x1)
            card_x2 = min(out.shape[1] - 5, card_x1 + card_w)
            card_y2 = card_y1 + card_h

            # Draw semi-transparent dark HUD card background
            sub_img = out[card_y1:card_y2, card_x1:card_x2]
            if sub_img.shape[0] > 0 and sub_img.shape[1] > 0:
                black_rect = np.zeros_like(sub_img)
                res = cv2.addWeighted(sub_img, 0.25, black_rect, 0.75, 0)
                out[card_y1:card_y2, card_x1:card_x2] = res

            # Card border with status color
            cv2.rectangle(out, (card_x1, card_y1), (card_x2, card_y2), badge_color, 1)

            # Draw Line 1 (Header)
            cv2.putText(
                out, line1, (card_x1 + 6, card_y1 + 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, badge_color, 1, cv2.LINE_AA
            )

            # Draw Line 2 (Checklist)
            # Custom render checklist with item-specific colors
            cursor_x = card_x1 + 6
            y_pos = card_y1 + 34
            items_to_draw = [
                ("H:", worker.ppe.get("helmet", PPEState.UNKNOWN)),
                ("V:", worker.ppe.get("safety_vest", PPEState.UNKNOWN)),
                ("G:", worker.ppe.get("gloves", PPEState.UNKNOWN)),
                ("F:", worker.ppe.get("safety_footwear", PPEState.UNKNOWN)),
            ]
            for prefix, state in items_to_draw:
                symbol, sym_col = MARKERS[state]
                txt = f"{prefix}{symbol} "
                cv2.putText(out, txt, (cursor_x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.38, sym_col, 1, cv2.LINE_AA)
                cursor_x += len(txt) * 7 + 2

        return out
