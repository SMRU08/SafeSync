"""
association.py — RAKSHYA VISION Phase 5
Spatial anatomy-aware association between detected PPE items and tracked workers.
Resolves multi-worker assignment contention via optimal bipartite matching.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from scipy.optimize import linear_sum_assignment

try:
    from app.ai.compliance.schemas import PPEItemType, WorkerBoundingBox
except ImportError:
    from backend.app.ai.compliance.schemas import PPEItemType, WorkerBoundingBox


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
        self, worker_box: np.ndarray, ppe_box: np.ndarray, item_type: PPEItemType
    ) -> float:
        """
        Calculates spatial match score between a worker and a candidate PPE item.
        Score ranges from 0.0 (no match / outside anatomical zone) to 1.0+ (perfect match).
        """
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
            min_cont = self.helmet_params.get("min_containment_ratio", 0.20)
        elif item_type == PPEItemType.SAFETY_VEST:
            min_cont = self.vest_params.get("min_containment_ratio", 0.30)
        elif item_type == PPEItemType.GLOVES:
            min_cont = self.gloves_params.get("min_containment_ratio", 0.15)
        elif item_type == PPEItemType.SAFETY_FOOTWEAR:
            min_cont = self.footwear_params.get("min_containment_ratio", 0.15)
        else:
            min_cont = 0.20

        if containment < min_cont:
            return 0.0

        # Normalized horizontal and vertical alignment penalty
        p_xc = (px1 + px2) / 2.0
        p_yc = (py1 + py2) / 2.0
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
        """
        img_h, img_w = img_shape[:2]
        wb = worker_boxes[worker_idx]
        zone = self.get_body_zone(wb, item_type)
        zx1, zy1, zx2, zy2 = zone

        # Check frame boundary clipping
        if item_type == PPEItemType.HELMET and zy1 <= self.edge_margin_px:
            return True  # Head cut off at top
        if item_type == PPEItemType.SAFETY_FOOTWEAR and zy2 >= (img_h - self.edge_margin_px):
            return True  # Feet cut off at bottom
        if (zx1 <= self.edge_margin_px and (wb[2] - wb[0]) < 30) or (
            zx2 >= (img_w - self.edge_margin_px) and (wb[2] - wb[0]) < 30
        ):
            return True  # Body cut off at side

        # Check occlusion by other workers
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
    ) -> Tuple[Dict[int, Dict[str, Optional[Dict[str, Any]]]], List[Dict[str, Any]]]:
        """
        Associates detected PPE items with tracked workers.

        Args:
            tracked_workers: List of (track_id, bbox_xyxy, confidence)
            ppe_detections: List of dicts with keys 'class_name', 'bbox' [x1, y1, x2, y2], 'confidence'
            img_shape: (height, width) of input image

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
                    aff = self.compute_affinity(wb, p_box, item_type)
                    affinity_matrix[w_idx, i_idx] = aff
                    if aff > 0.15:  # Minimum acceptable affinity threshold
                        cost_matrix[w_idx, i_idx] = 1.0 - aff

            # Bipartite matching via Hungarian algorithm
            row_ind, col_ind = linear_sum_assignment(cost_matrix)

            matched_items_indices = set()
            for r, c in zip(row_ind, col_ind):
                if cost_matrix[r, c] < 0.85 and affinity_matrix[r, c] >= 0.15:
                    tid = worker_ids[r]
                    matched_item = items[c].copy()
                    matched_item["association_score"] = round(float(affinity_matrix[r, c]), 3)
                    result[tid][item_type.value] = matched_item
                    matched_items_indices.add(c)

            for i_idx, item in enumerate(items):
                if i_idx not in matched_items_indices:
                    unassociated_ppe.append(item)

        return result, unassociated_ppe
