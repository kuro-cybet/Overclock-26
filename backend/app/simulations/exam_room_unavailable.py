import json
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database.models.room import Room
from app.database.models.booking import RoomBooking
from app.services.recovery_service import recovery_service
from app.database.models.audit import AuditLog

class ExamRoomUnavailableSimulation:
    def trigger(self, db: Session, room_number: str = "ENG-101") -> Dict[str, Any]:
        # 1. Capture before state
        room = db.query(Room).filter(Room.room_number.like(f"%{room_number}%")).first()
        if not room:
            room = db.query(Room).first()

        before_state = {
            "room_id": room.id,
            "room_name": room.name,
            "room_status": room.status,
            "readiness": room.daily_readiness_status
        }

        # 2. Find upcoming exam booking in this room
        booking = db.query(RoomBooking).filter(
            RoomBooking.room_id == room.id,
            RoomBooking.purpose == "examination",
            RoomBooking.status == "confirmed"
        ).first()

        if not booking:
            # Create exam booking 30 minutes from now if none found
            now = datetime.utcnow()
            booking = RoomBooking(
                booking_code=f"BKG-SIM-EXAM",
                room_id=room.id,
                user_id="faculty-lead",
                user_role="faculty",
                title="CS304: Distributed Systems Examination",
                purpose="examination",
                start_time=now + timedelta(minutes=30),
                end_time=now + timedelta(minutes=150),
                status="confirmed",
                equipment_required=json.dumps(["wifi", "lab_pcs"])
            )
            db.add(booking)
            db.flush()

        booking_before = {
            "booking_id": booking.id,
            "title": booking.title,
            "start_time": booking.start_time.isoformat(),
            "status": booking.status,
            "room_id": booking.room_id
        }

        # 3. Simulate failure: Mark exam room unavailable shortly before exam
        room.status = "unavailable"
        room.daily_readiness_status = "unconfirmed"

        # 4. Generate recovery options
        recovery_plan = recovery_service.generate_recovery_plan(
            db=db,
            disruption_type="exam_room_unavailable",
            entity_id=room.id
        )

        after_state = {
            "room_id": room.id,
            "room_name": room.name,
            "room_status": room.status,
            "readiness": room.daily_readiness_status,
            "active_disruption": True
        }

        # Audit
        audit = AuditLog(
            action="SIMULATION_EXAM_ROOM_UNAVAILABLE",
            actor_id="admin-sim",
            actor_role="admin",
            entity_type="room",
            entity_id=room.id,
            old_value=json.dumps(before_state),
            new_value=json.dumps(after_state),
            reason="Scenario Simulator: Examination room marked unavailable shortly before exam"
        )
        db.add(audit)
        db.flush()

        return {
            "scenario": "examination_room_unavailable",
            "summary": f"Room '{room.name}' ({room.room_number}) set to 'unavailable' with upcoming exam scheduled.",
            "before_state": {"room": before_state, "booking": booking_before},
            "after_state": {"room": after_state, "booking": booking_before},
            "recovery_options": recovery_plan["options"],
            "requires_action": True
        }

exam_room_sim = ExamRoomUnavailableSimulation()

