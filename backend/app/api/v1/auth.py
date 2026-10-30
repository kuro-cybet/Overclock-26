import json
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import get_db
from app.database.models.audit import AuditLog
from app.database.models.role_assignment import RoleAssignment
from app.database.models.user import User
from app.core.security import verify_password, create_access_token
from app.schemas.auth import (
    GoogleLoginRequest,
    ImpersonateRequest,
    LoginRequest,
    TokenResponse,
    UserSummary,
)
from app.api.deps import get_current_user, require_admin_sub_role

router = APIRouter(prefix="/auth", tags=["auth"])

# Canonical persona used when a system_admin previews a portal. Overridable so
# the deployed demo can preview the real provisioned accounts.
PERSONA_EMAILS = {
    "technician": os.getenv("CAMPUSOPS_PERSONA_TECHNICIAN", "techtroveversion3@gmail.com"),
    "faculty": os.getenv("CAMPUSOPS_PERSONA_FACULTY", "susen469@gmail.com"),
    "student": os.getenv("CAMPUSOPS_PERSONA_STUDENT", "192573020.simats@saveetha.com"),
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
    """
    Authenticate with a password.

    Disabled by default. CampusOps uses ``POST /auth/google`` and the
    server-side role allowlist; password sign-in only exists as a fallback and
    must be explicitly enabled with ``PASSWORD_LOGIN_ENABLED=true``.
    """
    if not settings.PASSWORD_LOGIN_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password sign-in is disabled. Continue with Google.",
        )

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

    user.last_login_at = datetime.utcnow()

    token = create_access_token(
        subject=user.id,
        role=user.role,
        sub_role=user.sub_role
    )

    db.commit()

    return TokenResponse(
        access_token=token,
        user=_user_summary(user)
    )


@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Sign in with a Google Identity Services ID token.

    The role is **never** taken from the client. It is looked up from the
    server-side ``role_assignments`` allowlist by verified email, so only the
    accounts an administrator assigned can obtain a token, and each one can
    only ever get its assigned role.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured on this server.",
        )

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token

        claims = id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Google credential.",
        )

    email = (claims.get("email") or "").strip().lower()
    if not email or not claims.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google did not return a verified email address.",
        )

    assignment = (
        db.query(RoleAssignment)
        .filter(RoleAssignment.email == email, RoleAssignment.is_active.is_(True))
        .first()
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "This Google account has not been assigned a CampusOps role. "
                "Contact the system administrator."
            ),
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            # Google-only accounts never use a password; this sentinel can
            # never match a hash produced by hash_password().
            hashed_password="!",
            name=claims.get("name") or email.split("@")[0],
            role=assignment.role,
            created_at=datetime.utcnow(),
        )
        db.add(user)
        db.flush()

    user.name = user.name or claims.get("name") or email.split("@")[0]
    user.role = assignment.role
    user.sub_role = assignment.sub_role
    user.department = assignment.department or user.department
    user.building_id = assignment.building_id or user.building_id
    user.floor_id = assignment.floor_id or user.floor_id
    user.avatar_url = claims.get("picture") or user.avatar_url
    user.auth_provider = "google"
    user.provider_subject = claims.get("sub") or user.provider_subject
    user.email_verified = True
    user.last_login_at = datetime.utcnow()
    user.is_active = True

    if assignment.consumed_at is None:
        assignment.consumed_at = datetime.utcnow()

    db.add(
        AuditLog(
            action="GOOGLE_SIGN_IN",
            actor_id=user.id,
            actor_role=user.sub_role or user.role,
            entity_type="user",
            entity_id=user.id,
            new_value=json.dumps({"email": email, "provider": "google"}),
            reason="User signed in with Google.",
        )
    )
    db.commit()

    token = create_access_token(
        subject=user.id,
        role=user.role,
        sub_role=user.sub_role,
    )

    return TokenResponse(
        access_token=token,
        user=_user_summary(user),
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
