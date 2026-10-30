import json
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException, status as http_status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.booking import RoomBooking
from app.database.models.room import Room
from app.database.models.campus import Building
from app.database.models.incident import Incident
from app.database.models.work_order import WorkOrder
from app.database.models.notification import Notification
from app.database.models.approval import ApprovalRequest
from app.database.models.user import User
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    ExaminationSessionResponse,
    ExamReadinessInspectionRequest,
    ExamReadinessResponse
)
from app.services.booking_service import booking_service
from app.services.event_service import event_service
from app.services.notification_service import notification_service
from app.core.exceptions import EntityNotFoundError, PermissionDeniedError
from app.api.deps import get_current_user

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.get(
    "",
    response_model=List[BookingResponse],
    summary="List Room Bookings",
    description="Retrieves scheduled room reservations across campus with multi-parameter filtering."
)
def list_bookings(
    room_id: Optional[str] = Query(None, description="Filter by room UUID"),
    status: Optional[str] = Query(None, description="Filter by status: `confirmed`, `tentative`, `cancelled`, `completed`"),
    user_id: Optional[str] = Query(None, description="Filter by booking creator user UUID"),
    purpose: Optional[str] = Query(None, description="Filter by purpose: `examination`, `lecture`, `lab_session`, `meeting`, `seminar`"),
    limit: int = Query(100, ge=1, le=500, description="Maximum bookings to return"),
    db: Session = Depends(get_db)
):
    """
    List scheduled bookings with timetable and room allocation data.
    """
    q = db.query(RoomBooking)
    if room_id:
        q = q.filter(RoomBooking.room_id == room_id)
    if status:
        q = q.filter(RoomBooking.status == status)
    if user_id:
        q = q.filter(RoomBooking.user_id == user_id)
    if purpose:
        q = q.filter(RoomBooking.purpose == purpose)
    bookings = q.order_by(RoomBooking.start_time.asc()).limit(limit).all()
    return bookings

@router.get(
    "/examinations",
    response_model=List[ExaminationSessionResponse],
    summary="List Scheduled Examinations with Room Readiness",
    description="Retrieves upcoming examination sessions enriched with assigned room operational status, active infrastructure incidents, and daily readiness flags."
)
def list_examination_sessions(
    limit: int = Query(50, ge=1, le=200, description="Maximum examination sessions to return"),
    db: Session = Depends(get_db)
):
    """
    Lists scheduled examinations enriched with room details and current readiness.
    """
    bookings = (
        db.query(RoomBooking)
        .filter(RoomBooking.purpose == "examination", RoomBooking.status != "cancelled")
        .order_by(RoomBooking.start_time.asc())
        .limit(limit)
        .all()
    )

    results = []
    now = datetime.utcnow()

    for b in bookings:
        room = db.query(Room).filter(Room.id == b.room_id).first()
        building = db.query(Building).filter(Building.id == room.building_id).first() if room else None

        active_incident = (
            db.query(Incident)
            .filter(
                Incident.room_id == b.room_id,
                Incident.status.in_(["open", "in_progress", "pending_parts", "pending_approval"])
            )
            .first()
        )

        hours_remaining = round(max(0.0, (b.start_time - now).total_seconds() / 3600.0), 1)

        results.append({
            "id": b.id,
            "booking_code": b.booking_code,
            "title": b.title,
            "purpose": b.purpose,
            "start_time": b.start_time.isoformat(),
            "end_time": b.end_time.isoformat(),
            "hours_remaining": hours_remaining,
            "room_id": room.id if room else None,
            "room_number": room.room_number if room else "Unknown",
            "room_name": room.name if room else "Unknown",
            "building_name": building.name if building else "Main Campus",
            "room_status": room.status if room else "unknown",
            "daily_readiness_status": room.daily_readiness_status if room else "unconfirmed",
            "equipment_required": b.equipment_required,
            "has_open_incident": active_incident is not None,
            "incident_title": active_incident.title if active_incident else None,
            "status": b.status
        })

    return results

