import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.database.models.room import Room
from app.database.models.booking import RoomBooking
from app.core.exceptions import BookingConflictError, CampusOpsException

class BookingService:
    def check_room_availability(
        self,
        db: Session,
        room_id: str,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: Optional[str] = None
    ) -> bool:
        # Check room status itself
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room or room.status in ["under_maintenance", "unavailable"]:
            return False

        # Check overlapping bookings
        query = db.query(RoomBooking).filter(
            RoomBooking.room_id == room_id,
            RoomBooking.status.in_(["confirmed"]),
            or_(
                and_(RoomBooking.start_time <= start_time, RoomBooking.end_time > start_time),
                and_(RoomBooking.start_time < end_time, RoomBooking.end_time >= end_time),
                and_(RoomBooking.start_time >= start_time, RoomBooking.end_time <= end_time)
            )
        )
        if exclude_booking_id:
            query = query.filter(RoomBooking.id != exclude_booking_id)

        conflicts = query.count()
        return conflicts == 0

    def create_booking(
        self,
        db: Session,
        user_id: str,
        user_role: str,
        room_id: str,
        title: str,
        purpose: str,
        start_time: datetime,
        end_time: datetime,
        equipment_required: Optional[List[str]] = None
    ) -> RoomBooking:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise CampusOpsException("Room not found.", 404)

        if not self.check_room_availability(db, room_id, start_time, end_time):
            raise BookingConflictError(
                room_name=room.name,
                conflict_details=f"Slot {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')} is already booked or room is unavailable."
            )

        # Check room equipment matches requirements
        if equipment_required and room.features:
            features = json.loads(room.features)
            missing = [eq for eq in equipment_required if eq not in features]
            if missing:
                raise CampusOpsException(f"Room lacks requested features: {missing}", 422)

        booking_count = db.query(RoomBooking).count()
        booking = RoomBooking(
            booking_code=f"BKG-{datetime.utcnow().strftime('%Y%m')}-{booking_count + 1:04d}",
            room_id=room_id,
            user_id=user_id,
            user_role=user_role,
            title=title,
            purpose=purpose,
            start_time=start_time,
            end_time=end_time,
            status="confirmed",
            equipment_required=json.dumps(equipment_required or [])
        )
        db.add(booking)
        db.flush()
        return booking

    def find_feasible_alternative_rooms(
        self,
        db: Session,
        required_capacity: int,
        required_features: List[str],
        start_time: datetime,
        end_time: datetime,
        exclude_room_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # Candidate rooms must have capacity >= required_capacity and status available
        rooms = db.query(Room).filter(
            Room.capacity >= required_capacity,
            Room.status == "available"
        ).all()

        feasible = []
        for r in rooms:
            if exclude_room_id and r.id == exclude_room_id:
                continue

            # Check features
            room_feats = json.loads(r.features) if r.features else []
            has_all_feats = all(f in room_feats for f in required_features)
            if not has_all_feats:
                continue

            # Check schedule availability
            if self.check_room_availability(db, r.id, start_time, end_time):
                feasible.append({
                    "room_id": r.id,
                    "room_number": r.room_number,
                    "name": r.name,
                    "capacity": r.capacity,
                    "features": room_feats,
                    "daily_readiness": r.daily_readiness_status,
                    "feasibility_score": 100 - (r.capacity - required_capacity)  # closer capacity match is preferred
                })

        feasible.sort(key=lambda x: x["feasibility_score"], reverse=True)
        return feasible

booking_service = BookingService()

