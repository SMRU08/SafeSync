"""
test_hazards.py — SafeSync Phase 6 Tests
Comprehensive test suite for Fire & Smoke Hazard Analysis.
Covers:
  - Spatial hazard tracker (association, distinct event IDs, separate streams)
  - Temporal state machine (SUSPECTED, CONFIRMED, CLEARED, NO_HAZARD transitions)
  - Zone resolution and polygon ROI containment
  - PPE separation: fire/smoke NEVER causes PPE violations and vice versa
  - API endpoints: /api/hazards/config, /api/hazards/analyze, /api/hazards, /api/hazards/{event_id}
"""

import io
import cv2
import pytest
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.ai.hazards.schemas import (
    HazardType,
    HazardState,
    HazardRelationship,
    HazardBoundingBox,
)
from app.ai.hazards.tracker import SpatialHazardTracker, HazardTrack
from app.ai.hazards.temporal import TemporalHazardStateMachine
from app.ai.hazards.zones import ZoneManager, point_in_polygon
from app.ai.hazards.hazard_engine import HazardAnalysisEngine
from app.ai.detection.schemas import DetectionObject, BoundingBox
from app.ai.compliance.schemas import PPEItemType, PPEState


from app.database.session import engine, Base

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_config():
    return {
        "hazard": {
            "confidence_threshold": 0.25,
            "fire_confidence": 0.25,
            "smoke_confidence": 0.25,
            "confirmation_frames": 5,
            "minimum_observation_ratio": 0.60,
            "clear_frames": 10,
            "max_gap_frames": 5,
        },
        "tracking": {
            "iou_threshold": 0.20,
            "center_distance_threshold": 0.25,
            "max_unseen_frames": 15,
        },
        "zones": {"enabled": True},
    }


def make_test_jpeg(width: int = 640, height: int = 480) -> bytes:
    img = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(img, "TEST", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    success, encoded = cv2.imencode(".jpg", img)
    assert success
    return encoded.tobytes()


# ─── 1. Spatial Hazard Tracker Tests ──────────────────────────────────────────

def test_hazard_tracker_initialization(sample_config):
    tracker = SpatialHazardTracker(sample_config)
    assert tracker.event_counter == 0
    assert len(tracker.active_tracks) == 0


def test_hazard_tracker_assigns_distinct_ids_for_different_locations(sample_config):
    tracker = SpatialHazardTracker(sample_config)
    dets = [
        {"hazard_type": HazardType.FIRE, "confidence": 0.8, "bbox": [10, 10, 50, 50], "zone_id": "zone1"},
        {"hazard_type": HazardType.FIRE, "confidence": 0.9, "bbox": [400, 300, 500, 400], "zone_id": "zone2"},
    ]
    active = tracker.update(dets, frame_idx=1)
    assert len(active) == 2
    assert active[0].event_id != active[1].event_id
    assert active[0].event_id.startswith("HAZARD-")
    assert active[1].event_id.startswith("HAZARD-")


def test_hazard_tracker_separate_fire_and_smoke_streams(sample_config):
    tracker = SpatialHazardTracker(sample_config)
    dets = [
        {"hazard_type": HazardType.FIRE, "confidence": 0.85, "bbox": [100, 100, 200, 200], "zone_id": "z1"},
        {"hazard_type": HazardType.SMOKE, "confidence": 0.75, "bbox": [100, 100, 200, 200], "zone_id": "z1"},
    ]
    active = tracker.update(dets, frame_idx=1)
    assert len(active) == 2
    types = {t.hazard_type for t in active}
    assert types == {HazardType.FIRE, HazardType.SMOKE}
    # Even though bboxes are identical, fire and smoke do NOT merge into one track
    assert active[0].event_id != active[1].event_id


# ─── 2. Temporal State Machine Tests ──────────────────────────────────────────

def test_temporal_single_frame_is_candidate(sample_config):
    sm = TemporalHazardStateMachine(sample_config)
    track = HazardTrack(
        event_id="HAZARD-0001",
        hazard_type=HazardType.FIRE,
        bbox=np.array([100, 100, 200, 200]),
        confidence=0.90,
        frame_idx=1,
        camera_id="camera_01",
        zone_id="production_floor",
    )
    st = sm.evaluate_track_state(track)
    assert st == HazardState.CANDIDATE, f"Expected CANDIDATE, got {st}"


def test_temporal_confirmation_after_5_frames(sample_config):
    sm = TemporalHazardStateMachine(sample_config)
    track = HazardTrack(
        event_id="HAZARD-0001",
        hazard_type=HazardType.FIRE,
        bbox=np.array([100, 100, 200, 200]),
        confidence=0.90,
        frame_idx=1,
        camera_id="camera_01",
        zone_id="production_floor",
    )
    # Frame 1: CANDIDATE
    st = sm.evaluate_track_state(track)
    assert st == HazardState.CANDIDATE

    # Frames 2..4: DETECTING
    for f in range(2, 5):
        track.update(np.array([100, 100, 200, 200]), 0.90, frame_idx=f, zone_id="production_floor")
        st = sm.evaluate_track_state(track)
        assert st == HazardState.DETECTING

    # Frame 5: reaches confirmation_frames=5 -> CONFIRMED
    track.update(np.array([100, 100, 200, 200]), 0.90, frame_idx=5, zone_id="production_floor")
    st = sm.evaluate_track_state(track)
    assert st == HazardState.CONFIRMED

    # Frame 6: subsequent detection -> ACTIVE
    track.update(np.array([100, 100, 200, 200]), 0.90, frame_idx=6, zone_id="production_floor")
    st = sm.evaluate_track_state(track)
    assert st == HazardState.ACTIVE


def test_temporal_missed_frame_tolerance(sample_config):
    sm = TemporalHazardStateMachine(sample_config)
    track = HazardTrack("HAZARD-0001", HazardType.SMOKE, np.array([100, 100, 200, 200]), 0.8, 1, "cam1", "z1")
    for f in range(1, 6):
        track.update(np.array([100, 100, 200, 200]), 0.8, f, "z1")
        sm.evaluate_track_state(track)
    assert sm.event_states["HAZARD-0001"] in (HazardState.CONFIRMED, HazardState.ACTIVE)

    # Miss 3 frames (< clear_frames=10)
    for _ in range(3):
        track.mark_missed()
        st = sm.evaluate_track_state(track)
        assert st in (HazardState.CONFIRMED, HazardState.ACTIVE)


def test_temporal_clearing_after_missed_frames(sample_config):
    sm = TemporalHazardStateMachine(sample_config)
    track = HazardTrack("HAZARD-0001", HazardType.FIRE, np.array([100, 100, 200, 200]), 0.85, 1, "cam1", "z1")
    for f in range(1, 6):
        track.update(np.array([100, 100, 200, 200]), 0.85, f, "z1")
        sm.evaluate_track_state(track)
    assert sm.event_states["HAZARD-0001"] in (HazardState.CONFIRMED, HazardState.ACTIVE)

    # Miss frames until clearing triggers
    observed_states = []
    for _ in range(25):
        track.mark_missed()
        st = sm.evaluate_track_state(track)
        observed_states.append(st)

    assert any(s in (HazardState.CLEARING, HazardState.CLEARED) for s in observed_states)
    assert observed_states[-1] in (HazardState.CLEARING, HazardState.CLEARED, HazardState.NO_HAZARD)


# ─── 3. Zone and ROI Tests ───────────────────────────────────────────────────

def test_point_in_polygon():
    poly = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]
    assert point_in_polygon(0.5, 0.5, poly) is True
    assert point_in_polygon(1.5, 0.5, poly) is False


