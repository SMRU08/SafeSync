"""
zones.py — SafeSync Phase 6
Camera and Zone Metadata Manager with optional ROI Polygon containment.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List, Tuple

log = logging.getLogger(__name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DEFAULT_CAMERAS_CONFIG = os.path.join(ROOT, "configs", "cameras.yaml")


DEFAULT_HAZARD_CONFIG = os.path.join(ROOT, "configs", "hazard.yaml")


def point_in_polygon(x: float, y: float, polygon: List[List[float]]) -> bool:
    """
    Standard Ray-Casting algorithm to check if (x, y) is inside a polygon.
    Polygon is a list of [x, y] vertices.
    """
    n = len(polygon)
    if n < 3:
        return False
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


class ZoneManager:
    """
    Manages camera metadata, spatial zone associations, and hazard exclusion/inclusion ROIs.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        hazard_config_path: Optional[str] = None,
    ):
        self.config_path = config_path or DEFAULT_CAMERAS_CONFIG
        self.hazard_config_path = hazard_config_path or DEFAULT_HAZARD_CONFIG
        self.cameras: Dict[str, Dict[str, Any]] = {}
        self.zones: Dict[str, Dict[str, Any]] = {}
        self.exclusion_rois: Dict[str, List[Dict[str, Any]]] = {}
        self.inclusion_rois: Dict[str, List[List[float]]] = {}
        self.load_config()

    def load_config(self):
        # 1. Load cameras and zones from cameras.yaml
        if os.path.isfile(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                for cam in data.get("cameras", []):
                    cid = str(cam.get("id", ""))
                    if cid:
                        self.cameras[cid] = cam
                        # Check if camera has hazard_roi configured directly
                        h_roi = cam.get("hazard_roi")
                        if h_roi and len(h_roi) >= 3:
                            self.inclusion_rois[cid] = h_roi

                for z in data.get("zones", []):
                    zid = str(z.get("id", ""))
                    if zid:
                        self.zones[zid] = z

                log.info("ZoneManager loaded %d cameras and %d zones from %s", len(self.cameras), len(self.zones), self.config_path)
            except Exception as e:
                log.error("Failed to load cameras config: %s", e)
        else:
            log.warning("Cameras config not found at %s. Using fallback.", self.config_path)

        # 2. Load exclusion ROIs from hazard.yaml
        if os.path.isfile(self.hazard_config_path):
            try:
                with open(self.hazard_config_path, "r", encoding="utf-8") as f:
                    h_data = yaml.safe_load(f) or {}
                zones_cfg = h_data.get("zones", {})
                self.exclusion_rois = zones_cfg.get("exclusion_rois", {}) or {}
                log.info("ZoneManager loaded exclusion ROIs for cameras: %s", list(self.exclusion_rois.keys()))
            except Exception as e:
                log.error("Failed to load hazard config for exclusion ROIs: %s", e)

    def is_in_exclusion_roi(
        self,
        camera_id: str,
        center_x: float,
        center_y: float,
        frame_width: int = 640,
        frame_height: int = 480,
    ) -> bool:
        """
        Returns True if the coordinate falls inside any configured exclusion ROI
        for this camera (e.g. windows, bright ceiling lights, steam exhaust).
        Detections in exclusion ROIs should be filtered out.
        """
        if not camera_id or camera_id not in self.exclusion_rois:
            return False

        norm_x = center_x / max(1.0, float(frame_width))
        norm_y = center_y / max(1.0, float(frame_height))

        rois = self.exclusion_rois[camera_id]
        for roi in rois:
            polygon = roi.get("polygon")
            if polygon and len(polygon) >= 3:
                if point_in_polygon(norm_x, norm_y, polygon):
                    log.debug("Coordinate (%f, %f) falls inside exclusion ROI '%s'", norm_x, norm_y, roi.get("name", "unnamed"))
                    return True
        return False

    def is_in_hazard_roi(
        self,
        camera_id: str,
        center_x: float,
        center_y: float,
        frame_width: int = 640,
        frame_height: int = 480,
    ) -> bool:
        """
        If camera has a configured inclusion hazard_roi, returns True if inside it.
        If no inclusion hazard_roi is configured, returns True (all regions monitored).
        """
        if not camera_id or camera_id not in self.inclusion_rois:
            return True

        norm_x = center_x / max(1.0, float(frame_width))
        norm_y = center_y / max(1.0, float(frame_height))
        polygon = self.inclusion_rois[camera_id]
        return point_in_polygon(norm_x, norm_y, polygon)

    def resolve_zone(
        self,
        camera_id: str,
        center_x: float,
        center_y: float,
        frame_width: int = 640,
        frame_height: int = 480,
    ) -> str:
        """
        Resolves the zone for a given camera and coordinate.
        If camera is not found, returns 'UNKNOWN'.
        If camera has a zone and optional polygon ROI is defined, verifies containment.
        """
        if not camera_id or camera_id not in self.cameras:
            return "UNKNOWN"

        cam_info = self.cameras[camera_id]
        zone_id = cam_info.get("zone_id", "UNKNOWN")

        if zone_id not in self.zones:
            return zone_id if zone_id != "UNKNOWN" else "UNKNOWN"

        zone_info = self.zones[zone_id]
        polygon = zone_info.get("polygon_normalized")

        if polygon and len(polygon) >= 3:
            # Check normalized coordinates
            norm_x = center_x / max(1.0, float(frame_width))
            norm_y = center_y / max(1.0, float(frame_height))
            if point_in_polygon(norm_x, norm_y, polygon):
                return zone_id
            else:
                # Outside the defined polygon zone
                return "UNKNOWN"

        # If no polygon ROI is required, camera belongs to the assigned zone
        return zone_id

    def get_camera_name(self, camera_id: str) -> str:
        if camera_id in self.cameras:
            return self.cameras[camera_id].get("name", camera_id)
        return camera_id or "Default Camera"

    def get_zone_name(self, zone_id: str) -> str:
        if zone_id in self.zones:
            return self.zones[zone_id].get("name", zone_id)
        if zone_id == "UNKNOWN":
            return "Unassigned Zone"
        return zone_id
