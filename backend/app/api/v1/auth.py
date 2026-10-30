from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.user import User
from app.core.security import verify_password, create_access_token
from app.schemas.auth import LoginRequest, TokenResponse, UserSummary
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate User and Generate JWT Token",
    description="Authenticates campus user with university email and password, returning a signed JWT Bearer access token and user profile summary.",
    responses={
        401: {"description": "Incorrect email or password"}
    }
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user credentials.

    - **email**: Valid registered campus email address.
    - **password**: Plaintext password checked against argon2/bcrypt password hash.
    - Returns signed JWT token with sub-role claims and active session profile.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    token = create_access_token(
        subject=user.id,
        role=user.role,
        sub_role=user.sub_role
    )

    user_summary = UserSummary(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        sub_role=user.sub_role,
        department=user.department,
        building_id=user.building_id,
        floor_id=user.floor_id
    )

    return TokenResponse(
        access_token=token,
        user=user_summary
    )

@router.get(
    "/me",
    response_model=UserSummary,
    summary="Get Authenticated User Profile",
    description="Returns the profile and role metadata of the currently authenticated bearer token owner.",
    responses={
        401: {"description": "Missing, expired, or invalid authorization token"}
    }
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Retrieve profile details for current active session.

    Requires HTTP Bearer token in the `Authorization` header.
    """
    return UserSummary(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        sub_role=current_user.sub_role,
        department=current_user.department,
        building_id=current_user.building_id,
        floor_id=current_user.floor_id
    )
