"""
association.py — SafeSync Phase 5
Spatial anatomy-aware association between detected PPE items and tracked workers.
Resolves multi-worker assignment contention via optimal bipartite matching.
"""

import numpy as np
import cv2
from typing import List, Dict, Tuple, Optional, Any
from scipy.optimize import linear_sum_assignment

try:
    from app.ai.compliance.schemas import PPEItemType, WorkerBoundingBox
except ImportError:
    from backend.app.ai.compliance.schemas import PPEItemType, WorkerBoundingBox


def verify_helmet_features(
    worker_box: np.ndarray,
    helmet_box: np.ndarray,
    frame: Optional[np.ndarray] = None,
    confidence: float = 0.0,
    img_shape: Optional[Tuple[int, int]] = None,
) -> bool:
    """
    Validates candidate helmet detection against human cranial anatomy and visual features:
    1. Relative height ratio: Head/helmet occupies 0.05 to 0.26 of standing person height
       (or up to 0.42 if the lower body is clipped by the bottom frame boundary).
    2. Aspect ratio: Helmets range from compact to wide-brim (0.55 to 2.80 width-to-height).
       Wide-brim hard hats (ANSI Type P, forestry, wide-brim industrial) have pw/ph up to ~2.26.
    3. Cranium zone: Helmet center must fall in the uppermost cranium region of the worker.
    4. Relative width ratio: Helmet width occupies 0.18 to 0.90 of worker box width.
    5. Hair vs Helmet visual verification (when frame is available):
       Rejects dark/brown hair patches that lack helmet shell colors (yellow, white, red, blue, green).
    """
    wx1, wy1, wx2, wy2 = [float(v) for v in worker_box]
    px1, py1, px2, py2 = [float(v) for v in helmet_box]

    wh = max(1.0, wy2 - wy1)
    ww = max(1.0, wx2 - wx1)
    ph = max(1.0, py2 - py1)
    pw = max(1.0, px2 - px1)

    # Detect if lower body is clipped at the bottom of the frame
    is_lower_body_clipped = False
    if img_shape is not None:
        ih, _ = img_shape[:2]
        if wy2 >= (ih - 25):
            is_lower_body_clipped = True

    max_h_ratio = 0.42 if is_lower_body_clipped else 0.26
    max_yc = 0.35 if is_lower_body_clipped else 0.24

    # 1. Anatomical height ratio
    h_ratio = ph / wh
    if h_ratio < 0.05 or h_ratio > max_h_ratio:
        return False

    # 2. Aspect ratio (width / height) — range: 0.55 (narrow safety cap) to 2.80 (wide-brim hard hat)
    aspect_ratio = pw / ph
    if aspect_ratio < 0.55 or aspect_ratio > 2.80:
        return False

    # 3. Cranium zone: helmet center relative to top of worker
    pyc = (py1 + py2) / 2.0
    rel_yc = (pyc - wy1) / wh
    if rel_yc < -0.10 or rel_yc > max_yc:
        return False

    # 4. Relative width (pw / ww) — up to 0.98 for wide-brim industrial helmets
    w_ratio = pw / ww
    if w_ratio < 0.18 or w_ratio > 0.98:
        return False

    # 5. Visual chromatic & luminance check for hair false positives
    if frame is not None and frame.size > 0:
        ih, iw = frame.shape[:2]
        ix1 = max(0, min(iw - 1, int(px1)))
        iy1 = max(0, min(ih - 1, int(py1)))
        ix2 = max(ix1 + 1, min(iw, int(px2)))
        iy2 = max(iy1 + 1, min(ih, int(py2)))

        crop = frame[iy1:iy2, ix1:ix2]
        if crop.size >= 36:
            hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
            h = hsv[:, :, 0]
            s = hsv[:, :, 1]
            v = hsv[:, :, 2]

            # Industrial helmet shell colors (EN 397 / ANSI Z89.1):
            # - Yellow / Lime: H: 20-42, S >= 60, V >= 80
            # - Red / Orange: (H <= 12 or H >= 168), S >= 80, V >= 95
            # - White / Silver: S <= 45, V >= 165
            # - Blue: H: 95-130, S >= 60, V >= 60
            # - Green: H: 45-85, S >= 60, V >= 60
            m_yellow = (h >= 20) & (h <= 42) & (s >= 60) & (v >= 80)
            m_red = ((h <= 12) | (h >= 168)) & (s >= 80) & (v >= 95)
            m_white = (s <= 45) & (v >= 165)
            m_blue = (h >= 95) & (h <= 130) & (s >= 60) & (v >= 60)
            m_green = (h >= 45) & (h <= 85) & (s >= 60) & (v >= 60)

            total = float(crop.shape[0] * crop.shape[1])
            shell_color_ratio = float(np.count_nonzero(m_yellow | m_red | m_white | m_blue | m_green)) / total

            # If the model has high confidence (>=0.65), trust it directly without HSV gating
            if confidence >= 0.65:
                return True

            # If the crop lacks helmet shell colors, reject only if confidence is low (<0.50)
            if shell_color_ratio < 0.05:
                if confidence < 0.50:
                    return False

    return True


