import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.database.models.user import User
from app.database.models.whatsapp import WhatsAppUserLink
from app.database.models.incident import Incident
from app.database.models.report import Report
from app.database.models.work_order import WorkOrder
from app.database.models.campus import Building
from app.database.models.room import Room
from app.services.sla_service import sla_service
from app.services.notification_service import notification_service

logger = logging.getLogger("whatsapp_ticket_service")

class WhatsAppTicketService:
    # ---------------------------------------------------------
    # 1. Identity & Phone Linking
    # ---------------------------------------------------------
    def generate_link_code(self, db: Session, user: User, phone_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates a secure 6-digit link code for an authenticated user to connect WhatsApp.
        Expires in 15 minutes.
        """
        code = f"{random.randint(100000, 999999)}"
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        clean_phone = phone_number.replace("+", "").strip() if phone_number else None

        existing_link = db.query(WhatsAppUserLink).filter(WhatsAppUserLink.user_id == user.id).first()
        if existing_link:
            existing_link.verification_code = code
            existing_link.code_expires_at = expires_at
            if clean_phone:
                existing_link.phone_number = clean_phone
        else:
            dummy_phone = clean_phone or f"pending_{user.id[:8]}"
            link = WhatsAppUserLink(
                user_id=user.id,
                phone_number=dummy_phone,
                verification_code=code,
                code_expires_at=expires_at,
                is_verified=False
            )
            db.add(link)

        db.commit()
        return {
            "link_code": code,
            "expires_in_minutes": 15,
            "instructions": f"From WhatsApp, send: LINK {code}"
        }

    def verify_link_code(self, db: Session, phone_number: str, code: str) -> Optional[User]:
        """
        Verifies the 6-digit code sent from a user's WhatsApp and ties the phone number to the account.
        """
        clean_phone = phone_number.replace("+", "").strip()
        clean_code = code.strip()

        now = datetime.utcnow()
        link = (
            db.query(WhatsAppUserLink)
            .filter(
                WhatsAppUserLink.verification_code == clean_code,
                WhatsAppUserLink.code_expires_at >= now
            )
            .first()
        )

        if not link:
            return None

        user = db.query(User).filter(User.id == link.user_id).first()
        if not user:
            return None

        # Bind phone number
        link.phone_number = clean_phone
        link.is_verified = True
        link.verified_at = now
        link.verification_code = None

        user.phone_number = clean_phone
        user.whatsapp_verified = True

        db.commit()
        db.refresh(user)
        return user

    def get_user_by_phone(self, db: Session, phone_number: str) -> Optional[User]:
        """Retrieves a verified CampusOps user by their WhatsApp phone number."""
        clean_phone = phone_number.replace("+", "").strip()
        link = (
            db.query(WhatsAppUserLink)
            .filter(
                WhatsAppUserLink.phone_number == clean_phone,
                WhatsAppUserLink.is_verified == True
            )
            .first()
        )
        if link:
            return db.query(User).filter(User.id == link.user_id).first()

        # Fallback check on User table
        return db.query(User).filter(User.phone_number == clean_phone, User.whatsapp_verified == True).first()

    # ---------------------------------------------------------
    # 2. Location Validation
    # ---------------------------------------------------------
    def resolve_location(self, db: Session, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Matches extracted building and room names against verified database entries.
        """
        raw_room = (location_data.get("room") or "").strip()
        raw_building = (location_data.get("building") or "").strip()

        matched_room = None
        matched_building = None

        if raw_room:
            # Try exact room_number match
            matched_room = db.query(Room).filter(Room.room_number.ilike(raw_room)).first()
            if not matched_room:
                # Try partial name match
                matched_room = db.query(Room).filter(Room.name.ilike(f"%{raw_room}%")).first()

        if matched_room:
            matched_building = db.query(Building).filter(Building.id == matched_room.building_id).first()

        if not matched_building and raw_building:
            matched_building = db.query(Building).filter(Building.name.ilike(f"%{raw_building}%")).first()

        if not matched_building:
            matched_building = db.query(Building).first()

        return {
            "room_id": matched_room.id if matched_room else None,
            "room_code": matched_room.room_number if matched_room else (raw_room or "General Space"),
            "building_id": matched_building.id if matched_building else None,
            "building_name": matched_building.name if matched_building else (raw_building or "Campus Grounds")
        }

    # ---------------------------------------------------------
    # 3. Automatic Ticket Creation
    # ---------------------------------------------------------
    def create_ticket_from_whatsapp(
        self,
        db: Session,
        user: User,
        data: Dict[str, Any]
    ) -> Incident:
        """
        Creates an official CampusOps Report and Incident from confirmed WhatsApp details.
        """
        location = self.resolve_location(db, data.get("location", {}))
        category = data.get("category") or "General Maintenance"
        description = data.get("description") or "Reported via WhatsApp Assistant"
        priority = data.get("priority_recommendation") or "NORMAL"

        priority_map = {
            "CRITICAL": "P1",
            "HIGH": "P2",
            "NORMAL": "P3",
            "LOW": "P4"
        }
        db_priority = priority_map.get(priority.upper(), "P3")
        sla_due = sla_service.calculate_deadline(db_priority)

        inc_count = db.query(Incident).count()
        incident_code = f"COP-{1000 + inc_count + 1}"

        incident = Incident(
            incident_code=incident_code,
            title=f"{category} issue in {location['room_code']}",
            description=description,
            category=category.lower(),
            severity="high" if db_priority in ["P1", "P2"] else "medium",
            priority=db_priority,
            building_id=location["building_id"],
            room_id=location["room_id"],
            status="open",
            sla_due_at=sla_due,
            is_sla_breached=False,
            correlated_count=1,
            summary=f"Automated WhatsApp ticket opened by {user.name} ({user.role})."
        )
        db.add(incident)
        db.flush()

        # Create linked report
        report_count = db.query(Report).count()
        report = Report(
            report_code=f"RPT-{datetime.utcnow().strftime('%Y%m')}-{report_count + 1:04d}",
            title=incident.title,
            description=description,
            category=category.lower(),
            urgency="high" if db_priority in ["P1", "P2"] else "medium",
            building_id=location["building_id"],
            room_id=location["room_id"],
            reporter_id=user.id,
            reporter_role=user.role,
            source="whatsapp",
            status="correlated",
            incident_id=incident.id
        )
        db.add(report)
        db.commit()
        db.refresh(incident)

        logger.info(f"[WhatsApp] Created ticket {incident.incident_code} for user {user.email}")
        return incident

    # ---------------------------------------------------------
    # 4. Ticket Status Queries
    # ---------------------------------------------------------
    def query_user_tickets(self, db: Session, user: User, query_code: Optional[str] = None) -> str:
        """
        Retrieves user's active tickets. If query_code is given, checks that specific ticket.
        Strictly enforces user-level authorization so users never view other people's tickets.
        """
        # 1. Specific ticket lookup
        if query_code:
            clean_code = query_code.strip().upper()
            incident = db.query(Incident).filter(Incident.incident_code == clean_code).first()
            if not incident:
                return f"Could not find any ticket with code {clean_code}. Please verify the ticket reference number."

            # Verify ownership: check if user is reporter of any linked report or admin
            if user.role != "admin":
                is_owner = db.query(Report).filter(
                    Report.incident_id == incident.id,
                    Report.reporter_id == user.id
                ).first()
                if not is_owner:
                    return f"Ticket {clean_code} is restricted. You may only view tickets that you personally submitted."

            wo = db.query(WorkOrder).filter(WorkOrder.incident_id == incident.id).first()
            tech_name = "Not yet assigned"
            if wo and wo.assigned_technician_id:
                tech = db.query(User).filter(User.id == wo.assigned_technician_id).first()
                if tech:
                    tech_name = tech.name

            room = db.query(Room).filter(Room.id == incident.room_id).first() if incident.room_id else None
            loc = room.room_number if room else "Campus Facility"

            return (
                f"📋 *Ticket Details: {incident.incident_code}*\n\n"
                f"• *Title:* {incident.title}\n"
                f"• *Status:* {incident.status.replace('_', ' ').title()}\n"
                f"• *Priority:* {incident.priority}\n"
                f"• *Location:* {loc}\n"
                f"• *Technician:* {tech_name}\n"
                f"• *Logged:* {incident.created_at.strftime('%d %b %Y, %I:%M %p')}\n\n"
                f"You will automatically receive WhatsApp updates as work progresses."
            )

        # 2. List all tickets for current user
        reports = (
            db.query(Report)
            .filter(Report.reporter_id == user.id)
            .order_by(Report.created_at.desc())
            .limit(5)
            .all()
        )

        if not reports:
            return (
                "You currently have no tickets registered under this account.\n\n"
                "To report a new issue, simply send a description (e.g. 'Projector broken in Room 204')."
            )

        lines = ["📋 *Your Recent CampusOps Tickets:*"]
        for r in reports:
            inc = db.query(Incident).filter(Incident.id == r.incident_id).first() if r.incident_id else None
            code = inc.incident_code if inc else r.report_code
            status = (inc.status if inc else r.status).replace("_", " ").title()
            lines.append(f"• *{code}* — {r.title} ({status})")

        lines.append("\nTo inspect any ticket, reply with: *Check <Ticket ID>*")
        return "\n".join(lines)

whatsapp_ticket_service = WhatsAppTicketService()

