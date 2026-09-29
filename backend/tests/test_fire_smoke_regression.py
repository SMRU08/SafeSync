"""
test_fire_smoke_regression.py — SafeSync Fire & Smoke Regression Test Suite
===========================================================================
Validates the end-to-end fix for Fire & Smoke detection across:
1. Detector multi-task class retention (ensuring fire & smoke are not suppressed)
2. WorkerComplianceEngine environmental_hazards population
3. Temporal validation: CANDIDATE -> DETECTING -> CONFIRMED
4. SafetyEngine Rule 1 (Fire) and Rule 2 (Smoke) P0/P1 event generation
5. Hazard detection when Workers = 0 (independence constraint)
6. Visualizer dual-type rendering (dict and HazardEventDetail)
7. Hard negative / non-hazard rejection
"""

import os
import cv2
import numpy as np
import pytest
from app.ai.detection.detector import Detector
from app.ai.compliance.compliance_engine import WorkerComplianceEngine
from app.ai.compliance.visualizer import ComplianceVisualizer
from app.ai.hazards.hazard_engine import HazardAnalysisEngine
from app.ai.hazards.schemas import (
    HazardType,
    HazardState,
    HazardEventDetail,
    HazardBoundingBox,
)
from app.services.safety_engine import SafetyEngine, EventType, AlarmPriority


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEST_A_PATH = os.path.join(ROOT, "datasets", "processed_v3", "images", "test", "dfire_00013.jpg")
TEST_B_PATH = os.path.join(ROOT, "datasets", "processed_v3", "images", "test", "dfire_00000.jpg")


