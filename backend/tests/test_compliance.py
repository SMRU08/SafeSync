"""
test_compliance.py — SafeSync Phase 5 Test Suite
Automated pytest suite testing:
- Tracker initialization & track ID stability
- PPE spatial association across anatomical zones
- Temporal confirmation and tolerance thresholds
- UNKNOWN occlusion state handling
- Multi-worker non-interference
- FastAPI compliance endpoints (/api/compliance/config, /api/compliance/analyze)
"""

import io
import cv2
import pytest
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.ai.compliance.schemas import (
    PPEItemType,
    PPEState,
    OverallComplianceState,
    WorkerBoundingBox,
)
from app.ai.compliance.tracker import ByteTrack, KalmanBoxTracker
from app.ai.compliance.association import SpatialPPEAssociator
from app.ai.compliance.temporal import TemporalComplianceTracker
from app.ai.compliance.visualizer import ComplianceVisualizer

client = TestClient(app)


# ─── 1. Tracker Tests ─────────────────────────────────────────────────────────

def test_tracker_initialization():
    tracker = ByteTrack(track_high_thresh=0.3, track_low_thresh=0.1)
    assert tracker.frame_id == 0
    assert len(tracker.tracked_stracks) == 0


def test_tracker_assigns_stable_track_ids():
    tracker = ByteTrack(new_track_thresh=0.4)
    # Frame 1: Person at [100, 100, 200, 300]
    det_f1 = np.array([[100, 100, 200, 300, 0.9]])
    tracks_f1 = tracker.update(det_f1)
    assert len(tracks_f1) == 1
    tid_1 = tracks_f1[0][0]

    # Frame 2: Person moved slightly to [102, 101, 202, 301]
    det_f2 = np.array([[102, 101, 202, 301, 0.92]])
    tracks_f2 = tracker.update(det_f2)
    assert len(tracks_f2) == 1
    tid_2 = tracks_f2[0][0]

    # Track ID must remain identical across frames
    assert tid_1 == tid_2


def test_tracker_multiple_distinct_tracks():
    tracker = ByteTrack(new_track_thresh=0.4)
    # Two distinct people far apart
    dets = np.array([
        [50, 100, 150, 400, 0.88],
        [500, 100, 600, 400, 0.92],
    ])
    tracks = tracker.update(dets)
    assert len(tracks) == 2
    assert tracks[0][0] != tracks[1][0]


# ─── 2. Spatial Association Tests ─────────────────────────────────────────────

def test_helmet_association_upper_zone():
    associator = SpatialPPEAssociator()
    worker_box = np.array([100, 100, 200, 400])  # W=100, H=300
    # Helmet inside head zone [100, 85, 200, 190]
    helmet_box = [110, 95, 170, 150]
    ppe_dets = [{"class_name": "helmet", "bbox": helmet_box, "confidence": 0.85}]

    assoc, unassoc = associator.associate([(1, worker_box, 0.9)], ppe_dets)
    assert assoc[1]["helmet"] is not None
    assert assoc[1]["helmet"]["class_name"] == "helmet"
    assert len(unassoc) == 0


def test_helmet_not_associated_when_in_foot_region():
    associator = SpatialPPEAssociator()
    worker_box = np.array([100, 100, 200, 400])
    # A helmet falsely placed down near feet (y=350)
    helmet_feet = [120, 350, 180, 390]
    ppe_dets = [{"class_name": "helmet", "bbox": helmet_feet, "confidence": 0.85}]

    assoc, unassoc = associator.associate([(1, worker_box, 0.9)], ppe_dets)
    # Must NOT associate helmet to worker's feet
    assert assoc[1]["helmet"] is None
    assert len(unassoc) == 1


def test_vest_association_torso_zone():
    associator = SpatialPPEAssociator()
    worker_box = np.array([100, 100, 200, 400])
    vest_box = [110, 160, 190, 280]  # Torso zone
    ppe_dets = [{"class_name": "safety_vest", "bbox": vest_box, "confidence": 0.90}]

    assoc, unassoc = associator.associate([(1, worker_box, 0.9)], ppe_dets)
    assert assoc[1]["safety_vest"] is not None
    assert len(unassoc) == 0


