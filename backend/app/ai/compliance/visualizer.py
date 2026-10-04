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
COLOR_WORKER_BOX = (255, 200, 0)      # Bright Amber (legacy; person box now uses status color)
COLOR_COMPLIANT = (94, 197, 34)       # #22C55E  Green  — SAFE / COMPLIANT
COLOR_NON_COMPLIANT = (68, 68, 239)   # #EF4444  Red    — CONFIRMED VIOLATION
COLOR_UNKNOWN = (11, 158, 245)        # #F59E0B  Amber  — UNKNOWN / VISIBILITY LIMITED

# PPE checklist state markers
MARKERS = {
    PPEState.PRESENT: ("[+]", COLOR_COMPLIANT),      # Green check
    PPEState.ABSENT: ("[-]", COLOR_NON_COMPLIANT),   # Red cross
    PPEState.UNKNOWN: ("[?]", COLOR_UNKNOWN),        # Amber question mark
}

PPE_DISPLAY_NAMES = {
    "helmet": "Helmet",
    "safety_vest": "Vest",
    "gloves": "Gloves",
    "safety_footwear": "Footwear",
}

# Display states (visual only — derived from the validated overall_status)
DISPLAY_SAFE = "SAFE"
DISPLAY_UNKNOWN = "UNKNOWN"
DISPLAY_VIOLATION = "VIOLATION"


def _state_value(state: Any) -> str:
    return str(getattr(state, "value", state)).upper()


