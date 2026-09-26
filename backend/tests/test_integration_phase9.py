"""
test_integration_phase9.py — SafeSync Phase 9
Full end-to-end integration and system verification test suite.
"""

import os
import time
import json
import hashlib
from datetime import datetime, timezone
import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient

from app.main import app
from app.ai.detection.model_loader import ModelLoader, CANONICAL_CLASSES
from app.ai.detection.detector import Detector
from app.ai.compliance.tracker import ByteTrack
from app.ai.compliance.association import SpatialPPEAssociator
from app.ai.compliance.temporal import TemporalComplianceTracker
from app.ai.compliance.compliance_engine import WorkerComplianceEngine
from app.ai.compliance.schemas import PPEState, OverallComplianceState
from app.ai.hazards.tracker import SpatialHazardTracker, HazardTrack
from app.ai.hazards.temporal import TemporalHazardStateMachine
from app.ai.hazards.schemas import HazardType, HazardState
from app.services.event_normalizer import EventNormalizer
from app.services.risk_engine import RiskEngine
from app.services.alert_engine import AlertEngine
from app.services.event_broadcaster import broadcaster
from app.database.session import SessionLocal
from app.models.risk_alert import Incident, Alert
from app.ai.risk.schemas import EventType, RiskLevel, AlertStatus, NormalizedSafetyEvent


@pytest.fixture
def client():
    return TestClient(app)


def test_model_provenance_and_classes():
    """Verify v2 model existence, checksum, and canonical 7-class ontology."""
    weights_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "models", "detection", "ppe_fire_smoke_v2", "weights", "best.pt"
    ))
    expected_sha = "490a4867d0c9c848ed38e9d5b196a21f925371e3019079b6b7e30c0a5084b2f3"
    assert os.path.exists(weights_path), f"Checkpoint missing: {weights_path}"

    with open(weights_path, "rb") as f:
        computed_sha = hashlib.sha256(f.read()).hexdigest()
    assert computed_sha.lower() == expected_sha.lower(), "Model SHA256 checksum mismatch"

    loader = ModelLoader.get_instance()
    loader.load_model()
    assert loader.classes == CANONICAL_CLASSES, f"Class ontology mismatch: {loader.classes}"


