from typing import Optional, List
import hashlib
import hmac
import time
from fastapi import Depends, HTTPException, Request, status, Header
from sqlalchemy.orm import Session
from app.config import settings
from app.database.connection import get_db
from app.core.security import decode_access_token
from app.core.permissions import check_permission
from app.database.models.user import User


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "").strip()
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account does not exist or has been deactivated.",
        )
    return user


async def require_inbound_email_access(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Gate the simulated inbound-email webhook.

    Two accepted callers:
      1. An external mail gateway that signs the raw body with
         CAMPUSOPS_INBOUND_SECRET (or CAMPUSOPS_WEBHOOK_SECRET).
      2. A logged-in admin (used by the demo console / tests).
    """
    secret = settings.CAMPUSOPS_INBOUND_SECRET or settings.CAMPUSOPS_WEBHOOK_SECRET
    timestamp = request.headers.get("x-campusops-timestamp", "")
    signature = request.headers.get("x-campusops-signature", "")

    if secret and timestamp and signature:
        try:
            timestamp_number = int(timestamp)
        except ValueError:
            timestamp_number = 0

        if abs(time.time() - timestamp_number) <= 300:
            raw_body = (await request.body()).decode("utf-8", errors="replace")
            expected = hmac.new(
                secret.encode("utf-8"),
                f"{timestamp}.{raw_body}".encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            if hmac.compare_digest(expected, signature.lower()):
                return None

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provide a system admin token or a valid webhook signature.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_current_user(authorization=authorization, db=db)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for this operation.",
        )
    return user


def require_role(allowed_roles: list):
    """Gate by top-level role (admin / technician / faculty / student)."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action forbidden for role '{current_user.role}'. Required: {allowed_roles}",
            )
        return current_user
    return role_checker


def require_admin_sub_role(allowed_sub_roles: List[str]):
    """
    Gate admin-only endpoints by sub-role.
    'system_admin' is always allowed through (full admin control).
    Other admin sub-roles are only allowed if they appear in allowed_sub_roles.
    Non-admin roles or unauthorized sub-roles get 403 Forbidden.
    """
    def sub_role_checker(
        authorization: Optional[str] = Header(None),
        db: Session = Depends(get_db)
    ) -> User:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token is missing.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization.replace("Bearer ", "").strip()
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload["sub"]
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account does not exist or has been deactivated.",
            )

        if user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required for this operation.",
            )

        # system_admin has full access to all admin operations
        if user.sub_role == "system_admin":
            return user

        if user.sub_role not in allowed_sub_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Your admin sub-role '{user.sub_role}' is not authorised for this action. "
                    f"Required: {allowed_sub_roles} (or system_admin)."
                ),
            )
        return user
    return sub_role_checker


def require_any_admin(current_user: User = Depends(get_current_user)) -> User:
    """Allow any admin sub-role (but not other roles)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )
    return current_user


def require_permission(permission: str):
    """
    Gate an endpoint on a named permission from app.core.permissions.

    system_admin is a superset for admin operations, but business approvals
    stay with their domain sub-roles (separation of duties is enforced in
    the service layer).
    """
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        check_permission(current_user.role, current_user.sub_role, permission)
        return current_user
    return permission_checker

