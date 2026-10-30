from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.user import User
from app.schemas.auth import UserSummary, DemoAccountResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get(
    "",
    response_model=List[UserSummary],
    summary="List Campus Users",
    description="Retrieves active user profiles across campus roles with optional filtering by role."
)
def list_users(
    role: Optional[str] = Query(None, description="Filter users by primary role: `admin`, `technician`, `faculty`, `student`"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of users to retrieve"),
    db: Session = Depends(get_db)
):
    """
    List user accounts with role, department, and assigned physical location metadata.
    """
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

@router.get(
    "/demo-accounts",
    response_model=List[DemoAccountResponse],
    summary="Get Demo Accounts for Quick Switching",
    description="Returns pre-seeded demo user profiles representing different system roles for presentation and testing convenience."
)
def get_demo_accounts(db: Session = Depends(get_db)):
    """
    Returns preset demo accounts for rapid role-switching and presentation walkthroughs.
    """
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
