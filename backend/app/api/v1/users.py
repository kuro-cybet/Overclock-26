from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.user import User
from app.schemas.auth import UserSummary

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=List[UserSummary])
def list_users(
    role: Optional[str] = Query(None),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    users = q.limit(limit).all()
    return [
        UserSummary(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role,
            sub_role=u.sub_role,
            department=u.department,
            building_id=u.building_id,
            floor_id=u.floor_id
        ) for u in users
    ]

@router.get("/demo-accounts")
def get_demo_accounts(db: Session = Depends(get_db)):
    # Returns preset demo accounts for easy switching
    demo_emails = [
        "admin@campusops.edu",
        "dept_mgr@campusops.edu",
        "facilities@campusops.edu",
        "procurement@campusops.edu",
        "tech@campusops.edu",
        "floor_incharge@campusops.edu",
        "janitor@campusops.edu",
        "room_incharge@campusops.edu",
        "faculty@campusops.edu",
        "student@campusops.edu"
    ]
    users = db.query(User).filter(User.email.in_(demo_emails)).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "sub_role": u.sub_role,
            "department": u.department,
            "password": "password123"
        }
        for u in users
    ]