def verify_safety_vest_features(
    worker_box: np.ndarray,
    vest_box: np.ndarray,
    frame: Optional[np.ndarray] = None,
    confidence: float = 0.0,
    img_shape: Optional[Tuple[int, int]] = None,
) -> bool:
    """
    Validates candidate safety vest detection against thoracic anatomy and high-visibility chromatic requirements:
    1. Anatomical height ratio: Vest spans 0.14 to 0.65 of standing worker height.
    2. Vertical placement: Vest center must fall in the thoracic/torso zone (0.12 to 0.68 of worker height).
    3. Relative width ratio: Vest occupies 0.28 to 1.25 of worker width.
    4. High-visibility chromatic & reflective verification (when frame is available):
       Industrial safety vests (EN ISO 20471 / ANSI 107) feature fluorescent lime or fluorescent orange
       and/or retro-reflective silver bands.
       Casual clothing (black, navy, grey, brown, white cotton, red shirts, dark green hoodies) lacks
       fluorescent pigments and retro-reflective tape, rejecting false positives.
    """
    wx1, wy1, wx2, wy2 = [float(v) for v in worker_box]
    px1, py1, px2, py2 = [float(v) for v in vest_box]

    wh = max(1.0, wy2 - wy1)
    ww = max(1.0, wx2 - wx1)
    ph = max(1.0, py2 - py1)
    pw = max(1.0, px2 - px1)

    # 1. Anatomical height ratio
    h_ratio = ph / wh
    if h_ratio < 0.14 or h_ratio > 0.65:
        return False

    # 2. Torso zone: vest center relative to top of worker
    pyc = (py1 + py2) / 2.0
    rel_yc = (pyc - wy1) / wh
    if rel_yc < 0.12 or rel_yc > 0.68:
        return False

    # 3. Relative width
    w_ratio = pw / ww
    if w_ratio < 0.28 or w_ratio > 1.25:
        return False

    # 4. High-visibility chromatic & reflective tape verification
    if frame is not None and frame.size > 0:
        ih, iw = frame.shape[:2]
        ix1 = max(0, min(iw - 1, int(px1)))
        iy1 = max(0, min(ih - 1, int(py1)))
        ix2 = max(ix1 + 1, min(iw, int(px2)))
        iy2 = max(iy1 + 1, min(ih, int(py2)))

        crop = frame[iy1:iy2, ix1:ix2]
        if crop.size >= 48:
            hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
            h = hsv[:, :, 0]
            s = hsv[:, :, 1]
            v = hsv[:, :, 2]

            # High-visibility fluorescent lime-yellow: H: 25-45 (S >= 60, V >= 115) or chartreuse H: 45-60 (S >= 60, V >= 135)
            mask_lime = ((h >= 25) & (h <= 45) & (s >= 60) & (v >= 115)) | ((h > 45) & (h <= 60) & (s >= 60) & (v >= 135))

            # High-visibility fluorescent orange: H: 5-22, S >= 90, V >= 130
            mask_orange = (h >= 5) & (h <= 22) & (s >= 90) & (v >= 130)

            # Retro-reflective silver strips: high reflectance (V >= 190), low saturation (S <= 60)
            mask_reflective = (s <= 60) & (v >= 190)

            total = float(crop.shape[0] * crop.shape[1])
            hivis_ratio = float(np.count_nonzero(mask_lime | mask_orange)) / total
            refl_ratio = float(np.count_nonzero(mask_reflective)) / total

            # An industrial safety vest: accept high-confidence model detections directly
            is_valid_vest = (hivis_ratio >= 0.03) or (refl_ratio >= 0.015)
            if not is_valid_vest and confidence < 0.45:
                return False

    return True