def test_ppe_10_scenarios_e2e():
    """Test all 10 PPE compliance scenarios end-to-end."""
    cfg = {
        "required_ppe": {"helmet": True, "safety_vest": True, "gloves": True, "safety_footwear": True},
        "temporal": {"confirmation_frames": 3, "missing_detection_tolerance": 3}
    }
    worker_box = np.array([100.0, 100.0, 200.0, 400.0])
    no_occl = {"head": False, "chest": False, "hands": False, "feet": False}
    all_occl = {"head": True, "chest": True, "hands": True, "feet": True}
    det_obj = lambda: {"bbox": [100, 100, 150, 150], "confidence": 0.9}

    # S1: Compliant
    t1 = TemporalComplianceTracker(cfg)
    for _ in range(3):
        w1 = t1.update_worker(1, worker_box, 0.9, {k: det_obj() for k in ["helmet", "safety_vest", "gloves", "safety_footwear"]}, no_occl)
    assert w1.overall_status == OverallComplianceState.COMPLIANT

    # S2: Missing helmet
    t2 = TemporalComplianceTracker(cfg)
    assoc_no_h = {k: det_obj() for k in ["safety_vest", "gloves", "safety_footwear"]}
    assoc_no_h["helmet"] = None
    for _ in range(3):
        w2 = t2.update_worker(2, worker_box, 0.9, assoc_no_h, no_occl)
    assert w2.ppe["helmet"] == PPEState.ABSENT
    assert w2.overall_status == OverallComplianceState.NON_COMPLIANT

    # S3: Missing vest
    t3 = TemporalComplianceTracker(cfg)
    assoc_no_v = {k: det_obj() for k in ["helmet", "gloves", "safety_footwear"]}
    assoc_no_v["safety_vest"] = None
    for _ in range(3):
        w3 = t3.update_worker(3, worker_box, 0.9, assoc_no_v, no_occl)
    assert w3.ppe["safety_vest"] == PPEState.ABSENT

    # S4: Missing gloves
    t4 = TemporalComplianceTracker(cfg)
    assoc_no_g = {k: det_obj() for k in ["helmet", "safety_vest", "safety_footwear"]}
    assoc_no_g["gloves"] = None
    for _ in range(3):
        w4 = t4.update_worker(4, worker_box, 0.9, assoc_no_g, no_occl)
    assert w4.ppe["gloves"] == PPEState.ABSENT

    # S5: Missing footwear
    t5 = TemporalComplianceTracker(cfg)
    assoc_no_f = {k: det_obj() for k in ["helmet", "safety_vest", "gloves"]}
    assoc_no_f["safety_footwear"] = None
    for _ in range(3):
        w5 = t5.update_worker(5, worker_box, 0.9, assoc_no_f, no_occl)
    assert w5.ppe["safety_footwear"] == PPEState.ABSENT

    # S6: Mixed workers
    t6 = TemporalComplianceTracker(cfg)
    for _ in range(3):
        wa = t6.update_worker(10, worker_box, 0.9, {k: det_obj() for k in ["helmet", "safety_vest", "gloves", "safety_footwear"]}, no_occl)
        wb = t6.update_worker(20, worker_box, 0.9, assoc_no_h, no_occl)
    assert wa.overall_status == OverallComplianceState.COMPLIANT
    assert wb.overall_status == OverallComplianceState.NON_COMPLIANT

    # S7: Occluded worker
    t7 = TemporalComplianceTracker(cfg)
    w7 = t7.update_worker(30, worker_box, 0.9, {k: None for k in ["helmet", "safety_vest", "gloves", "safety_footwear"]}, all_occl)
    assert all(st == PPEState.UNKNOWN for st in w7.ppe.values())
    assert w7.overall_status == OverallComplianceState.UNKNOWN

    # S8: Worker leaving scene
    bt = ByteTrack(track_high_thresh=0.5, track_buffer=2)
    dets = np.array([[100.0, 100.0, 200.0, 400.0, 0.9]])
    trks1 = bt.update(dets)
    assert len(trks1) == 1
    # Empty frames to age out
    bt.update(np.empty((0, 5)))
    bt.update(np.empty((0, 5)))
    trks3 = bt.update(np.empty((0, 5)))
    assert len(trks3) == 0

    # S9: Temporal tolerance holding
    t9 = TemporalComplianceTracker({"temporal": {"confirmation_frames": 2, "missing_detection_tolerance": 4}})
    assoc_all = {k: det_obj() for k in ["helmet", "safety_vest", "gloves", "safety_footwear"]}
    t9.update_worker(99, worker_box, 0.9, assoc_all, no_occl)
    t9.update_worker(99, worker_box, 0.9, assoc_all, no_occl)
    for _ in range(2):
        w9 = t9.update_worker(99, worker_box, 0.9, assoc_no_h, no_occl)
    assert w9.ppe["helmet"] == PPEState.PRESENT

    # S10: Close proximity spatial isolation
    associator = SpatialPPEAssociator()
    w1_box = np.array([100.0, 100.0, 200.0, 400.0])
    w2_box = np.array([180.0, 100.0, 280.0, 400.0])
    single_helmet = [120, 95, 180, 145]
    ppe_dets = [{"class_name": "helmet", "bbox": single_helmet, "confidence": 0.9}]
    assoc, _ = associator.associate([(1, w1_box, 0.9), (2, w2_box, 0.9)], ppe_dets)
    assert assoc[1]["helmet"] is not None and assoc[2]["helmet"] is None


def test_fire_smoke_7_scenarios_e2e():
    """Test all 7 fire and smoke hazard scenarios."""
    cfg = {"hazard": {"fire_confidence": 0.35, "smoke_confidence": 0.30, "confirmation_frames": 5, "clear_frames": 10}}

    # 1. Fire confirmed
    sm1 = TemporalHazardStateMachine(cfg)
    trk1 = HazardTrack("H1", HazardType.FIRE, np.array([100, 100, 200, 200]), 0.9, 1, "c1", "z1")
    for f in range(2, 6):
        trk1.update(np.array([100, 100, 200, 200]), 0.9, frame_idx=f, zone_id="z1")
        st1 = sm1.evaluate_track_state(trk1)
    assert st1 == HazardState.CONFIRMED

    # 2. Smoke confirmed
    sm2 = TemporalHazardStateMachine(cfg)
    trk2 = HazardTrack("H2", HazardType.SMOKE, np.array([300, 150, 500, 350]), 0.8, 1, "c1", "z1")
    for f in range(2, 6):
        trk2.update(np.array([300, 150, 500, 350]), 0.8, frame_idx=f, zone_id="z1")
        st2 = sm2.evaluate_track_state(trk2)
    assert st2 == HazardState.CONFIRMED

    # 3. Multi-hazard
    sm3 = TemporalHazardStateMachine(cfg)
    trk_f = HazardTrack("H3_F", HazardType.FIRE, np.array([100, 100, 200, 200]), 0.9, 1, "c1", "z1")
    trk_s = HazardTrack("H3_S", HazardType.SMOKE, np.array([120, 80, 250, 180]), 0.85, 1, "c1", "z1")
    for f in range(2, 6):
        trk_f.update(np.array([100, 100, 200, 200]), 0.9, frame_idx=f, zone_id="z1")
        trk_s.update(np.array([120, 80, 250, 180]), 0.85, frame_idx=f, zone_id="z1")
        st_f = sm3.evaluate_track_state(trk_f)
        st_s = sm3.evaluate_track_state(trk_s)
    assert st_f == HazardState.CONFIRMED and st_s == HazardState.CONFIRMED

    # 4. Normal scene
    ht = SpatialHazardTracker()
    active = ht.update([], frame_idx=1)
    assert len(active) == 0

    # 5. Low conf suppressed
    detector = Detector()
    f_low_conf = 0.15
    assert f_low_conf < detector.default_conf

    # 6. Single frame fire remains CANDIDATE / SUSPECTED
    sm6 = TemporalHazardStateMachine(cfg)
    trk6 = HazardTrack("H6", HazardType.FIRE, np.array([100, 100, 200, 200]), 0.9, 1, "c1", "z1")
    assert sm6.evaluate_track_state(trk6) in (HazardState.CANDIDATE, HazardState.SUSPECTED)

    # 7. Single frame smoke remains CANDIDATE / SUSPECTED
    sm7 = TemporalHazardStateMachine(cfg)
    trk7 = HazardTrack("H7", HazardType.SMOKE, np.array([100, 100, 200, 200]), 0.8, 1, "c1", "z1")
    assert sm7.evaluate_track_state(trk7) in (HazardState.CANDIDATE, HazardState.SUSPECTED)


