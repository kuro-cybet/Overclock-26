from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.user import User
from app.schemas.auth import UserSummary
from app.api.deps import require_role

router = APIRouter(prefix="/users", tags=["users"])


def _summary(u: User) -> UserSummary:
    return UserSummary(
        id=u.id,
        email=u.email,
        name=u.name,
        role=u.role,
        sub_role=u.sub_role,
        department=u.department,
        building_id=u.building_id,
        floor_id=u.floor_id,
    )


@router.get("", response_model=List[UserSummary])
def list_users(
    role: Optional[str] = Query(None),
    limit: int = 50,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    users = q.limit(limit).all()
    return [_summary(u) for u in users]
