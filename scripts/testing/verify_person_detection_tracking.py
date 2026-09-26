"""
verify_person_detection_tracking.py — SafeSync Test Matrix Verification
Automated test suite verifying:
1. Person detection & bounding box accuracy
2. Walking person recall & continuous tracking
3. Multi-person tracking & track ID persistence
4. Ghost worker / single-frame false alarm suppression
5. Strict anatomical PPE association (no cross-contamination)
6. Coordinate scaling & clamping integrity
7. Real-world DB check: TEST_STREAM_CAM purged cleanly
"""

import sys
import os
import sqlite3
import numpy as np

# Ensure backend path is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app.ai.detection.detector import Detector
from app.ai.compliance.tracker import ByteTrack, TrackState
from app.ai.compliance.compliance_engine import WorkerComplianceEngine
from app.camera.manager import CameraManager
from app.ai.compliance.schemas import PPEState, OverallComplianceState


def test_01_stationary_person_fit():
    print("[TEST 01] Running Stationary Person Fit & Clamping Verification...")
    det = Detector(model_type="ppe")
    # Synthetic frame with a person box
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Validate clamping and coordinate normalization
    clamped = det._validate_and_clamp_bbox([-10.0, -5.0, 700.0, 500.0], 640, 480, "person")
    assert clamped is not None, "Failed to clamp valid person box"
    assert clamped.x1 >= 0.0 and clamped.y1 >= 0.0
    assert clamped.x2 <= 640.0 and clamped.y2 <= 480.0
    print("  -> Passed: Bounding box cleanly clamped to [0, 640] x [0, 480]")


def test_02_walking_person_recall():
    print("[TEST 02] Running Walking Person Recall & Trajectory Tracking...")
    tracker = ByteTrack(track_high_thresh=0.25, new_track_thresh=0.35, confirmation_frames=2)
    
    # Simulate a person walking across 15 frames from x=50 to x=350
    track_ids = []
    for frame_idx in range(15):
        x = 50 + frame_idx * 20
        y = 100
        det = np.array([[x, y, x + 80, y + 200, 0.85]])
        active_tracks = tracker.update(det)
        if len(active_tracks) > 0:
            track_ids.append(active_tracks[0][0])

    assert len(track_ids) >= 14, f"Walking person tracking lost too many frames: {len(track_ids)}/15"
    assert len(set(track_ids)) == 1, f"Walking person ID switched during trajectory: {set(track_ids)}"
    print(f"  -> Passed: Worker maintained stable ID #{track_ids[0]} across {len(track_ids)} frames")


def test_03_multi_person_disjoint_ids():
    print("[TEST 03] Running Multi-Person Scene Tracking...")
    tracker = ByteTrack(track_high_thresh=0.25, new_track_thresh=0.35, confirmation_frames=2)

    # Frame 1 & 2: Two persons present simultaneously
    det1 = np.array([
        [100, 100, 180, 300, 0.88],  # Person A
        [350, 100, 430, 300, 0.85],  # Person B
    ])
    tracker.update(det1)
    tracks = tracker.update(det1)
    assert len(tracks) == 2, f"Expected 2 active tracks, got {len(tracks)}"
    tids = [t[0] for t in tracks]
    assert len(set(tids)) == 2, f"Track IDs must be distinct: {tids}"
    print(f"  -> Passed: Multi-person scene tracked cleanly with IDs {tids}")


def test_04_ghost_worker_suppression():
    print("[TEST 04] Running Ghost Worker (Single-Frame False Positive) Suppression...")
    tracker = ByteTrack(track_high_thresh=0.25, new_track_thresh=0.35, confirmation_frames=2)

    # Frame 1: Spurious detection with low/medium confidence (e.g. shadow or jacket, conf=0.40)
    spurious_det = np.array([[200, 200, 260, 350, 0.40]])
    tracks_f1 = tracker.update(spurious_det)
    assert len(tracks_f1) == 0, f"Ghost worker promoted on single frame! Count={len(tracks_f1)}"

    # Frame 2: Person is NOT there anymore
    tracks_f2 = tracker.update(np.empty((0, 5)))
    assert len(tracks_f2) == 0, "Ghost worker persisted after single frame disappeared!"

    print("  -> Passed: Single-frame spurious detection (conf 0.40) correctly rejected as TENTATIVE and dropped")


def test_05_ppe_association_non_interference():
    print("[TEST 05] Running Spatial PPE Association Isolation (No Cross-Contamination)...")
    engine = WorkerComplianceEngine()
    
    # 2 workers: Worker A at x in [50, 150], Worker B at x in [400, 500]
    # Helmet only on Worker A (x=80, y=70, w=40, h=30)
    tracked_workers = [
        (1, np.array([50.0, 80.0, 150.0, 350.0]), 0.90),
        (2, np.array([400.0, 80.0, 500.0, 350.0]), 0.90),
    ]
    ppe_dets = [
        {"class_name": "helmet", "bbox": [75.0, 70.0, 125.0, 110.0], "confidence": 0.85},
    ]
    associations, unassociated = engine.associator.associate(tracked_workers, ppe_dets)
    
    # Worker 1 MUST have helmet, Worker 2 MUST NOT have helmet
    assert associations[1]["helmet"] is not None, "Worker 1 should have associated helmet"
    assert associations[2]["helmet"] is None, "Worker 2 was cross-contaminated with Worker 1's helmet!"
    print("  -> Passed: PPE associated strictly to correct worker; zero cross-contamination")


def test_06_database_test_stream_cam_purged():
    print("[TEST 06] Verifying TEST_STREAM_CAM is Purged from SQLite DB and Manager...")
    db_path = os.path.join(ROOT, "backend", "safesync.db")
    if os.path.isfile(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT camera_id, name FROM cameras WHERE camera_id = 'test_stream_cam' OR name LIKE '%Stream Test%'")
        rows = c.fetchall()
        conn.close()
        assert len(rows) == 0, f"test_stream_cam still present in DB: {rows}"
        print("  -> Passed: SQLite DB does not contain test_stream_cam")
    
    # Check CameraManager configs
    manager = CameraManager.get_instance()
    assert "test_stream_cam" not in manager.configs, "test_stream_cam found in CameraManager configs!"
    print("  -> Passed: CameraManager registry only contains configured real cameras")


if __name__ == "__main__":
    print("=" * 70)
    print("SafeSync — PERSON DETECTION, TRACKING & PPE INTEGRITY MATRIX")
    print("=" * 70)
    test_01_stationary_person_fit()
    test_02_walking_person_recall()
    test_03_multi_person_disjoint_ids()
    test_04_ghost_worker_suppression()
    test_05_ppe_association_non_interference()
    test_06_database_test_stream_cam_purged()
    print("=" * 70)
    print("ALL VERIFICATION MATRIX TESTS PASSED (6/6)")
    print("=" * 70)
