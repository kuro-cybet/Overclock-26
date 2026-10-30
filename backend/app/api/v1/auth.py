from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.user import User
from app.core.security import verify_password, create_access_token
from app.schemas.auth import LoginRequest, TokenResponse, UserSummary
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
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

@router.get("/me", response_model=UserSummary)
def get_me(current_user: User = Depends(get_current_user)):
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

