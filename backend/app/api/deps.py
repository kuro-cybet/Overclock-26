from typing import Optional, List
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.core.security import decode_access_token
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
    'system_admin' is always allowed through (superuser).
    Other admin sub-roles are only allowed if they appear in allowed_sub_roles.
    Non-admin roles are always rejected.
    """
    def sub_role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required for this operation.",
            )
        # system_admin bypasses all sub-role restrictions
        if current_user.sub_role == "system_admin":
            return current_user
        if current_user.sub_role not in allowed_sub_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Your admin sub-role '{current_user.sub_role}' is not authorised for this action. "
                    f"Required: {allowed_sub_roles} (or system_admin)."
                ),
            )
        return current_user
    return sub_role_checker


def require_any_admin(current_user: User = Depends(get_current_user)) -> User:
    """Allow any admin sub-role (but not other roles)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )
    return current_user