def test_multi_worker_single_ppe_no_duplicate_assignment():
    associator = SpatialPPEAssociator()
    w1 = np.array([100, 100, 200, 400])
    w2 = np.array([180, 100, 280, 400])
    # Single helmet centered over w1
    single_helmet = [120, 95, 180, 145]
    ppe_dets = [{"class_name": "helmet", "bbox": single_helmet, "confidence": 0.9}]

    assoc, unassoc = associator.associate([(1, w1, 0.9), (2, w2, 0.9)], ppe_dets)
    # Assigned to worker 1, must NOT be duplicated to worker 2
    assert assoc[1]["helmet"] is not None
    assert assoc[2]["helmet"] is None
    assert len(unassoc) == 0


# ─── 3. Temporal Validation Tests ─────────────────────────────────────────────

def test_temporal_confirmation_frames_needed():
    temporal = TemporalComplianceTracker({"temporal": {"confirmation_frames": 3}})
    w_box = np.array([100, 100, 200, 400])
    assoc_present = {"helmet": {"class_name": "helmet", "bbox": [110, 95, 170, 145]}}

    # Frame 1: Seen 1 time -> UNKNOWN
    w1 = temporal.update_worker(1, w_box, 0.9, assoc_present, {item: False for item in PPEItemType})
    assert w1.ppe["helmet"] == PPEState.UNKNOWN

    # Frame 2: Seen 2 times -> UNKNOWN
    w2 = temporal.update_worker(1, w_box, 0.9, assoc_present, {item: False for item in PPEItemType})
    assert w2.ppe["helmet"] == PPEState.UNKNOWN

    # Frame 3: Seen 3 times -> PRESENT
    w3 = temporal.update_worker(1, w_box, 0.9, assoc_present, {item: False for item in PPEItemType})
    assert w3.ppe["helmet"] == PPEState.PRESENT


def test_temporal_missing_tolerance_before_absent():
    temporal = TemporalComplianceTracker({
        "temporal": {"confirmation_frames": 2, "missing_detection_tolerance": 4}
    })
    w_box = np.array([100, 100, 200, 400])
    assoc_present = {"helmet": {"class_name": "helmet", "bbox": [110, 95, 170, 145]}}
    assoc_empty = {"helmet": None}

    # First confirm helmet as PRESENT
    temporal.update_worker(1, w_box, 0.9, assoc_present, {item: False for item in PPEItemType})
    temporal.update_worker(1, w_box, 0.9, assoc_present, {item: False for item in PPEItemType})

    # Drop 1, 2, 3 frames -> Should tolerate and remain PRESENT
    for _ in range(3):
        w = temporal.update_worker(1, w_box, 0.9, assoc_empty, {item: False for item in PPEItemType})
        assert w.ppe["helmet"] == PPEState.PRESENT

    # Drop 4th frame -> tolerance exceeded, transitions to ABSENT
    w4 = temporal.update_worker(1, w_box, 0.9, assoc_empty, {item: False for item in PPEItemType})
    assert w4.ppe["helmet"] == PPEState.ABSENT


def test_occlusion_results_in_unknown_state():
    temporal = TemporalComplianceTracker()
    w_box = np.array([100, 5, 200, 300])  # Near top border
    assoc_empty = {"helmet": None}

    # Head is occluded (True)
    w = temporal.update_worker(
        1, w_box, 0.9, assoc_empty,
        {PPEItemType.HELMET: True, PPEItemType.SAFETY_VEST: False, PPEItemType.GLOVES: False, PPEItemType.SAFETY_FOOTWEAR: False}
    )
    assert w.ppe["helmet"] == PPEState.UNKNOWN


# ─── 4. Compliance API Endpoints Tests ────────────────────────────────────────

def test_api_compliance_config():
    response = client.get("/api/compliance/config")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert "helmet" in data["policy"]
    assert "tracking" in data
    assert "temporal" in data


def test_api_compliance_analyze_valid():
    img = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    _, encoded = cv2.imencode(".jpg", img)
    file_bytes = io.BytesIO(encoded.tobytes())

    response = client.post(
        "/api/compliance/analyze",
        files={"file": ("frame.jpg", file_bytes, "image/jpeg")},
        params={"confidence": 0.25, "annotate": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert "workers" in data
    assert "summary" in data
    assert "annotated_image_base64" in data


def test_api_compliance_analyze_unsupported_format():
    response = client.post(
        "/api/compliance/analyze",
        files={"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")}
    )
    assert response.status_code == 415


def test_api_compliance_analyze_zero_bytes():
    response = client.post(
        "/api/compliance/analyze",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")}
    )
    assert response.status_code == 400
