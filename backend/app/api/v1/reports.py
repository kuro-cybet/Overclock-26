from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.report import Report
from app.database.models.user import User
from app.schemas.report import ReportCreate, ReportResponse
from app.services.intake_service import intake_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("", response_model=ReportResponse)
def submit_report(
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = intake_service.process_incoming_report(
        db=db,
        reporter_id=current_user.id,
        reporter_role=current_user.role,
        title=payload.title,
        description=payload.description,
        building_id=payload.building_id,
        room_id=payload.room_id,
        asset_id=payload.asset_id,
        category=payload.category,
        urgency=payload.urgency,
        source=payload.source or "web_portal"
    )
    db.commit()
    return result["report"]

@router.get("", response_model=List[ReportResponse])
def list_reports(
    status: Optional[str] = Query(None),
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Report)

    # Scoping: Students & Faculty see only their submitted reports
    if current_user.role in ["student", "faculty"]:
        q = q.filter(Report.reporter_id == current_user.id)

    if status:
        q = q.filter(Report.status == status)

    reports = q.order_by(Report.created_at.desc()).limit(limit).all()
    return reports

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        from app.core.exceptions import EntityNotFoundError
        raise EntityNotFoundError("Report", report_id)
    return report