def resolve_worker_display(worker: WorkerTrack) -> Dict[str, Any]:
    """
    Maps a worker's FINAL, temporally-validated compliance state to box display data.

    This is a pure visualization mapping. It never re-derives compliance from raw
    detections. The authoritative input is ``worker.overall_status``, which the
    TemporalComplianceTracker computes with priority ABSENT > UNKNOWN > PRESENT
    (after the configured missing-detection tolerance).

    Priority:
        NON_COMPLIANT  -> RED    "CONFIRMED VIOLATION"  (+ missing items)
        UNKNOWN        -> AMBER  "UNKNOWN"              (+ limited-visibility items)
        COMPLIANT      -> GREEN  "SAFE"
    UNKNOWN is never mapped to RED.
    """
    status = worker.overall_status
    ppe = worker.ppe or {}

    absent = [PPE_DISPLAY_NAMES[k] for k in PPE_DISPLAY_NAMES if _state_value(ppe.get(k, "UNKNOWN")) == "ABSENT"]
    unknown = [PPE_DISPLAY_NAMES[k] for k in PPE_DISPLAY_NAMES if _state_value(ppe.get(k, "UNKNOWN")) == "UNKNOWN"]

    # Priority 1: CONFIRMED VIOLATION / ABSENT -> RED
    if status == OverallComplianceState.NON_COMPLIANT or len(absent) > 0:
        return {
            "display_state": DISPLAY_VIOLATION,
            "color": COLOR_NON_COMPLIANT,
            "label": "CONFIRMED VIOLATION",
            "detail": f"Missing: {', '.join(absent)}" if absent else "",
            "missing_items": absent,
            "unknown_items": unknown,
        }

    # Priority 2: ANY PPE = UNKNOWN (or worker overall_status is UNKNOWN) -> AMBER / YELLOW
    if status == OverallComplianceState.UNKNOWN or len(unknown) > 0:
        return {
            "display_state": DISPLAY_UNKNOWN,
            "color": COLOR_UNKNOWN,
            "label": "UNKNOWN",
            "detail": f"{', '.join(unknown)} visibility limited" if unknown else "Visibility limited",
            "missing_items": [],
            "unknown_items": unknown,
        }

    # Priority 3: ALL required PPE = PRESENT -> GREEN
    return {
        "display_state": DISPLAY_SAFE,
        "color": COLOR_COMPLIANT,
        "label": "SAFE",
        "detail": "",
        "missing_items": [],
        "unknown_items": [],
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

        # 1. Render environmental hazards (fire, smoke) if present (clean pass-through and validated tracks)
        if hazards:
            for h in hazards:
                if isinstance(h, dict):
                    b = h.get("bbox", [0, 0, 0, 0])
                    cname = str(h.get("class_name", "hazard")).lower()
                    conf = float(h.get("confidence", 0.0))
                    state = str(h.get("state", "")).upper()
                else:
                    # HazardEventDetail or duck-typed hazard object
                    raw_b = getattr(h, "bbox", None)
                    if hasattr(raw_b, "x1"):
                        b = [raw_b.x1, raw_b.y1, raw_b.x2, raw_b.y2]
                    elif isinstance(raw_b, (list, tuple)):
                        b = raw_b
                    else:
                        b = [0, 0, 0, 0]
                    htype = getattr(h, "hazard_type", "hazard")
                    cname = htype.value.lower() if hasattr(htype, "value") else str(htype).lower()
                    conf = float(getattr(h, "confidence", 0.0))
                    hstate = getattr(h, "state", "")
                    state = hstate.value.upper() if hasattr(hstate, "value") else str(hstate).upper()

                # State gate: only render confirmed or high-confidence hazards
                # Candidate/Detecting states must NOT appear on the live HUD
                SHOW_STATES = {"CONFIRMED", "ACTIVE"}
                if state not in SHOW_STATES and conf < 0.35:
                    continue

                # Distinct high-contrast colors: Fire=Crimson Red, Smoke=Bright Amber
                color = (0, 0, 240) if cname == "fire" else (0, 140, 255)
                bx1, by1, bx2, by2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
                cv2.rectangle(out, (bx1, by1), (bx2, by2), color, 3)

                state_str = f" [{state}]" if state and state not in ("NO_HAZARD", "") else ""
                lbl = f"{cname.upper()}{state_str} {conf:.2f}"

                # Render background badge pill for label legibility
                (lw, lh), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                lbl_y1 = max(0, by1 - lh - 6)
                lbl_y2 = by1
                cv2.rectangle(out, (bx1, lbl_y1), (bx1 + lw + 6, lbl_y2), (0, 0, 0), -1)
                cv2.rectangle(out, (bx1, lbl_y1), (bx1 + lw + 6, lbl_y2), color, 1)
                cv2.putText(
                    out, lbl, (bx1 + 3, lbl_y2 - 3),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA
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

            # Resolve display from the FINAL validated worker state (never raw detections)
            display = resolve_worker_display(worker)
            badge_color = display["color"]
            box_thickness = 3 if display["display_state"] == DISPLAY_VIOLATION else 2

            # Draw COMPLETE worker person box in the worker's own status color
            cv2.rectangle(out, (x1, y1), (x2, y2), badge_color, box_thickness)

            if not self.show_hud:
                # Simple track label only
                lbl = f"Worker #{worker.track_id} {display['label']}"
                cv2.putText(out, lbl, (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, badge_color, 2)
                continue

            # ─── Render Information Card (HUD) ───
            header_text = f"Worker #{worker.track_id} {display['label']}"
            detail_text = display["detail"]
            h_text, _ = MARKERS.get(worker.ppe.get("helmet", PPEState.UNKNOWN), ("[?]", COLOR_UNKNOWN))
            v_text, _ = MARKERS.get(worker.ppe.get("safety_vest", PPEState.UNKNOWN), ("[?]", COLOR_UNKNOWN))
            g_text, _ = MARKERS.get(worker.ppe.get("gloves", PPEState.UNKNOWN), ("[?]", COLOR_UNKNOWN))
            f_text, _ = MARKERS.get(worker.ppe.get("safety_footwear", PPEState.UNKNOWN), ("[?]", COLOR_UNKNOWN))

            line1 = header_text
            line2 = f"H:{h_text} V:{v_text} G:{g_text} F:{f_text}"

            # Calculate HUD background dimensions
            card_w = max(190, max(len(line1), len(line2), len(detail_text)) * 8 + 10)
            card_h = 58 if detail_text else 42

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

            # Draw Line 3 (Detail): "Missing: Helmet" (RED) or "Footwear visibility limited" (UNKNOWN)
            if detail_text:
                cv2.putText(
                    out, detail_text, (card_x1 + 6, card_y1 + 51),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, badge_color, 1, cv2.LINE_AA
                )

        return out