@router.post(
    "",
    response_model=BookingResponse,
    summary="Create Room Reservation",
    description="Reserves a classroom, lab, or examination hall with automated conflict detection and double-booking prevention.",
    responses={
        401: {"description": "Authentication required"},
        409: {"description": "Conflict: Target room is already reserved for this time interval"}
    }
)
def create_booking(
    payload: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reserve a campus room with automated double-booking prevention.
    """
    booking = booking_service.create_booking(
        db=db,
        user_id=current_user.id,
        user_role=current_user.role,
        room_id=payload.room_id,
        title=payload.title,
        purpose=payload.purpose,
        start_time=payload.start_time,
        end_time=payload.end_time,
        equipment_required=payload.equipment_required
    )
    db.commit()
    db.refresh(booking)
    return booking

@router.post(
    "/{booking_id}/exam-readiness",
    response_model=ExamReadinessResponse,
    summary="Submit Examination Readiness Inspection",
    description="Submits a structured pre-exam physical inspection checklist (HVAC, power, seating, AV). If faults are discovered, automatically creates an emergency incident and alerts facilities dispatch.",
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Forbidden: Only faculty or administrators may submit exam inspections"},
        404: {"description": "Booking or room not found"}
    }
)
def submit_exam_readiness_inspection(
    booking_id: str,
    payload: ExamReadinessInspectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a pre-exam physical inspection for a scheduled examination session.
    Records inspection status and timestamps.
    If infrastructure problems are found, logs an emergency incident and triggers targeted notifications.
    Faculty cannot override administrative approvals.
    """
    if current_user.role not in ["faculty", "admin"]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Only faculty invigilators or operations administrators may submit examination readiness inspections."
        )

    booking = db.query(RoomBooking).filter(RoomBooking.id == booking_id).first()
    if not booking:
        raise EntityNotFoundError("RoomBooking", booking_id)

    room = db.query(Room).filter(Room.id == booking.room_id).first()
    if not room:
        raise EntityNotFoundError("Room", booking.room_id)

    timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    checklist_dict = payload.checklist.model_dump() if hasattr(payload.checklist, "model_dump") else payload.checklist

    if payload.status == "ready":
        # Mark room confirmed today
        room.daily_readiness_status = "confirmed_today"
        room.last_confirmed_at = datetime.utcnow()
        room.confirmed_by = current_user.name
        room.status = "available"

        event_service.log_event(
            db=db,
            event_type="exam_readiness_confirmed",
            entity_type="room_booking",
            entity_id=booking.id,
            severity="info",
            payload={"room": room.room_number, "inspector": current_user.name, "checklist": checklist_dict},
            actor_id=current_user.id
        )

        db.commit()
        return {
            "status": "ready",
            "readiness_status": "ready",
            "booking_id": booking.id,
            "message": f"Examination readiness confirmed for {booking.title} in {room.room_number}.",
            "room_number": room.room_number,
            "inspected_by": current_user.name,
            "timestamp": timestamp_str
        }

    else:
        # Fault detected: Record infrastructure problems and alert facilities
        faults_str = ", ".join(payload.reported_faults) if payload.reported_faults else (payload.notes or "Facility fault")
        room.daily_readiness_status = "unavailable"
        room.status = "under_maintenance"

        # 1. Log incident automatically
        incident_count = db.query(Incident).count()
        inc = Incident(
            incident_code=f"INC-{datetime.utcnow().strftime('%Y%m')}-{incident_count + 1:04d}",
            title=f"Pre-Exam Facility Failure: {booking.title} ({room.room_number})",
            description=f"Faculty inspection by {current_user.name} reported infrastructure faults: {faults_str}. Additional notes: {payload.notes or 'None'}",
            category="academic_exam_facility",
            severity="critical",
            priority="P1",
            building_id=room.building_id,
            room_id=room.id,
            status="open",
            sla_due_at=datetime.utcnow() + timedelta(minutes=30),
            summary=f"Pre-exam readiness check failed in {room.room_number}: {faults_str}"
        )
        db.add(inc)
        db.flush()

        # 2. Trigger targeted notification to operations & facilities admin
        notification_service.create_in_app_notification(
            db=db,
            recipient_id="admin",
            recipient_role="admin",
            title=f"CRITICAL: Exam Readiness Failure in {room.room_number}",
            message=f"Prof. {current_user.name} reported '{faults_str}' for exam '{booking.title}'. Immediate tech dispatch or room relocation required.",
            notif_type="critical",
            link_url="/admin/incidents"
        )

        event_service.log_event(
            db=db,
            event_type="exam_readiness_fault",
            entity_type="room_booking",
            entity_id=booking.id,
            severity="critical",
            payload={"incident_id": inc.id, "faults": faults_str, "room": room.room_number},
            actor_id=current_user.id
        )

        db.commit()
        return {
            "status": "fault_detected",
            "readiness_status": "fault_detected",
            "booking_id": booking.id,
            "message": f"Pre-exam fault logged. Emergency incident {inc.incident_code} dispatched to facilities response team.",
            "incident_code": inc.incident_code,
            "room_number": room.room_number,
            "inspected_by": current_user.name,
            "timestamp": timestamp_str
        }
