"""
evidence_manager.py — RAKSHYA VISION Phase 10 Step 9
Core Service for Incident Visual Evidence Archival, SHA-256 Tamper Verification,
Storage Quota Enforcement, and Fault-Isolated Evidence Capture.
"""

import os
import cv2
import json
import uuid
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session

try:
    from app.config import get_settings
    from app.models.evidence import EvidenceItem
    from app.models.risk_alert import Incident
    from app.camera.manager import CameraManager
except ImportError:
    from backend.app.config import get_settings
    from backend.app.models.evidence import EvidenceItem
    from backend.app.models.risk_alert import Incident
    from backend.app.camera.manager import CameraManager

logger = logging.getLogger("evidence_manager")
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class EvidenceManager:
    """
    Singleton service managing visual evidence archival for safety incidents.
    Provides tamper-evident SHA-256 storage, quota management, and complete fault isolation.
    """
    _instance: Optional["EvidenceManager"] = None

    def __init__(self, base_dir: Optional[str] = None):
        settings = get_settings()
        self.evidence_dir_rel = base_dir or settings.EVIDENCE_STORAGE_DIR
        self.storage_root = (PROJECT_ROOT / self.evidence_dir_rel).resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.max_storage_gb = getattr(settings, "MAX_EVIDENCE_STORAGE_GB", 20.0)
        self.max_storage_bytes = int(self.max_storage_gb * 1024 * 1024 * 1024)
        self.retention_days = getattr(settings, "EVIDENCE_RETENTION_DAYS", 30)

    @classmethod
    def get_instance(cls, base_dir: Optional[str] = None) -> "EvidenceManager":
        if cls._instance is None:
            cls._instance = EvidenceManager(base_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    def resolve_secure_path(self, relative_path: str) -> Path:
        """
        Safely resolves a relative evidence file path, strictly defending against path traversal.
        Raises PermissionError if path resolves outside the evidence storage root.
        """
        cleaned = relative_path.replace("\\", "/").strip("/")
        # If path begins with evidence_dir_rel, strip it so it resolves relative to storage_root
        prefix = self.evidence_dir_rel.replace("\\", "/").strip("/")
        if cleaned.startswith(prefix + "/"):
            cleaned = cleaned[len(prefix) + 1:]
        elif cleaned == prefix:
            cleaned = ""

        resolved = (self.storage_root / cleaned).resolve()

        # Check bounds: resolved path must start with storage_root
        try:
            resolved.relative_to(self.storage_root)
        except ValueError:
            logger.warning("Path traversal attempt detected: %s resolves to %s", relative_path, resolved)
            raise PermissionError("Access denied: path traversal attempt detected.")

        return resolved

    def compute_sha256_bytes(self, data: bytes) -> str:
        """Computes SHA-256 hexadecimal digest for raw binary data."""
        return hashlib.sha256(data).hexdigest()

    def compute_sha256_file(self, file_path: Path) -> str:
        """Computes SHA-256 hexadecimal digest for an on-disk file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def capture_incident_evidence(
        self,
        incident_id: str,
        camera_id: str,
        frame: Optional[np.ndarray] = None,
        annotations: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
        evidence_type: str = "SNAPSHOT",
    ) -> Optional[EvidenceItem]:
        """
        Captures and persists visual evidence for an incident.
        Fault-isolated: failure to write or missing frame will NEVER crash the caller.
        """
        try:
            target_frame = frame
            # If no frame supplied, attempt to fetch latest frame from camera manager
            if target_frame is None:
                try:
                    cam_mgr = CameraManager.get_instance()
                    target_frame, _ = cam_mgr.get_latest_frame(camera_id)
                except Exception as cam_err:
                    logger.debug("Could not retrieve camera frame for %s: %s", camera_id, cam_err)

            if target_frame is None or not isinstance(target_frame, np.ndarray) or target_frame.size == 0:
                logger.info("No valid video frame available for camera %s; skipping evidence snapshot.", camera_id)
                return None

            now = datetime.now(timezone.utc)
            year_str = now.strftime("%Y")
            month_str = now.strftime("%m")
            day_str = now.strftime("%d")

            # Structured directory: outputs/evidence/YYYY/MM/DD/{camera_id}/
            folder = self.storage_root / year_str / month_str / day_str / camera_id
            folder.mkdir(parents=True, exist_ok=True)

            evidence_id = str(uuid.uuid4())
            filename = f"{incident_id}_{evidence_id[:8]}_{int(now.timestamp())}.jpg"
            target_file = folder / filename

            # Encode frame to JPEG
            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
            success, buffer = cv2.imencode(".jpg", target_frame, encode_params)
            if not success or buffer is None:
                logger.error("Failed to JPEG encode frame for incident %s", incident_id)
                return None

            raw_bytes = buffer.tobytes()
            file_size = len(raw_bytes)
            checksum = self.compute_sha256_bytes(raw_bytes)

            # Write file to disk
            with open(target_file, "wb") as f:
                f.write(raw_bytes)

            # Relative path from project root
            rel_path = str(target_file.relative_to(PROJECT_ROOT)).replace("\\", "/")

            evidence_item = None
            if db is not None:
                evidence_item = EvidenceItem(
                    evidence_id=evidence_id,
                    incident_id=incident_id,
                    camera_id=camera_id,
                    evidence_type=evidence_type,
                    file_path=rel_path,
                    file_size_bytes=file_size,
                    sha256_checksum=checksum,
                    metadata_json=json.dumps(annotations) if annotations else None,
                    created_at=now,
                )
                db.add(evidence_item)
                db.commit()
                db.refresh(evidence_item)
                logger.info(
                    "Archived evidence %s for incident %s (camera=%s, size=%d bytes, sha256=%s...)",
                    evidence_id, incident_id, camera_id, file_size, checksum[:10]
                )

                # Check storage quota asynchronously/safely
                self.enforce_storage_quota(db=db)

            return evidence_item

        except Exception as err:
            logger.error("Fault-isolated error capturing evidence for incident %s: %s", incident_id, err)
            return None

    def verify_evidence_integrity(self, evidence_id: str, db: Session) -> Dict[str, Any]:
        """
        Verifies on-disk file checksum against the recorded SHA-256 digest in the database.
        Returns detailed verification status to expose any tampering.
        """
        item = db.query(EvidenceItem).filter(EvidenceItem.evidence_id == evidence_id).first()
        if not item:
            return {
                "evidence_id": evidence_id,
                "verified": False,
                "error": "Evidence record not found in database",
            }

        try:
            file_path = self.resolve_secure_path(item.file_path)
            if not file_path.is_file():
                return {
                    "evidence_id": item.evidence_id,
                    "incident_id": item.incident_id,
                    "verified": False,
                    "error": "Physical evidence file missing on disk",
                }

            live_hash = self.compute_sha256_file(file_path)
            is_valid = (live_hash.lower() == item.sha256_checksum.lower())

            return {
                "evidence_id": item.evidence_id,
                "incident_id": item.incident_id,
                "camera_id": item.camera_id,
                "file_path": item.file_path,
                "file_size_bytes": item.file_size_bytes,
                "expected_sha256": item.sha256_checksum,
                "computed_sha256": live_hash,
                "verified": is_valid,
                "tampered": not is_valid,
                "created_at": item.created_at.isoformat(),
            }
        except PermissionError as perm_err:
            return {
                "evidence_id": item.evidence_id,
                "verified": False,
                "error": str(perm_err),
            }
        except Exception as e:
            return {
                "evidence_id": item.evidence_id,
                "verified": False,
                "error": f"Verification failed: {e}",
            }

    def get_total_storage_usage(self) -> int:
        """Returns total bytes used in evidence storage directory."""
        total_bytes = 0
        if self.storage_root.exists():
            for p in self.storage_root.rglob("*"):
                if p.is_file():
                    total_bytes += p.stat().st_size
        return total_bytes

    def enforce_storage_quota(self, db: Optional[Session] = None) -> int:
        """
        Checks total storage against max_storage_bytes.
        If exceeded, deletes oldest evidence files linked to RESOLVED or DISMISSED incidents.
        Returns number of pruned evidence files.
        """
        current_bytes = self.get_total_storage_usage()
        if current_bytes <= self.max_storage_bytes:
            return 0

        logger.warning(
            "Evidence storage usage (%d bytes) exceeds quota (%d bytes). Initiating pruning...",
            current_bytes, self.max_storage_bytes
        )

        pruned_count = 0
        if db is not None:
            # Candidate evidence items: oldest first, belonging to resolved/dismissed incidents
            candidates = (
                db.query(EvidenceItem)
                .join(Incident, EvidenceItem.incident_id == Incident.incident_id)
                .filter(Incident.status.in_(["RESOLVED", "DISMISSED"]))
                .order_by(EvidenceItem.created_at.asc())
                .limit(50)
                .all()
            )

            for item in candidates:
                try:
                    target_file = self.resolve_secure_path(item.file_path)
                    if target_file.is_file():
                        target_file.unlink()
                    db.delete(item)
                    db.commit()
                    pruned_count += 1
                except Exception as del_err:
                    logger.error("Failed to prune evidence %s: %s", item.evidence_id, del_err)

                # Re-check quota
                if self.get_total_storage_usage() <= self.max_storage_bytes:
                    break

        logger.info("Storage quota enforcement pruned %d old evidence items.", pruned_count)
        return pruned_count

    def cleanup_expired_evidence(self, days: Optional[int] = None, db: Optional[Session] = None) -> int:
        """
        Purges evidence items older than retention threshold (default: settings.EVIDENCE_RETENTION_DAYS).
        Only purges items linked to RESOLVED/DISMISSED incidents to protect active investigation integrity.
        """
        threshold_days = days or self.retention_days
        cutoff = datetime.now(timezone.utc) - timedelta(days=threshold_days)

        pruned_count = 0
        if db is not None:
            expired_items = (
                db.query(EvidenceItem)
                .join(Incident, EvidenceItem.incident_id == Incident.incident_id)
                .filter(
                    EvidenceItem.created_at < cutoff,
                    Incident.status.in_(["RESOLVED", "DISMISSED"])
                )
                .all()
            )

            for item in expired_items:
                try:
                    target_file = self.resolve_secure_path(item.file_path)
                    if target_file.is_file():
                        target_file.unlink()
                    db.delete(item)
                    pruned_count += 1
                except Exception as exp_err:
                    logger.error("Error deleting expired evidence file %s: %s", item.file_path, exp_err)

            db.commit()

        logger.info("Purged %d expired evidence artifacts older than %d days.", pruned_count, threshold_days)
        return pruned_count
