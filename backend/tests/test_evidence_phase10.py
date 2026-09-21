"""
test_evidence_phase10.py — RAKSHYA VISION Phase 10 Step 9
Unit & Integration Test Suite for Incident Evidence Archival, SHA-256 Integrity Verification,
Storage Quota Enforcement, Path Traversal Defense, and Fault Isolation.
"""

import os
import cv2
import json
import uuid
import pytest
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import get_db, Base, engine
from app.config import get_settings
from app.models.risk_alert import Incident, Alert
from app.models.evidence import EvidenceItem
from app.services.evidence_manager import EvidenceManager
from app.services.alert_engine import AlertEngine
from app.ai.risk.schemas import NormalizedSafetyEvent, EventType

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.close()


@pytest.fixture
def test_image():
    # 200x200 3-channel test frame
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    img[:, :] = (128, 64, 32)
    cv2.putText(img, "TEST FRAME", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return img


def test_evidence_capture_and_sha256(setup_db, test_image, tmp_path):
    """Verifies that evidence capture correctly saves JPEG, computes SHA-256, and stores in DB."""
    db = setup_db
    inc_id = f"inc-test-{uuid.uuid4().hex[:8]}"

    # Create dummy incident
    inc = Incident(
        incident_id=inc_id,
        status="OPEN",
        event_types="MISSING_HELMET",
        camera_id="cam_test_01",
        zone_id="ZONE_A",
        affected_tracks="[]",
        risk_score=75,
        risk_level="HIGH",
    )
    db.add(inc)
    db.commit()

    mgr = EvidenceManager.get_instance()
    evidence = mgr.capture_incident_evidence(
        incident_id=inc_id,
        camera_id="cam_test_01",
        frame=test_image,
        annotations={"box": [10, 10, 50, 50], "event": "MISSING_HELMET"},
        db=db,
        evidence_type="SNAPSHOT",
    )

    assert evidence is not None
    assert evidence.incident_id == inc_id
    assert evidence.camera_id == "cam_test_01"
    assert len(evidence.sha256_checksum) == 64
    assert evidence.file_size_bytes > 0

    # Verify physical file exists and matches recorded checksum
    real_path = mgr.resolve_secure_path(evidence.file_path)
    assert real_path.is_file()
    computed_hash = mgr.compute_sha256_file(real_path)
    assert computed_hash == evidence.sha256_checksum


def test_evidence_tamper_detection(setup_db, test_image):
    """Verifies that any modification to on-disk evidence fails SHA-256 integrity verification."""
    db = setup_db
    inc_id = f"inc-tamper-{uuid.uuid4().hex[:8]}"
    inc = Incident(
        incident_id=inc_id,
        status="OPEN",
        event_types="FIRE_DETECTED",
        camera_id="cam_tamper",
        zone_id="ZONE_B",
        affected_tracks="[]",
        risk_score=90,
        risk_level="CRITICAL",
    )
    db.add(inc)
    db.commit()

    mgr = EvidenceManager.get_instance()
    evidence = mgr.capture_incident_evidence(
        incident_id=inc_id,
        camera_id="cam_tamper",
        frame=test_image,
        db=db,
    )
    assert evidence is not None

    # Verification before tampering
    res_clean = mgr.verify_evidence_integrity(evidence.evidence_id, db)
    assert res_clean["verified"] is True
    assert res_clean["tampered"] is False

    # Tamper with file on disk by appending arbitrary bytes
    target_file = mgr.resolve_secure_path(evidence.file_path)
    with open(target_file, "ab") as f:
        f.write(b"CORRUPTED_TAMPER_INJECTION")

    # Verification after tampering
    res_tampered = mgr.verify_evidence_integrity(evidence.evidence_id, db)
    assert res_tampered["verified"] is False
    assert res_tampered["tampered"] is True
    assert res_tampered["computed_sha256"] != res_tampered["expected_sha256"]


def test_path_traversal_defense():
    """Verifies that malicious path traversal sequences are detected and forbidden."""
    mgr = EvidenceManager.get_instance()

    # Attempting to escape storage directory
    with pytest.raises(PermissionError):
        mgr.resolve_secure_path("../../../windows/system32/cmd.exe")

    with pytest.raises(PermissionError):
        mgr.resolve_secure_path("..\\..\\..\\secret.key")


def test_storage_quota_enforcement(setup_db, test_image):
    """Verifies that quota enforcement prunes oldest evidence belonging to resolved/dismissed incidents."""
    db = setup_db
    mgr = EvidenceManager.get_instance()

    # Create resolved incident with evidence
    inc_old = Incident(
        incident_id=f"inc-prune-{uuid.uuid4().hex[:8]}",
        status="RESOLVED",
        event_types="SMOKE_DETECTED",
        camera_id="cam_prune",
        zone_id="ZONE_C",
        affected_tracks="[]",
        risk_score=50,
        risk_level="MEDIUM",
    )
    db.add(inc_old)
    db.commit()

    ev_old = mgr.capture_incident_evidence(
        incident_id=inc_old.incident_id,
        camera_id="cam_prune",
        frame=test_image,
        db=db,
    )
    assert ev_old is not None

    # Temporarily set max_storage_bytes below current usage to trigger pruning
    original_max = mgr.max_storage_bytes
    try:
        mgr.max_storage_bytes = 10  # Very small threshold to force prune
        pruned = mgr.enforce_storage_quota(db=db)
        assert pruned >= 1
    finally:
        mgr.max_storage_bytes = original_max


def test_fault_isolation(setup_db):
    """Verifies that missing frames or disk write errors do not crash incident creation."""
    db = setup_db
    engine = AlertEngine()

    # Create a normalized event where camera has no active stream
    event = NormalizedSafetyEvent(
        event_id=str(uuid.uuid4()),
        camera_id="cam_offline_nonexistent",
        zone_id="ZONE_D",
        event_type=EventType.MISSING_HELMET,
        track_id=101,
        duration_seconds=5.0,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # Process event through alert engine
    alert, incident, action = engine.process_event(event, db=db)

    # Incident and alert MUST still be generated successfully despite lack of camera frame
    assert incident is not None
    assert incident.incident_id is not None
    assert action in ["CREATED", "COOLDOWN_SUPPRESSED", "ESCALATED"]


def test_evidence_api_endpoints(setup_db, test_image):
    """Tests GET /api/incidents/{id}/evidence, GET /api/evidence/{id}, and download endpoint."""
    db = setup_db
    inc_id = f"inc-api-{uuid.uuid4().hex[:8]}"
    inc = Incident(
        incident_id=inc_id,
        status="OPEN",
        event_types="FIRE_DETECTED",
        camera_id="cam_api",
        zone_id="ZONE_API",
        affected_tracks="[]",
        risk_score=85,
        risk_level="CRITICAL",
    )
    db.add(inc)
    db.commit()

    mgr = EvidenceManager.get_instance()
    ev = mgr.capture_incident_evidence(
        incident_id=inc_id,
        camera_id="cam_api",
        frame=test_image,
        db=db,
    )
    assert ev is not None

    # 1. List incident evidence
    resp = client.get(f"/api/incidents/{inc_id}/evidence")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["evidence_id"] == ev.evidence_id
    assert data[0]["camera_id"] == "cam_api"

    # 2. Get evidence detail with integrity check
    resp_detail = client.get(f"/api/evidence/{ev.evidence_id}")
    assert resp_detail.status_code == 200
    detail = resp_detail.json()
    assert detail["verified"] is True
    assert detail["tampered"] is False
    assert detail["sha256_checksum"] == ev.sha256_checksum

    # 3. Download evidence image
    resp_dl = client.get(f"/api/evidence/{ev.evidence_id}/download")
    assert resp_dl.status_code == 200
    assert resp_dl.headers["content-type"] == "image/jpeg"
    assert len(resp_dl.content) == ev.file_size_bytes

    # 4. Storage status
    resp_storage = client.get("/api/evidence/storage/status")
    assert resp_storage.status_code == 200
    storage_info = resp_storage.json()
    assert "total_bytes_used" in storage_info
    assert "max_storage_gb" in storage_info


def test_nonexistent_evidence_returns_404():
    """Verifies that requests for nonexistent incidents or evidence return 404."""
    resp_missing_inc = client.get("/api/incidents/nonexistent-incident-uuid/evidence")
    assert resp_missing_inc.status_code == 404

    resp_missing_ev = client.get("/api/evidence/nonexistent-evidence-uuid")
    assert resp_missing_ev.status_code == 404

    resp_missing_dl = client.get("/api/evidence/nonexistent-evidence-uuid/download")
    assert resp_missing_dl.status_code == 404


def test_cleanup_expired_evidence_retention(setup_db, test_image):
    """Verifies EvidenceManager.cleanup_expired_evidence removes physical files and DB rows."""
    db = setup_db
    mgr = EvidenceManager.get_instance()

    inc = Incident(
        incident_id=f"inc-ret-{uuid.uuid4().hex[:8]}",
        status="RESOLVED",
        event_types="SMOKE_DETECTED",
        camera_id="cam_ret",
        zone_id="ZONE_RET",
        affected_tracks="[]",
        risk_score=40,
        risk_level="MEDIUM",
    )
    db.add(inc)
    db.commit()

    ev = mgr.capture_incident_evidence(
        incident_id=inc.incident_id,
        camera_id="cam_ret",
        frame=test_image,
        db=db,
    )
    assert ev is not None
    real_file = mgr.resolve_secure_path(ev.file_path)
    assert real_file.is_file()

    # Manually backdate created_at to 40 days ago
    from datetime import timedelta
    ev.created_at = datetime.now(timezone.utc) - timedelta(days=40)
    db.commit()

    # Clean up evidence older than 30 days
    pruned = mgr.cleanup_expired_evidence(days=30, db=db)
    assert pruned >= 1
    assert not real_file.exists()
