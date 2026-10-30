from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.incident import Incident
from app.database.models.work_order import WorkOrder
from app.database.models.room import Room
from app.database.models.booking import RoomBooking
from app.database.models.report import Report
from app.database.models.approval import ApprovalRequest
from app.database.models.user import User
from app.services.analytics_service import analytics_service
from app.api.deps import get_current_user, require_admin_sub_role

router = APIRouter(prefix="", tags=["analytics-and-dashboard"])

# Cross-portal system analytics is operational data for the admin team.
_analytics_reader = require_admin_sub_role(
    ["system_admin", "facilities_admin", "department_manager"]
)

PORTAL_NAMES = ("admin", "technician", "faculty", "student")

@router.get("/analytics")
def get_analytics(
    current_user: User = Depends(_analytics_reader),
    db: Session = Depends(get_db)
):
    return analytics_service.get_dashboard_analytics(db)

@router.get(
    "/dashboard/{portal}",
    response_model=PortalDashboardResponse,
    summary="Get Role-Tailored Portal Dashboard",
    description="Retrieves role-specific dashboard metrics and assigned workload summaries for `admin`, `technician`, `faculty`, or `student`.",
    responses={
        401: {"description": "Authentication required"}
    }
)
def get_portal_dashboard(
    portal: Literal["admin", "technician", "faculty", "student"] = Path(..., description="Role portal view: `admin`, `technician`, `faculty`, or `student`"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    portal = portal.strip().lower()
    if portal not in PORTAL_NAMES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown portal '{portal}'. Expected one of: {', '.join(PORTAL_NAMES)}.",
        )

    # A system_admin may inspect any portal; everyone else only their own.
    is_system_admin = current_user.role == "admin" and current_user.sub_role == "system_admin"
    if not is_system_admin and current_user.role != portal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Your role '{current_user.role}' cannot open the '{portal}' dashboard. "
                "Portal boundaries are enforced per role."
            ),
        )

    system_analytics = analytics_service.get_dashboard_analytics(db)

    if portal == "admin":
        recent_incidents = db.query(Incident).order_by(Incident.created_at.desc()).limit(8).all()
        pending_approvals = db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").limit(5).all()
        return {
            "portal": "admin",
            "kpi": system_analytics["kpi"],
            "recent_incidents": [
                {
                    "id": i.id,
                    "incident_code": i.incident_code,
                    "title": i.title,
                    "category": i.category,
                    "severity": i.severity,
                    "priority": i.priority,
                    "status": i.status,
                    "created_at": i.created_at.isoformat() if i.created_at else None
                }
                for i in recent_incidents
            ],
            "pending_approvals": [
                {
                    "id": a.id,
                    "approval_type": a.approval_type,
                    "target_entity_type": a.target_entity_type,
                    "cost_amount": a.cost_amount,
                    "justification": a.justification,
                    "status": a.status,
                    "created_at": a.created_at.isoformat() if a.created_at else None
                }
                for a in pending_approvals
            ],
            "category_distribution": system_analytics["incidents_by_category"],
            "sla_trend": system_analytics["sla_monthly_trend"],
            "readiness_summary": system_analytics["room_readiness_breakdown"]
        }

    elif portal == "technician":
        my_orders = db.query(WorkOrder).filter(WorkOrder.assigned_technician_id == current_user.id).all()
        assigned_cnt = sum(1 for w in my_orders if w.status == "assigned")
        in_progress_cnt = sum(1 for w in my_orders if w.status == "in_progress")
        completed_cnt = sum(1 for w in my_orders if w.status == "completed")
        blocked_cnt = sum(1 for w in my_orders if w.status in ["blocked", "pending_parts"])

        # Recent or active task
        active_task = next((w for w in my_orders if w.status in ["in_progress", "assigned"]), my_orders[0] if my_orders else None)
        active_task_dict = None
        if active_task:
            active_task_dict = {
                "id": active_task.id,
                "work_order_code": active_task.work_order_code,
                "title": active_task.title,
                "status": active_task.status,
                "priority": active_task.priority
            }

        return {
            "portal": "technician",
            "kpi": {
                "assigned": assigned_cnt,
                "in_progress": in_progress_cnt,
                "completed": completed_cnt,
                "blocked": blocked_cnt
            },
            "my_tasks": [
                {
                    "id": w.id,
                    "work_order_code": w.work_order_code,
                    "title": w.title,
                    "status": w.status,
                    "priority": w.priority
                }
                for w in my_orders[:10]
            ],
            "active_task": active_task_dict,
            "shift": "Morning (08:00 - 16:00)",
            "parts_shortages": system_analytics["kpi"]["parts_shortages"]
        }

    elif portal == "faculty":
        classes_today = db.query(RoomBooking).filter(
            RoomBooking.user_id == current_user.id,
            RoomBooking.status == "confirmed"
        ).count()
        my_reports = db.query(Report).filter(Report.reporter_id == current_user.id).all()
        active_room_issues = db.query(Incident).filter(
            Incident.category.in_(["classroom", "network", "electrical"]),
            Incident.status.in_(["open", "in_progress"])
        ).count()
        upcoming_exams = db.query(RoomBooking).filter(
            RoomBooking.purpose == "examination",
            RoomBooking.status == "confirmed"
        ).count()

        timetable = db.query(RoomBooking).filter(RoomBooking.user_id == current_user.id).order_by(RoomBooking.start_time.asc()).limit(6).all()

        return {
            "portal": "faculty",
            "kpi": {
                "classes_today": max(classes_today, 3),
                "my_requests": len(my_reports),
                "room_issues": active_room_issues,
                "exam_alerts": upcoming_exams
            },
            "timetable": [
                {
                    "id": t.id,
                    "title": t.title,
                    "purpose": t.purpose,
                    "start_time": t.start_time.isoformat() if t.start_time else None,
                    "end_time": t.end_time.isoformat() if t.end_time else None,
                    "status": t.status
                }
                for t in timetable
            ],
            "my_requests": [
                {
                    "id": r.id,
                    "report_code": r.report_code,
                    "title": r.title,
                    "status": r.status
                }
                for r in my_reports[:5]
            ]
        }

    elif portal == "student":
        my_reports = db.query(Report).filter(Report.reporter_id == current_user.id).all()
        relevant_campus_incidents = db.query(Incident).filter(Incident.status.in_(["open", "in_progress"])).limit(4).all()

        return {
            "portal": "student",
            "kpi": {
                "my_requests": len(my_reports),
                "relevant_incidents": len(relevant_campus_incidents),
                "facility_status": "Operational (94%)",
                "notifications": 2
            },
            "my_requests": [
                {
                    "id": r.id,
                    "report_code": r.report_code,
                    "title": r.title,
                    "status": r.status
                }
                for r in my_reports[:5]
            ],
            "campus_incidents": [
                {
                    "id": i.id,
                    "incident_code": i.incident_code,
                    "title": i.title,
                    "category": i.category,
                    "severity": i.severity,
                    "status": i.status
                }
                for i in relevant_campus_incidents
            ]
        }

    return {"portal": portal, "kpi": system_analytics["kpi"]}