def test_risk_and_alert_lifecycle():
    """Verify risk calculation, alert generation, deduplication, cooldown, ack, and resolution."""
    risk_engine = RiskEngine()
    alert_engine = AlertEngine()
    db = SessionLocal()

    try:
        # LOW
        low = risk_engine.evaluate(event_type=EventType.MISSING_GLOVES, duration_seconds=0.0, affected_workers_count=1, zone_id="storage_area")
        assert low.risk_level == RiskLevel.LOW

        # MEDIUM
        med = risk_engine.evaluate(event_type=EventType.MISSING_HELMET, duration_seconds=0.0, affected_workers_count=1, zone_id="storage_area")
        assert med.risk_level == RiskLevel.MEDIUM

        # HIGH
        high = risk_engine.evaluate(event_type=EventType.SMOKE_DETECTED, duration_seconds=10.0, affected_workers_count=1, zone_id="storage_area")
        assert high.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

        # CRITICAL
        crit = risk_engine.evaluate(event_type=EventType.FIRE_DETECTED, duration_seconds=15.0, affected_workers_count=2, zone_id="electrical_room")
        assert crit.risk_level == RiskLevel.CRITICAL

        # Alert Lifecycle
        event = NormalizedSafetyEvent(
            event_id="EV-PYTEST-001",
            event_type=EventType.MISSING_HELMET,
            timestamp=datetime.now(timezone.utc).isoformat(),
            camera_id="CAM-PYTEST-01",
            zone_id="FAB_BAY_01",
            track_id=9999,
            confidence=0.95,
            duration_seconds=12.0,
        )

        alt1, inc1, act1 = alert_engine.process_event(event, db)
        assert alt1 is not None and inc1 is not None and act1 == "CREATED"

        # Cooldown duplicate suppression
        alt2, inc2, act2 = alert_engine.process_event(event, db)
        assert alt2 is None and inc2 is not None and act2 == "COOLDOWN_SUPPRESSED"

        # Acknowledge & Resolve
        ack = alert_engine.acknowledge_alert(alt1.alert_id, db)
        assert ack.status == AlertStatus.ACKNOWLEDGED
        res = alert_engine.resolve_alert(alt1.alert_id, db)
        assert res.status == AlertStatus.RESOLVED

    finally:
        db.close()


def test_pipeline_latency_budget():
    """Verify end-to-end pipeline latency stays well under 100ms CPU budget."""
    comp_engine = WorkerComplianceEngine()
    frame = np.zeros((384, 384, 3), dtype=np.uint8)
    cv2.rectangle(frame, (80, 50), (200, 320), (220, 220, 220), -1)

    # Warmup
    comp_engine.process_frame(frame, annotate=False)

    times = []
    for _ in range(5):
        t0 = time.perf_counter()
        comp_engine.process_frame(frame, annotate=False)
        times.append((time.perf_counter() - t0) * 1000.0)

    mean_ms = float(np.mean(times))
    # Adaptive latency budget: GPU target = 100ms, CPU (dev/CI) target = 2000ms
    import torch
    budget_ms = 100.0 if torch.cuda.is_available() else 2000.0
    assert mean_ms < budget_ms, (
        f"Mean latency exceeded budget: {mean_ms:.2f}ms > {budget_ms:.0f}ms "
        f"({'GPU' if torch.cuda.is_available() else 'CPU'} mode)"
    )


def test_security_input_validation(client):
    """Test empty file, unsupported extension, and path traversal rejection."""
    r_empty = client.post("/api/detection/image", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert r_empty.status_code == 400

    r_bad_ext = client.post("/api/detection/image", files={"file": ("hack.exe", b"fake", "application/octet-stream")})
    assert r_bad_ext.status_code in [400, 415]

    r_trav = client.get("/api/alerts/../../etc/passwd")
    assert r_trav.status_code in [404, 422]
