"""
evidence.py — SafeSync Phase 10 Step 9
FastAPI Router for Tamper-Evident Incident Evidence Archival and Secure Retrieval.
Includes strict path-traversal prevention, RBAC authorization, and SHA-256 integrity verification.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

try:
    from app.database.session import get_db
    from app.models.evidence import EvidenceItem
    from app.models.risk_alert import Incident
    from app.services.evidence_manager import EvidenceManager
    from app.security.auth import require_role
except ImportError:
    from backend.app.database.session import get_db
    from backend.app.models.evidence import EvidenceItem
    from backend.app.models.risk_alert import Incident
    from backend.app.services.evidence_manager import EvidenceManager
    from backend.app.security.auth import require_role

logger = logging.getLogger("evidence_api")
router = APIRouter(prefix="/api", tags=["Evidence Archival"])


@router.get("/incidents/{incident_id}/evidence", response_model=List[Dict[str, Any]])
def get_incident_evidence(
    incident_id: str = Path(..., description="UUID of parent incident"),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"])),
):
    """
    Lists all visual evidence artifacts associated with a safety incident.
    """
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found."
        )

    records = db.query(EvidenceItem).filter(EvidenceItem.incident_id == incident_id).order_by(EvidenceItem.id.asc()).all()

    return [
        {
            "evidence_id": r.evidence_id,
            "incident_id": r.incident_id,
            "camera_id": r.camera_id,
            "evidence_type": r.evidence_type,
            "file_size_bytes": r.file_size_bytes,
            "sha256_checksum": r.sha256_checksum,
            "created_at": r.created_at.isoformat(),
            "download_url": f"/api/evidence/{r.evidence_id}/download",
        }
        for r in records
    ]


@router.get("/evidence/storage/status")
def get_evidence_storage_status(
    current_user=Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"])),
):
    """
    Returns storage quota, current usage metrics, and retention policy for evidence archives.
    """
    mgr = EvidenceManager.get_instance()
    used_bytes = mgr.get_total_storage_usage()
    max_bytes = mgr.max_storage_bytes
    percent = round((used_bytes / max_bytes) * 100, 3) if max_bytes > 0 else 0.0

    return {
        "storage_dir": mgr.evidence_dir_rel,
        "total_bytes_used": used_bytes,
        "max_storage_bytes": max_bytes,
        "max_storage_gb": mgr.max_storage_gb,
        "quota_percent_used": percent,
        "retention_days": mgr.retention_days,
    }


@router.get("/evidence/{evidence_id}")
def get_evidence_detail(
    evidence_id: str = Path(..., description="Evidence UUID"),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"])),
):
    """
    Retrieves full metadata and live cryptographic SHA-256 integrity verification status for an evidence artifact.
    """
    mgr = EvidenceManager.get_instance()
    item = db.query(EvidenceItem).filter(EvidenceItem.evidence_id == evidence_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence artifact '{evidence_id}' not found."
        )

    verification = mgr.verify_evidence_integrity(evidence_id, db)
    return {
        "evidence_id": item.evidence_id,
        "incident_id": item.incident_id,
        "camera_id": item.camera_id,
        "evidence_type": item.evidence_type,
        "file_size_bytes": item.file_size_bytes,
        "sha256_checksum": item.sha256_checksum,
        "computed_sha256": verification.get("computed_sha256"),
        "verified": verification.get("verified", False),
        "tampered": verification.get("tampered", False),
        "created_at": item.created_at.isoformat(),
        "download_url": f"/api/evidence/{item.evidence_id}/download",
    }


@router.get("/evidence/{evidence_id}/download")
def download_evidence_file(
    evidence_id: str = Path(..., description="Evidence UUID"),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ADMIN", "OPERATOR", "VIEWER"])),
):
    """
    Streams the raw evidence snapshot file securely with strict path traversal defenses.
    """
    mgr = EvidenceManager.get_instance()
    item = db.query(EvidenceItem).filter(EvidenceItem.evidence_id == evidence_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence artifact '{evidence_id}' not found."
        )

    try:
        secure_path = mgr.resolve_secure_path(item.file_path)
    except PermissionError:
        logger.error("Path traversal blocked during download of evidence %s: %s", evidence_id, item.file_path)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: illegal path traversal attempt."
        )

    if not secure_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical evidence file not found on disk."
        )

    return FileResponse(
        path=str(secure_path),
        media_type="image/jpeg",
        filename=os.path.basename(str(secure_path)),
    )
