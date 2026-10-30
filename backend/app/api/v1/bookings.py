from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.booking import RoomBooking
from app.database.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import booking_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.get("", response_model=List[BookingResponse])
def list_bookings(
    room_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    purpose: Optional[str] = Query(None),
    limit: int = 100,
    db: Session = Depends(get_db)
):
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

@router.post("", response_model=BookingResponse)
def create_booking(
    payload: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

