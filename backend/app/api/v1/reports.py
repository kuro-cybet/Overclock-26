from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.report import Report
from app.database.models.user import User
from app.schemas.report import ReportCreate, ReportResponse
from app.services.intake_service import intake_service
from app.api.deps import get_current_user
from app.core.exceptions import EntityNotFoundError

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post(
    "",
    response_model=ReportResponse,
    summary="Submit Facility or Equipment Report",
    description="Submits a new maintenance, facility, or IT issue report. AI extraction classifies urgency and category.",
    responses={
        401: {"description": "Authentication required"}
    }
)
def submit_report(
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a facility fault or maintenance request.

    - **title**: Brief summary of the problem.
    - **description**: Comprehensive description of symptoms or damage.
    - **building_id**: Campus building UUID.
    - **room_id**: Optional specific classroom, lab, or office UUID.
    - **asset_id**: Optional specific asset UUID.
    """
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

@router.get(
    "",
    response_model=List[ReportResponse],
    summary="List Maintenance Reports",
    description="Retrieves submitted maintenance reports. Scoped automatically by caller role (students and faculty see only their own reports).",
    responses={
        401: {"description": "Authentication required"}
    }
)
def list_reports(
    status: Optional[str] = Query(None, description="Filter by status: `submitted`, `triaged`, `converted`, `rejected`"),
    limit: int = Query(100, ge=1, le=500, description="Maximum reports to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List reports visible to the active user.
    """
    q = db.query(Report)

    # Scoping: Students & Faculty see only their submitted reports
    if current_user.role in ["student", "faculty"]:
        q = q.filter(Report.reporter_id == current_user.id)

    if status:
        q = q.filter(Report.status == status)

    reports = q.order_by(Report.created_at.desc()).limit(limit).all()
    return reports

@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get Report by ID",
    description="Retrieves a specific report by its UUID.",
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Report not found"}
    }
)
def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve single report details.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise EntityNotFoundError("Report", report_id)

    # Students and faculty may only open their own reports.
    if current_user.role in ["student", "faculty"] and report.reporter_id != current_user.id:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="You can only view your own reports.",
        )

    return report