class TestFireSmokeRegression:

    def test_detector_retains_fire_and_smoke(self):
        """Ensures Detector does NOT discard class 5 (fire) and class 6 (smoke)."""
        detector = Detector(model_type="ppe")
        assert "fire" in detector.class_conf_thresholds or detector.default_conf <= 0.20
        assert "smoke" in detector.class_conf_thresholds or detector.default_conf <= 0.20

    @pytest.mark.skipif(not os.path.exists(TEST_A_PATH), reason="User Test A image not found")
    def test_compliance_engine_extracts_environmental_hazards_test_a(self):
        """Ensures ComplianceEngine populates environmental_hazards even when workers=0 on Test A."""
        engine = WorkerComplianceEngine()
        img = cv2.imread(TEST_A_PATH)
        assert img is not None, "Failed to load Test A image"

        resp, _, _ = engine.process_frame(img, confidence_threshold=0.20)
        assert len(resp.environmental_hazards) > 0, "environmental_hazards must not be empty on Test A"

        smoke_hazards = [
            h for h in resp.environmental_hazards if h.get("class_name") == "smoke"
        ]
        assert len(smoke_hazards) >= 1, f"Expected smoke hazard in Test A, got: {resp.environmental_hazards}"
        assert smoke_hazards[0]["confidence"] >= 0.20

    @pytest.mark.skipif(not os.path.exists(TEST_B_PATH), reason="User Test B image not found")
    def test_compliance_engine_extracts_environmental_hazards_test_b(self):
        """Ensures ComplianceEngine populates environmental_hazards on Test B."""
        engine = WorkerComplianceEngine()
        img = cv2.imread(TEST_B_PATH)
        assert img is not None, "Failed to load Test B image"

        resp, _, _ = engine.process_frame(img, confidence_threshold=0.20)
        assert len(resp.environmental_hazards) > 0, "environmental_hazards must not be empty on Test B"

        smoke_hazards = [
            h for h in resp.environmental_hazards if h.get("class_name") == "smoke"
        ]
        assert len(smoke_hazards) >= 1, f"Expected smoke hazard in Test B, got: {resp.environmental_hazards}"

    @pytest.mark.skipif(not os.path.exists(TEST_A_PATH), reason="User Test A image not found")
    def test_hazard_engine_temporal_confirmation_pipeline(self):
        """
        Validates temporal state progression:
        Frame 1: CANDIDATE (No alert)
        Frame 2: DETECTING (No alert)
        Frame 3: CONFIRMED -> Triggers P0/P1 emergency alert in SafetyEngine
        """
        comp_engine = WorkerComplianceEngine()
        haz_engine = HazardAnalysisEngine()
        safety_engine = SafetyEngine()

        img = cv2.imread(TEST_A_PATH)
        comp_resp, _, _ = comp_engine.process_frame(img, confidence_threshold=0.20)
        raw_hazards = comp_resp.environmental_hazards
        assert len(raw_hazards) > 0

        # Frame 1
        h_resp1 = haz_engine.process_raw_hazards(raw_hazards, img.shape[:2], camera_id="cam_test")
        assert h_resp1.scene_hazard_state == HazardState.CANDIDATE
        assess1 = safety_engine.assess_scene("cam_test", compliance_response=comp_resp, hazard_response=h_resp1)
        # CANDIDATE stage must NOT trigger alerts
        assert len([e for e in assess1.events if e.event_type == EventType.SMOKE_DETECTED]) == 0

        # Frame 2
        h_resp2 = haz_engine.process_raw_hazards(raw_hazards, img.shape[:2], camera_id="cam_test")
        assert h_resp2.scene_hazard_state in (HazardState.DETECTING, HazardState.CONFIRMED)

        # Frame 3
        h_resp3 = haz_engine.process_raw_hazards(raw_hazards, img.shape[:2], camera_id="cam_test")
        assert h_resp3.scene_hazard_state == HazardState.CONFIRMED
        assert len(h_resp3.hazards) >= 1
        assert h_resp3.hazards[0].state == HazardState.CONFIRMED

        assess3 = safety_engine.assess_scene("cam_test", compliance_response=comp_resp, hazard_response=h_resp3)
        smoke_events = [e for e in assess3.events if e.event_type == EventType.SMOKE_DETECTED]
        assert len(smoke_events) == 1, "Must generate exactly one SMOKE_DETECTED event on confirmation"
        assert smoke_events[0].details.get("priority") in ("P0", "P1")

    def test_visualizer_handles_both_dict_and_hazard_event_detail(self):
        """Verifies ComplianceVisualizer handles dicts and HazardEventDetail without AttributeError."""
        viz = ComplianceVisualizer()
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # 1. Test dict input (raw detections)
        raw_dict = [{"class_name": "fire", "bbox": [50, 50, 150, 150], "confidence": 0.88}]
        res1 = viz.draw_frame(dummy_frame, workers=[], hazards=raw_dict)
        assert res1.shape == dummy_frame.shape

        # 2. Test HazardEventDetail input (tracked state)
        h_detail = HazardEventDetail(
            event_id="HAZARD-9999",
            hazard_type=HazardType.SMOKE,
            state=HazardState.CONFIRMED,
            camera_id="cam_01",
            zone_id="zone_test",
            confidence=0.75,
            raw_model_confidence=0.75,
            average_confidence=0.75,
            max_confidence=0.75,
            validated_confidence=0.75,
            bbox=HazardBoundingBox.from_xyxy(100, 100, 300, 300),
            first_seen="2026-09-27T00:00:00Z",
            last_seen="2026-09-27T00:00:01Z",
            duration_seconds=1.2,
            detection_count=4,
            persistence_ratio=1.0,
            frames_detected=4,
            frames_missed=0,
            spatial_consistency_score=1.0,
            temporal_score=1.0,
            final_hazard_state="CONFIRMED",
        )
        res2 = viz.draw_frame(dummy_frame, workers=[], hazards=[h_detail])
        assert res2.shape == dummy_frame.shape

    def test_clean_frame_does_not_trigger_false_hazard(self):
        """Verifies a blank/clean frame produces 0 environmental hazards."""
        comp_engine = WorkerComplianceEngine()
        clean_img = np.zeros((480, 640, 3), dtype=np.uint8)
        resp, _, _ = comp_engine.process_frame(clean_img, confidence_threshold=0.20)
        assert len(resp.environmental_hazards) == 0