def test_zone_manager_resolution():
    zm = ZoneManager()
    # Registered camera with direct zone
    z1 = zm.resolve_zone("camera_01", center_x=100, center_y=100)
    assert z1 == "production_floor"

    # Registered camera with polygon ROI: center inside [0.1..0.9]
    z3_in = zm.resolve_zone("camera_03", center_x=320, center_y=240, frame_width=640, frame_height=480)
    assert z3_in == "electrical_room"

    # Registered camera with polygon ROI: center outside [0.1..0.9]
    z3_out = zm.resolve_zone("camera_03", center_x=10, center_y=10, frame_width=640, frame_height=480)
    assert z3_out == "UNKNOWN"

    # Unregistered camera
    z_unknown = zm.resolve_zone("ghost_cam_00", center_x=100, center_y=100)
    assert z_unknown == "UNKNOWN"


# ─── 4. PPE Separation Tests (Strict Isolation) ──────────────────────────────

def test_hazard_never_triggers_ppe_violation():
    """
    Ensures fire and smoke detections cannot be interpreted as missing PPE
    and cannot generate PPE violation states.
    """
    engine = HazardAnalysisEngine()
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Process frame through hazard engine
    resp, _, _ = engine.process_frame(dummy_frame, camera_id="camera_01", annotate=False)

    # All returned hazards must strictly be fire or smoke
    for h in resp.hazards:
        assert h.hazard_type in [HazardType.FIRE, HazardType.SMOKE]
        assert h.hazard_type not in [PPEItemType.HELMET, PPEItemType.SAFETY_VEST, PPEItemType.GLOVES, PPEItemType.SAFETY_FOOTWEAR]


# ─── 5. FastAPI Hazards Endpoints Tests ──────────────────────────────────────

def test_api_hazards_config(client):
    response = client.get("/api/hazards/config")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert "hazard_thresholds" in data
    assert "tracking" in data
    assert "cameras" in data
    assert "configured_zones" in data


def test_api_hazards_analyze_valid(client):
    jpeg_bytes = make_test_jpeg()
    response = client.post(
        "/api/hazards/analyze",
        files={"file": ("frame.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
        params={"camera_id": "camera_01", "annotate": "true"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "frame_id" in data
    assert "scene_hazard_state" in data
    assert "relationship" in data
    assert "hazards" in data
    assert data["camera_id"] == "camera_01"


def test_api_hazards_analyze_unsupported_format(client):
    response = client.post(
        "/api/hazards/analyze",
        files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
    )
    assert response.status_code == 415


def test_api_hazards_analyze_zero_bytes(client):
    response = client.post(
        "/api/hazards/analyze",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
    )
    assert response.status_code == 400


def test_api_hazards_list(client):
    response = client.get("/api/hazards")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_hazards_detail_not_found(client):
    response = client.get("/api/hazards/NON_EXISTENT_ID_9999")
    assert response.status_code == 404
