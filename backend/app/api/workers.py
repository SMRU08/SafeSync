"""
workers.py — SafeSync Facial Recognition & Attendance API
Endpoints for worker registration, face enrollment, attendance tracking.
"""

import json
import logging
from datetime import datetime, date, timezone, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database.session import get_db
from app.models.worker_face import RegisteredWorker, AttendanceLog
from app.services.face_recognition_service import FaceRecognitionService

logger = logging.getLogger("workers_api")
router = APIRouter(prefix="/api/workers", tags=["workers"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class WorkerRegistrationRequest(BaseModel):
    name: str
    job_role: str
    origin: str
    face_image_b64: str  # Base64 encoded image with or without data URL prefix


class WorkerResponse(BaseModel):
    worker_id: str
    name: str
    job_role: str
    origin: str
    registered_at: str
    is_active: bool
    face_image_path: Optional[str] = None


class AttendanceLogResponse(BaseModel):
    id: int
    worker_id: str
    worker_name: Optional[str] = None
    date: str
    check_in_time: str
    camera_id: str
    camera_name: str


class FaceMatchRequest(BaseModel):
    face_image_b64: str
    camera_id: str = "unknown"
    camera_name: str = "Unknown Camera"


# ---------------------------------------------------------------------------
# Worker registration
# ---------------------------------------------------------------------------


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_worker(
    req: WorkerRegistrationRequest, db: Session = Depends(get_db)
):
    """Register a new worker with facial biometric enrollment."""
    svc = FaceRecognitionService.get_instance()

    # Extract face embedding from the provided image
    embedding = svc.extract_embedding_from_base64(req.face_image_b64)
    if embedding is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No face detected in the provided image. "
                "Please use a clear frontal face photo."
            ),
        )

    # Generate a unique worker_id (W0001, W0002, …)
    existing_count = db.query(RegisteredWorker).count()
    worker_id = f"W{existing_count + 1:04d}"
    while (
        db.query(RegisteredWorker)
        .filter(RegisteredWorker.worker_id == worker_id)
        .first()
    ):
        existing_count += 1
        worker_id = f"W{existing_count + 1:04d}"

    # Persist the face image to disk
    image_path = svc.save_face_image(worker_id, req.face_image_b64)

    # Create database record
    worker = RegisteredWorker(
        worker_id=worker_id,
        name=req.name,
        job_role=req.job_role,
        origin=req.origin,
        face_embedding=json.dumps(embedding),
        face_image_path=image_path,
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)

    logger.info("Registered new worker: %s (%s)", worker_id, req.name)
    return {
        "success": True,
        "worker_id": worker_id,
        "name": req.name,
        "job_role": req.job_role,
        "origin": req.origin,
        "message": (
            f"Worker {req.name} enrolled successfully with ID {worker_id}"
        ),
        "face_recognition_active": svc.is_available(),
    }


# ---------------------------------------------------------------------------
# Worker listing & deactivation
# ---------------------------------------------------------------------------


@router.get("/", response_model=List[WorkerResponse])
def list_workers(
    active_only: bool = True, db: Session = Depends(get_db)
):
    """List all registered workers."""
    q = db.query(RegisteredWorker)
    if active_only:
        q = q.filter(RegisteredWorker.is_active == True)  # noqa: E712
    workers = q.order_by(RegisteredWorker.registered_at.desc()).all()

    return [
        WorkerResponse(
            worker_id=w.worker_id,
            name=w.name,
            job_role=w.job_role,
            origin=w.origin,
            registered_at=w.registered_at.isoformat(),
            is_active=w.is_active,
            face_image_path=w.face_image_path,
        )
        for w in workers
    ]


@router.delete("/{worker_id}", status_code=status.HTTP_200_OK)
def deactivate_worker(worker_id: str, db: Session = Depends(get_db)):
    """Deactivate (soft-delete) a registered worker."""
    worker = (
        db.query(RegisteredWorker)
        .filter(RegisteredWorker.worker_id == worker_id)
        .first()
    )
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    worker.is_active = False
    db.commit()
    return {"success": True, "message": f"Worker {worker_id} deactivated"}


# ---------------------------------------------------------------------------
# Face matching & attendance logging
# ---------------------------------------------------------------------------


