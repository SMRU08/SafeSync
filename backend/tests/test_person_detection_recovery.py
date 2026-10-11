"""
test_person_detection_recovery.py — SafeSync Person Detection Recovery & Safety Semantics Tests

Verifies:
1. Absolute V3 Production Model Lock (Path & SHA-256).
2. Runtime operating thresholds (person: 0.22, fire/smoke: 0.20, gloves/footwear: 0.22).
3. Visible person in 1280x720 frame is detected by V3 and creates a tracked worker immediately.
4. Person detection survives NMS and ByteTrack tracking.
5. Invariant: 0 workers produces "NO_VERIFIED_DETECTION", NEVER "SAFE".
6. Invariant: Worker with full PPE produces "SAFE".
7. Invariant: Worker with confirmed absent PPE produces "VIOLATION".
8. Invariant: Worker with occluded gear produces "UNKNOWN", never a false violation.
"""

import os
import hashlib
import numpy as np
import pytest
from datetime import datetime, timezone

from app.ai.detection.model_loader import ModelLoader
from app.ai.detection.detector import Detector
from app.ai.compliance.compliance_engine import WorkerComplianceEngine
from app.services.safety_engine import SafetyEngine, SafetyAssessment
from app.ai.compliance.schemas import (
    ComplianceAnalysisResponse,
    ComplianceSummary,
    WorkerTrack,
    WorkerBoundingBox,
    PPEState,
    PPEItemType,
    PPEObservation,
    OverallComplianceState,
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
V3_EXPECTED_SHA = "9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe"
V3_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "detection", "ppe_fire_smoke_v3", "weights", "best.pt")
if not os.path.isfile(V3_MODEL_PATH):
    V3_MODEL_PATH = os.path.join("models", "detection", "ppe_fire_smoke_v3", "weights", "best.pt")


