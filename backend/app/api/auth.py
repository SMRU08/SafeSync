"""
auth.py — SafeSync Phase 10 Step 7
FastAPI Router for User Authentication, User Provisioning, and Audit Trail Inspection.
"""

from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.security.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_role,
    log_audit_event,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication & Security"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    expires_in_minutes: int


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    username: Optional[str]
    action: str
    resource: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]


@router.post("/login", response_model=TokenResponse)
def login(login_req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Authenticates user with username & password.
    Returns signed JWT access token and logs an audit trail event.
    """
    user = db.query(User).filter_by(username=login_req.username).first()

    if not user or not verify_password(login_req.password, user.hashed_password):
        log_audit_event(
            db=db,
            action="LOGIN_FAILED",
            username=login_req.username,
            resource="/api/auth/login",
            details="Invalid username or password",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        log_audit_event(
            db=db,
            action="LOGIN_BLOCKED",
            username=login_req.username,
            resource="/api/auth/login",
            details="Account is inactive",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(hours=8),
    )

    log_audit_event(
        db=db,
        action="LOGIN_SUCCESS",
        username=user.username,
        resource="/api/auth/login",
        details=f"User authenticated with role {user.role}",
        request=request,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=user.username,
        role=user.role,
        expires_in_minutes=480,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns profile for currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_req: UserCreateRequest,
    request: Request,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db),
):
    """
    ADMIN-only: Provision a new user with an explicit role (ADMIN, OPERATOR, VIEWER).
    """
    existing = db.query(User).filter_by(username=user_req.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_req.username}' is already registered.",
        )

    new_user = User(
        username=user_req.username,
        hashed_password=hash_password(user_req.password),
        full_name=user_req.full_name,
        role=user_req.role.value,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit_event(
        db=db,
        action="USER_CREATED",
        username=current_user.username,
        resource=f"/api/auth/users/{new_user.username}",
        details=f"Created user {new_user.username} with role {new_user.role}",
        request=request,
    )

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        full_name=new_user.full_name,
        role=new_user.role,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
    )


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def list_audit_logs(
    limit: int = 100,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db),
):
    """
    ADMIN-only: Inspect security audit log entries.
    """
    entries = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        AuditLogResponse(
            id=e.id,
            timestamp=e.timestamp,
            username=e.username,
            action=e.action,
            resource=e.resource,
            details=e.details,
            ip_address=e.ip_address,
        )
        for e in entries
    ]