@router.post("/match-face")
def match_face_and_log_attendance(
    req: FaceMatchRequest, db: Session = Depends(get_db)
):
    """Match a face against the database and log attendance if matched."""
    svc = FaceRecognitionService.get_instance()

    # Extract embedding from query image
    query_embedding = svc.extract_embedding_from_base64(req.face_image_b64)
    if query_embedding is None:
        return {"matched": False, "reason": "No face detected in image"}

    # Load all active worker embeddings
    workers = (
        db.query(RegisteredWorker)
        .filter(RegisteredWorker.is_active == True)  # noqa: E712
        .all()
    )
    if not workers:
        return {
            "matched": False,
            "reason": "No registered workers in database",
        }

    known_embeddings: List[tuple] = []
    for w in workers:
        try:
            emb = json.loads(w.face_embedding) if w.face_embedding else None
            if emb:
                known_embeddings.append((w.worker_id, emb))
        except Exception:
            continue

    if not known_embeddings:
        return {"matched": False, "reason": "No embeddings available"}

    # Perform matching
    match_result = svc.match_face(query_embedding, known_embeddings)
    if match_result is None:
        return {"matched": False, "reason": "No matching worker found"}

    matched_worker_id, distance = match_result
    worker = (
        db.query(RegisteredWorker)
        .filter(RegisteredWorker.worker_id == matched_worker_id)
        .first()
    )

    # Log attendance — deduplicate: once per calendar day per worker
    today = date.today()
    existing_log = (
        db.query(AttendanceLog)
        .filter(
            and_(
                AttendanceLog.worker_id == matched_worker_id,
                AttendanceLog.date == today,
            )
        )
        .first()
    )

    attendance_logged = False
    if not existing_log:
        log = AttendanceLog(
            worker_id=matched_worker_id,
            date=today,
            check_in_time=datetime.now(timezone.utc),
            camera_id=req.camera_id,
            camera_name=req.camera_name,
        )
        db.add(log)
        db.commit()
        attendance_logged = True

    return {
        "matched": True,
        "worker_id": matched_worker_id,
        "name": worker.name if worker else matched_worker_id,
        "job_role": worker.job_role if worker else "",
        "origin": worker.origin if worker else "",
        "distance": round(distance, 4),
        "attendance_logged": attendance_logged,
        "already_checked_in": not attendance_logged,
    }


# ---------------------------------------------------------------------------
# Attendance queries
# ---------------------------------------------------------------------------


@router.get("/attendance/today")
def get_today_attendance(db: Session = Depends(get_db)):
    """Get today's attendance log."""
    today = date.today()
    logs = (
        db.query(AttendanceLog)
        .filter(AttendanceLog.date == today)
        .order_by(AttendanceLog.check_in_time.desc())
        .all()
    )

    result = []
    for log in logs:
        worker = (
            db.query(RegisteredWorker)
            .filter(RegisteredWorker.worker_id == log.worker_id)
            .first()
        )
        result.append(
            {
                "id": log.id,
                "worker_id": log.worker_id,
                "worker_name": worker.name if worker else log.worker_id,
                "job_role": worker.job_role if worker else "",
                "date": log.date.isoformat(),
                "check_in_time": log.check_in_time.isoformat(),
                "camera_id": log.camera_id,
                "camera_name": log.camera_name,
            }
        )

    return {"date": today.isoformat(), "total": len(result), "logs": result}


@router.get("/attendance/history")
def get_attendance_history(
    days: int = 7, db: Session = Depends(get_db)
):
    """Get attendance history for the past N days."""
    start_date = date.today() - timedelta(days=days)
    logs = (
        db.query(AttendanceLog)
        .filter(AttendanceLog.date >= start_date)
        .order_by(AttendanceLog.check_in_time.desc())
        .all()
    )

    result = []
    for log in logs:
        worker = (
            db.query(RegisteredWorker)
            .filter(RegisteredWorker.worker_id == log.worker_id)
            .first()
        )
        result.append(
            {
                "id": log.id,
                "worker_id": log.worker_id,
                "worker_name": worker.name if worker else log.worker_id,
                "job_role": worker.job_role if worker else "",
                "date": log.date.isoformat(),
                "check_in_time": log.check_in_time.isoformat(),
                "camera_id": log.camera_id,
                "camera_name": log.camera_name,
            }
        )

    return {"days": days, "total": len(result), "logs": result}


# ---------------------------------------------------------------------------
# Face recognition diagnostics
# ---------------------------------------------------------------------------


@router.get("/face-recognition/status")
def get_face_recognition_status():
    """Check if the face recognition library is available."""
    svc = FaceRecognitionService.get_instance()
    return {
        "available": svc.is_available(),
        "engine": getattr(svc, "engine_name", "Active"),
        "tolerance": svc.TOLERANCE,
        "message": f"Biometric Engine Active: {getattr(svc, 'engine_name', 'Neural Face Embeddings')}",
    }