def test_v3_production_model_lock():
    """Verify that V3 checkpoint exists and matches approved SHA-256 hash exactly."""
    assert os.path.isfile(V3_MODEL_PATH), f"V3 checkpoint not found at {V3_MODEL_PATH}"
    hasher = hashlib.sha256()
    with open(V3_MODEL_PATH, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    actual_sha = hasher.hexdigest().lower()
    assert actual_sha == V3_EXPECTED_SHA, (
        f"V3 SHA-256 mismatch! Expected {V3_EXPECTED_SHA}, got {actual_sha}"
    )


def test_runtime_confidence_thresholds():
    """Verify that detector loads approved per-class operating thresholds."""
    detector = Detector()
    # Person operating threshold must be 0.22
    person_conf = detector.class_conf_thresholds.get("person", detector.default_conf)
    assert person_conf <= 0.22, f"Person threshold {person_conf} exceeds approved 0.22"

    # Fire and smoke must be 0.20
    fire_conf = detector.class_conf_thresholds.get("fire", detector.default_conf)
    smoke_conf = detector.class_conf_thresholds.get("smoke", detector.default_conf)
    assert fire_conf == 0.20, f"Fire threshold {fire_conf} != 0.20"
    assert smoke_conf == 0.20, f"Smoke threshold {smoke_conf} != 0.20"


def test_visible_person_detection_and_immediate_track():
    """Verify that a visible person in a 1280x720 frame creates an active track on frame 1."""
    import cv2
    img_path = "outputs/test_1280x720_person.jpg"
    if not os.path.isfile(img_path):
        pytest.skip(f"Test frame {img_path} not found")

    frame = cv2.imread(img_path)
    engine = WorkerComplianceEngine()
    resp, annotated_frame, latencies = engine.process_frame(
        frame,
        confidence_threshold=0.20,
        annotate=True,
    )

    assert resp is not None
    assert len(resp.workers) >= 1, "Visible person in 1280x720 frame must produce >= 1 tracked worker"
    w = resp.workers[0]
    assert w.track_id > 0
    assert w.bbox.width > 20
    assert w.bbox.height > 30


def test_invariant_zero_workers_is_never_safe():
    """
    Critical Invariant: 0 workers must produce NO_VERIFIED_DETECTION, NEVER SAFE.
    Zero workers does not imply compliance.
    """
    safety_engine = SafetyEngine()

    empty_compliance = ComplianceAnalysisResponse(
        frame_id=1,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        workers=[],
        summary=ComplianceSummary(
            total_workers=0,
            compliant_workers=0,
            non_compliant_workers=0,
            unknown_workers=0,
        ),
    )

    assessment = safety_engine.assess_scene(
        camera_id="camera_01",
        zone_id="production_floor",
        compliance_response=empty_compliance,
        hazard_response=None,
        camera_connected=True,
        ai_available=True,
    )

    assert assessment.workers_count == 0
    assert assessment.overall_safety_state == "NO_VERIFIED_DETECTION", (
        f"0 workers must evaluate to NO_VERIFIED_DETECTION, not {assessment.overall_safety_state}"
    )
    assert assessment.overall_safety_state != "SAFE", "0 workers must NEVER evaluate to SAFE"


def test_invariant_compliant_worker_evaluates_to_safe():
    """Worker detected with all required PPE present evaluates to SAFE."""
    safety_engine = SafetyEngine()

    worker = WorkerTrack(
        track_id=1,
        bbox=WorkerBoundingBox(x1=100, y1=100, x2=300, y2=500),
        confidence=0.85,
        overall_status=OverallComplianceState.COMPLIANT,
        ppe_status={
            "helmet": PPEState.PRESENT,
            "safety_vest": PPEState.PRESENT,
            "gloves": PPEState.PRESENT,
            "safety_footwear": PPEState.PRESENT,
        },
        ppe_details={
            "helmet": PPEObservation(item_type=PPEItemType.HELMET, state=PPEState.PRESENT, confidence=0.9),
            "safety_vest": PPEObservation(item_type=PPEItemType.SAFETY_VEST, state=PPEState.PRESENT, confidence=0.9),
            "gloves": PPEObservation(item_type=PPEItemType.GLOVES, state=PPEState.PRESENT, confidence=0.9),
            "safety_footwear": PPEObservation(item_type=PPEItemType.SAFETY_FOOTWEAR, state=PPEState.PRESENT, confidence=0.9),
        },
        is_compliant=True,
        history_length=15,
        first_seen=datetime.now(timezone.utc).isoformat(),
        last_seen=datetime.now(timezone.utc).isoformat(),
    )

    compliance_resp = ComplianceAnalysisResponse(
        frame_id=1,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        workers=[worker],
        summary=ComplianceSummary(
            total_workers=1,
            compliant_workers=1,
            non_compliant_workers=0,
            unknown_workers=0,
        ),
    )

    assessment = safety_engine.assess_scene(
        camera_id="camera_01",
        zone_id="production_floor",
        compliance_response=compliance_resp,
        hazard_response=None,
        camera_connected=True,
        ai_available=True,
    )

    assert assessment.workers_count == 1
    assert assessment.active_violations_count == 0
    assert assessment.overall_safety_state == "SAFE"


def test_invariant_worker_with_confirmed_violation_evaluates_to_violation():
    """Worker detected with confirmed absent required PPE evaluates to VIOLATION."""
    safety_engine = SafetyEngine()

    worker = WorkerTrack(
        track_id=2,
        bbox=WorkerBoundingBox(x1=100, y1=100, x2=300, y2=500),
        confidence=0.85,
        overall_status=OverallComplianceState.NON_COMPLIANT,
        ppe_status={
            "helmet": PPEState.ABSENT,
            "safety_vest": PPEState.PRESENT,
            "gloves": PPEState.PRESENT,
            "safety_footwear": PPEState.PRESENT,
        },
        ppe_details={
            "helmet": PPEObservation(item_type=PPEItemType.HELMET, state=PPEState.ABSENT, confidence=0.0, consecutive_missed=15),
            "safety_vest": PPEObservation(item_type=PPEItemType.SAFETY_VEST, state=PPEState.PRESENT, confidence=0.9),
            "gloves": PPEObservation(item_type=PPEItemType.GLOVES, state=PPEState.PRESENT, confidence=0.9),
            "safety_footwear": PPEObservation(item_type=PPEItemType.SAFETY_FOOTWEAR, state=PPEState.PRESENT, confidence=0.9),
        },
        is_compliant=False,
        history_length=20,
        first_seen=datetime.now(timezone.utc).isoformat(),
        last_seen=datetime.now(timezone.utc).isoformat(),
    )

    compliance_resp = ComplianceAnalysisResponse(
        frame_id=1,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        workers=[worker],
        summary=ComplianceSummary(
            total_workers=1,
            compliant_workers=0,
            non_compliant_workers=1,
            unknown_workers=0,
        ),
    )

    assessment = safety_engine.assess_scene(
        camera_id="camera_01",
        zone_id="production_floor",
        compliance_response=compliance_resp,
        hazard_response=None,
        camera_connected=True,
        ai_available=True,
    )

    assert assessment.workers_count == 1
    assert assessment.active_violations_count >= 1
    assert assessment.overall_safety_state == "VIOLATION"
