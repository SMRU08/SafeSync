"""
auth.py — SafeSync Phase 10 Step 7
Cryptographic password hashing (PBKDF2-HMAC-SHA256), PyJWT token management,
and Role-Based Access Control (RBAC) FastAPI dependencies.
"""

import os
import hmac
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Callable
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.audit import AuditLog

logger = logging.getLogger("auth_security")

# OAuth2 bearer token scheme (auto_error=False allows safe dev fallback)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# PBKDF2 Configuration
PBKDF2_ITERATIONS = 600_000
PBKDF2_ALGORITHM = "sha256"


def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 600,000 iterations and a 16-byte random salt.
    Format: pbkdf2_sha256$iterations$salt_hex$hash_hex
    """
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against the stored PBKDF2 hash in constant time.
    """
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = bytes.fromhex(parts[3])

        computed_hash = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(computed_hash, expected_hash)
    except Exception as e:
        logger.error("Password verification error: %s", e)
        return False


def get_jwt_secret() -> str:
    """Retrieves the JWT signing secret from settings or safe fallback."""
    secret = settings.JWT_SECRET_KEY or settings.SECRET_KEY
    if not secret:
        # Development fallback secret
        secret = "safesync-dev-secret-key-32bytes-long"
    return secret


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now})
    secret = get_jwt_secret()
    return jwt.encode(to_encode, secret, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decodes and verifies a JWT token. Raises HTTPException on invalid/expired token."""
    try:
        secret = get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def log_audit_event(
    db: Session,
    action: str,
    username: Optional[str] = None,
    resource: Optional[str] = None,
    details: Optional[str] = None,
    request: Optional[Request] = None,
):
    """Safely logs a security audit event to the database without throwing exceptions."""
    try:
        ip = None
        if request and request.client:
            ip = request.client.host
        entry = AuditLog(
            username=username or "anonymous",
            action=action,
            resource=resource,
            details=details,
            ip_address=ip,
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to write audit log: %s", e)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency returning the authenticated User.
    If AUTH_ENABLED is False and no token is provided, returns a development Admin user.
    """
    if not settings.AUTH_ENABLED and not token:
        # Provide safe development user
        dev_user = db.query(User).filter_by(username="dev_admin").first()
        if not dev_user:
            dev_user = User(
                username="dev_admin",
                full_name="Development Administrator",
                role=UserRole.ADMIN.value,
                hashed_password=hash_password("dev_admin_password"),
                is_active=True,
            )
            db.add(dev_user)
            db.commit()
            db.refresh(dev_user)
        return dev_user

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter_by(username=username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )
    return user


def require_role(allowed_roles: List[str]) -> Callable:
    """
    FastAPI dependency factory enforcing Role-Based Access Control.
    Example: Depends(require_role(["ADMIN", "OPERATOR"]))
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}. Current role: {current_user.role}",
            )
        return current_user

    return role_checker