class SpatialPPEAssociator:
    """
    Associates detected PPE items with specific tracked workers based on
    human anatomical body zones, containment ratios, and spatial proximity.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        assoc_cfg = cfg.get("association", {})

        # Spatial anatomical zone parameters
        self.helmet_params = assoc_cfg.get("helmet", {
            "vertical_roi_top": -0.05,
            "vertical_roi_bottom": 0.30,
            "max_lateral_offset": 0.25,
            "min_containment_ratio": 0.20,
        })
        self.vest_params = assoc_cfg.get("safety_vest", {
            "vertical_roi_top": 0.15,
            "vertical_roi_bottom": 0.70,
            "max_lateral_offset": 0.20,
            "min_containment_ratio": 0.30,
        })
        self.gloves_params = assoc_cfg.get("gloves", {
            "vertical_roi_top": 0.35,
            "vertical_roi_bottom": 0.90,
            "max_lateral_offset": 0.35,
            "min_containment_ratio": 0.15,
        })
        self.footwear_params = assoc_cfg.get("safety_footwear", {
            "vertical_roi_top": 0.70,
            "vertical_roi_bottom": 1.05,
            "max_lateral_offset": 0.25,
            "min_containment_ratio": 0.15,
        })

        occl_cfg = cfg.get("occlusion", {})
        self.edge_margin_px = occl_cfg.get("edge_margin_px", 20)
        self.inter_person_overlap_thresh = occl_cfg.get("inter_person_overlap_thresh", 0.35)

    def get_body_zone(self, worker_box: np.ndarray, item_type: PPEItemType) -> np.ndarray:
        """
        Calculates the expected [zx1, zy1, zx2, zy2] anatomical region for a specific PPE type.
        worker_box: [wx1, wy1, wx2, wy2]
        """
        wx1, wy1, wx2, wy2 = worker_box
        w = max(1.0, float(wx2 - wx1))
        h = max(1.0, float(wy2 - wy1))

        if item_type == PPEItemType.HELMET:
            params = self.helmet_params
        elif item_type == PPEItemType.SAFETY_VEST:
            params = self.vest_params
        elif item_type == PPEItemType.GLOVES:
            params = self.gloves_params
        elif item_type == PPEItemType.SAFETY_FOOTWEAR:
            params = self.footwear_params
        else:
            return worker_box.copy()

        top_rel = params.get("vertical_roi_top", 0.0)
        bottom_rel = params.get("vertical_roi_bottom", 1.0)
        lat_rel = params.get("max_lateral_offset", 0.2)

        zy1 = wy1 + top_rel * h
        zy2 = wy1 + bottom_rel * h
        zx1 = wx1 - lat_rel * w
        zx2 = wx2 + lat_rel * w

        return np.array([zx1, zy1, zx2, zy2], dtype=float)

    def compute_affinity(
        self,
        worker_box: np.ndarray,
        ppe_box: np.ndarray,
        item_type: PPEItemType,
        frame: Optional[np.ndarray] = None,
        confidence: float = 0.0,
        img_shape: Optional[Tuple[int, int]] = None,
    ) -> float:
        """
        Calculates spatial match score between a worker and a candidate PPE item.
        Score ranges from 0.0 (no match / outside anatomical zone) to 1.0+ (perfect match).
        """
        # First verify anatomical geometry, dimensions, and visual features
        if item_type == PPEItemType.HELMET:
            if not verify_helmet_features(
                worker_box, ppe_box, frame=frame, confidence=confidence, img_shape=img_shape
            ):
                return 0.0
        elif item_type == PPEItemType.SAFETY_VEST:
            if not verify_safety_vest_features(
                worker_box, ppe_box, frame=frame, confidence=confidence, img_shape=img_shape
            ):
                return 0.0

        zone = self.get_body_zone(worker_box, item_type)
        zx1, zy1, zx2, zy2 = zone
        px1, py1, px2, py2 = ppe_box

        # Compute intersection between PPE box and body zone
        ix1 = max(zx1, px1)
        iy1 = max(zy1, py1)
        ix2 = min(zx2, px2)
        iy2 = min(zy2, py2)

        inter_w = max(0.0, ix2 - ix1)
        inter_h = max(0.0, iy2 - iy1)
        inter_area = inter_w * inter_h

        ppe_area = max(1.0, float((px2 - px1) * (py2 - py1)))
        containment = inter_area / ppe_area

        if item_type == PPEItemType.HELMET:
            min_cont = self.helmet_params.get("min_containment_ratio", 0.35)
        elif item_type == PPEItemType.SAFETY_VEST:
            min_cont = self.vest_params.get("min_containment_ratio", 0.40)
        elif item_type == PPEItemType.GLOVES:
            min_cont = self.gloves_params.get("min_containment_ratio", 0.15)
        elif item_type == PPEItemType.SAFETY_FOOTWEAR:
            min_cont = self.footwear_params.get("min_containment_ratio", 0.15)
        else:
            min_cont = 0.20

        # Normalized centers for horizontal and vertical checks
        p_xc = (px1 + px2) / 2.0
        p_yc = (py1 + py2) / 2.0

        # Strict horizontal anchoring: center of PPE must be within worker box horizontal bounds
        wx1, wy1, wx2, wy2 = worker_box
        worker_w = max(1.0, float(wx2 - wx1))
        worker_h = max(1.0, float(wy2 - wy1))
        max_lat_margin = 0.20 * worker_w
        if p_xc < (wx1 - max_lat_margin) or p_xc > (wx2 + max_lat_margin):
            return 0.0

        # Strict vertical anatomical zone checks
        rel_yc = (p_yc - wy1) / worker_h
        if item_type == PPEItemType.HELMET:
            if rel_yc < -0.15 or rel_yc > 0.32:
                return 0.0
        elif item_type == PPEItemType.SAFETY_VEST:
            if rel_yc < 0.12 or rel_yc > 0.70:
                return 0.0
        elif item_type == PPEItemType.GLOVES:
            if rel_yc < 0.20 or rel_yc > 1.05:
                return 0.0
        elif item_type == PPEItemType.SAFETY_FOOTWEAR:
            if rel_yc < 0.60 or rel_yc > 1.15:
                return 0.0

        z_xc = (zx1 + zx2) / 2.0
        z_yc = (zy1 + zy2) / 2.0

        zone_w = max(1.0, zx2 - zx1)
        zone_h = max(1.0, zy2 - zy1)

        norm_dx = abs(p_xc - z_xc) / zone_w
        norm_dy = abs(p_yc - z_yc) / zone_h

        proximity_score = max(0.0, 1.0 - (0.5 * norm_dx + 0.5 * norm_dy))
        affinity = 0.6 * containment + 0.4 * proximity_score
        return float(affinity)

    def detect_occlusion(
        self,
        worker_idx: int,
        worker_boxes: List[np.ndarray],
        item_type: PPEItemType,
        img_shape: Tuple[int, int],
    ) -> bool:
        """
        Determines whether a worker's anatomical zone for a given PPE type is occluded
        either by frame boundary clipping or by overlapping adjacent workers.

        Frame boundary occlusion logic:
        - HELMET: head severed at top frame boundary
        - GLOVES / SAFETY_FOOTWEAR: lower body (hands/feet) clipped at bottom or lateral
        - Any type: severe lateral clipping (< 25px visible width)
        - Half-body workers (wh/ww < 2.0): lower body not in frame → GLOVES and SAFETY_FOOTWEAR UNKNOWN
        """
        img_h, img_w = img_shape[:2]
        wb = worker_boxes[worker_idx]
        wx1, wy1, wx2, wy2 = float(wb[0]), float(wb[1]), float(wb[2]), float(wb[3])
        wh = max(1.0, wy2 - wy1)
        ww = max(1.0, wx2 - wx1)

        zone = self.get_body_zone(wb, item_type)
        zx1, zy1, zx2, zy2 = zone

        # --- Frame boundary clipping checks ---
        margin = max(25, int(img_w * 0.04))

        # Helmet: head/cranium severed at top frame edge
        if item_type == PPEItemType.HELMET:
            if wy1 <= margin and (zy2 - zy1) < 25:
                return True  # Only head visible at top of frame → cranium clipped

        # Safety footwear: feet cut off at bottom frame edge
        if item_type == PPEItemType.SAFETY_FOOTWEAR:
            if zy2 >= (img_h - margin) or wy2 >= (img_h - margin):
                return True  # Feet zone extends to or below frame bottom

        # Gloves: hands (lower-arm zone) clipped at bottom or lateral edges
        if item_type == PPEItemType.GLOVES:
            if zy2 >= (img_h - margin) or wy2 >= (img_h - margin):
                return True  # Gloves zone clipped at bottom

        # Lateral clipping: body severely cut off at either side
        if (wx1 <= margin and ww < 40) or (wx2 >= (img_w - margin) and ww < 40):
            return True

        # Half-body detection: worker height-to-width ratio < 2.0 suggests lower body is off frame
        # (Standing adult: wh/ww ≈ 2.5–4.0; if ratio < 2.0 → bottom of body is not in frame)
        if wh / ww < 2.0:
            if item_type in (PPEItemType.SAFETY_FOOTWEAR, PPEItemType.GLOVES):
                return True  # Lower body not visible

        # --- Frame boundary check on the body zone itself ---
        if zy2 > img_h - 2 or zy1 < 0:
            return True
        if zx2 > img_w - 2 or zx1 < 0:
            return True

        # --- Occlusion by other workers ---
        zone_area = max(1.0, (zx2 - zx1) * (zy2 - zy1))
        for j, other_wb in enumerate(worker_boxes):
            if j == worker_idx:
                continue
            # Overlap between this worker's zone and other worker's body
            ox1 = max(zx1, other_wb[0])
            oy1 = max(zy1, other_wb[1])
            ox2 = min(zx2, other_wb[2])
            oy2 = min(zy2, other_wb[3])

            ow = max(0.0, ox2 - ox1)
            oh = max(0.0, oy2 - oy1)
            inter = ow * oh
            if (inter / zone_area) >= self.inter_person_overlap_thresh:
                return True

        return False

    def associate(
        self,
        tracked_workers: List[Tuple[int, np.ndarray, float]],
        ppe_detections: List[Dict[str, Any]],
        img_shape: Tuple[int, int] = (720, 1280),
        frame: Optional[np.ndarray] = None,
    ) -> Tuple[Dict[int, Dict[str, Optional[Dict[str, Any]]]], List[Dict[str, Any]]]:
        """
        Associates detected PPE items with tracked workers.

        Args:
            tracked_workers: List of (track_id, bbox_xyxy, confidence)
            ppe_detections: List of dicts with keys 'class_name', 'bbox' [x1, y1, x2, y2], 'confidence'
            img_shape: (height, width) of input image
            frame: Optional BGR ndarray frame for visual feature and chromatic verification

        Returns:
            Tuple of:
            - associations: Dict mapping track_id -> Dict[item_type_str -> matched_ppe_dict or None]
            - unassociated_ppe: List of PPE detection dicts not matched to any worker
        """
        # Initialize output structure for all active workers
        result: Dict[int, Dict[str, Optional[Dict[str, Any]]]] = {
            tid: {
                PPEItemType.HELMET.value: None,
                PPEItemType.SAFETY_VEST.value: None,
                PPEItemType.GLOVES.value: None,
                PPEItemType.SAFETY_FOOTWEAR.value: None,
            }
            for tid, _, _ in tracked_workers
        }

        if not tracked_workers or not ppe_detections:
            return result, ppe_detections

        worker_boxes = [wb for _, wb, _ in tracked_workers]
        worker_ids = [tid for tid, _, _ in tracked_workers]
        num_workers = len(tracked_workers)

        unassociated_ppe: List[Dict[str, Any]] = []

        # Group PPE detections by canonical category
        ppe_by_category: Dict[PPEItemType, List[Dict[str, Any]]] = {
            PPEItemType.HELMET: [],
            PPEItemType.SAFETY_VEST: [],
            PPEItemType.GLOVES: [],
            PPEItemType.SAFETY_FOOTWEAR: [],
        }

        for ppe in ppe_detections:
            cname = ppe.get("class_name", "").lower()
            matched_enum = None
            for ppe_enum in PPEItemType:
                if ppe_enum.value == cname:
                    matched_enum = ppe_enum
                    break
            if matched_enum:
                ppe_by_category[matched_enum].append(ppe)
            else:
                unassociated_ppe.append(ppe)

        # Solve assignment independently for each PPE category to prevent cross-category conflicts
        for item_type, items in ppe_by_category.items():
            if not items:
                continue

            num_items = len(items)
            cost_matrix = np.ones((num_workers, num_items)) * 100.0
            affinity_matrix = np.zeros((num_workers, num_items))

            for w_idx, wb in enumerate(worker_boxes):
                for i_idx, item in enumerate(items):
                    p_box = np.array(item["bbox"], dtype=float)
                    p_conf = float(item.get("confidence", 0.0))
                    aff = self.compute_affinity(
                        wb,
                        p_box,
                        item_type,
                        frame=frame,
                        confidence=p_conf,
                        img_shape=img_shape,
                    )
                    affinity_matrix[w_idx, i_idx] = aff
                    if aff > 0.15:  # Minimum acceptable affinity threshold
                        cost_matrix[w_idx, i_idx] = 1.0 - aff

            # Bipartite matching via Hungarian algorithm
            row_ind, col_ind = linear_sum_assignment(cost_matrix)

            matched_items_indices = set()
            for r, c in zip(row_ind, col_ind):
                aff = affinity_matrix[r, c]
                if cost_matrix[r, c] < 0.85 and aff >= 0.15:
                    # Check for ambiguity with other workers (prevent cross-contamination)
                    ambiguous = False
                    if num_workers > 1:
                        other_affs = [affinity_matrix[other_r, c] for other_r in range(num_workers) if other_r != r]
                        max_other = max(other_affs) if other_affs else 0.0
                        if max_other > 0.20 and (aff - max_other) < 0.08:
                            ambiguous = True

                    if not ambiguous:
                        tid = worker_ids[r]
                        matched_item = items[c].copy()
                        matched_item["association_score"] = round(float(aff), 3)
                        result[tid][item_type.value] = matched_item
                        matched_items_indices.add(c)

            for i_idx, item in enumerate(items):
                if i_idx not in matched_items_indices:
                    unassociated_ppe.append(item)

        return result, unassociated_ppe
