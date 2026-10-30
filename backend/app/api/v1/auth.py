import json
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models.audit import AuditLog
from app.database.models.user import User
from app.core.security import verify_password, create_access_token
from app.schemas.auth import (
    ImpersonateRequest,
    LoginRequest,
    TokenResponse,
    UserSummary,
)
from app.api.deps import get_current_user, require_admin_sub_role

router = APIRouter(prefix="/auth", tags=["auth"])

# Canonical demo persona used when a system_admin previews a portal.
PERSONA_EMAILS = {
    "technician": "tech@campusops.edu",
    "faculty": "faculty@campusops.edu",
    "student": "student@campusops.edu",
}

PREVIEWABLE_ROLES = tuple(PERSONA_EMAILS.keys())


def _user_summary(user: User) -> UserSummary:
    return UserSummary(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        sub_role=user.sub_role,
        department=user.department,
        building_id=user.building_id,
        floor_id=user.floor_id,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Contact a system administrator."
        )

    token = create_access_token(
        subject=user.id,
        role=user.role,
        sub_role=user.sub_role
    )

    return TokenResponse(
        access_token=token,
        user=_user_summary(user)
    )


@router.get("/me", response_model=UserSummary)
def get_me(current_user: User = Depends(get_current_user)):
    return _user_summary(current_user)


@router.post("/impersonate", response_model=TokenResponse)
def impersonate_portal_role(
    payload: ImpersonateRequest,
    current_user: User = Depends(require_admin_sub_role(["system_admin"])),
    db: Session = Depends(get_db),
):
    """
    Issue a short-lived token for another portal role so a system_admin can
    preview the platform exactly as that role sees it.

    Only system_admin can call this. The original admin token stays valid and
    is never replaced on the server; the client keeps it to exit the preview.
    Admin roles cannot be impersonated (prevents privilege confusion).
    """
    if not payload.role and not payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide either 'role' or 'user_id'.",
        )

    target: Optional[User] = None

    if payload.user_id:
        target = db.query(User).filter(User.id == payload.user_id).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found.",
            )
    else:
        role = (payload.role or "").strip().lower()
        if role not in PREVIEWABLE_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {', '.join(PREVIEWABLE_ROLES)} portals can be previewed.",
            )
        target = (
            db.query(User)
            .filter(User.email == PERSONA_EMAILS[role], User.is_active.is_(True))
            .first()
        )
        if not target:
            target = (
                db.query(User)
                .filter(User.role == role, User.is_active.is_(True))
                .order_by(User.created_at.asc())
                .first()
            )

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active user exists for that portal role.",
        )

    if target.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin accounts cannot be impersonated. Use your own admin session.",
        )

    if not target.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Target account is deactivated.",
        )

    token = create_access_token(
        subject=target.id,
        role=target.role,
        sub_role=target.sub_role,
        expires_delta=timedelta(minutes=120),
        impersonated_by=current_user.id,
    )

    db.add(
        AuditLog(
            action="PORTAL_IMPERSONATED",
            actor_id=current_user.id,
            actor_role=current_user.sub_role or current_user.role,
            entity_type="user",
            entity_id=target.id,
            new_value=json.dumps(
                {
                    "target_email": target.email,
                    "target_role": target.role,
                    "target_sub_role": target.sub_role,
                }
            ),
            reason="System administrator opened portal preview.",
        )
    )
    db.commit()

    return TokenResponse(
        access_token=token,
        user=_user_summary(target),
        impersonated_by=current_user.id,
        impersonated_by_name=current_user.name,
    )
