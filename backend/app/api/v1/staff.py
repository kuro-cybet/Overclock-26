import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Body, status as http_status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.staff import StaffProfile
from app.database.models.user import User
from app.schemas.staff import (
    StaffProfileResponse,
    StaffStatusUpdateRequest,
    StaffStatusUpdateResponse,
    EligibleStaffResponse
)
from app.services.assignment_service import assignment_service
from app.api.deps import require_role

router = APIRouter(prefix="/staff", tags=["staff"])

_staff_access = require_role(["admin", "technician"])

@router.get("")
def list_staff(
    current_user: User = Depends(_staff_access),
    db: Session = Depends(get_db)
):
    profiles = db.query(StaffProfile).all()
    results = []
    for p in profiles:
        user = db.query(User).filter(User.id == p.user_id).first()
        if user:
            skills = json.loads(p.skills) if p.skills else []
            results.append({
                "profile_id": p.id,
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "sub_role": user.sub_role,
                "shift": p.shift,
                "assigned_building_id": p.assigned_building_id,
                "assigned_floor_id": p.assigned_floor_id,
                "availability_status": p.availability_status,
                "current_workload": p.current_workload,
                "skills": skills
            })
    return results

@router.patch(
    "/{user_id}/status",
    response_model=StaffStatusUpdateResponse,
    summary="Update Staff Availability Status",
    description="Updates the on-duty availability status of a technician (`available`, `on_task`, `absent`, `on_leave`).",
    responses={
        404: {"description": "Staff profile not found"}
    }
)
def update_staff_availability(
    user_id: str,
    status: str = Body(..., embed=True),
    current_user: User = Depends(_staff_access),
    db: Session = Depends(get_db)
):
    """
    Update technician availability status for dispatch matching.
    """
    prof = db.query(StaffProfile).filter(StaffProfile.user_id == user_id).first()
    if not prof:
        raise EntityNotFoundError("StaffProfile", user_id)
    prof.availability_status = payload.status
    db.commit()
    return {"user_id": user_id, "status": prof.availability_status}

@router.get(
    "/eligible",
    response_model=List[EligibleStaffResponse],
    summary="Find Eligible Technicians for Dispatch",
    description="Calculates suitability scores for available technicians based on skill matching, shift alignment, building proximity, and current workload."
)
def get_eligible_staff(
    skills: Optional[str] = Query(None),
    building_id: Optional[str] = Query(None),
    shift: Optional[str] = Query("morning"),
    current_user: User = Depends(_staff_access),
    db: Session = Depends(get_db)
):
    """
    Rank and retrieve eligible technicians matching criteria.
    """
    skills_list = [s.strip() for s in skills.split(",")] if skills else []
    return assignment_service.find_eligible_technicians(
        db=db,
        required_skills=skills_list,
        preferred_building_id=building_id,
        preferred_shift=shift
    )
