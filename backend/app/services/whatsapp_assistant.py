import json
import re
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.models.whatsapp import WhatsAppSession, WhatsAppMessageLog
from app.database.models.user import User
from app.database.models.campus import Building, Floor
from app.database.models.room import Room
from app.database.models.asset import Asset
from app.database.models.report import Report
from app.database.models.incident import Incident
from app.database.models.work_order import WorkOrder
from app.database.models.notification import NotificationOutbox
from app.services.ai_service import ai_service
from app.services.intake_service import intake_service
from app.services.whatsapp_service import whatsapp_service

class WhatsAppAssistant:
    """
    Intelligent WhatsApp Assistant for CampusOps.
    Handles conversational complaint registration (with multi-turn slot filling),
    grounded campus information retrieval, complaint tracking, and automatic notifications.
    """

    def get_or_create_session(self, db: Session, phone_number: str) -> WhatsAppSession:
        clean_phone = phone_number.replace("+", "").strip()
        session = db.query(WhatsAppSession).filter(WhatsAppSession.phone_number == clean_phone).first()
        if not session:
            # Check if there is an existing user with this phone number
            user = db.query(User).filter(
                or_(
                    User.phone_number == f"+{clean_phone}",
                    User.phone_number == clean_phone
                )
            ).first()

            session = WhatsAppSession(
                phone_number=clean_phone,
                user_id=user.id if user else None,
                current_intent=None,
                step="IDLE",
                context_data=json.dumps({})
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        return session

    def reset_session(self, db: Session, session: WhatsAppSession):
        session.current_intent = None
        session.step = "IDLE"
        session.context_data = json.dumps({})
        session.last_active_at = datetime.utcnow()
        db.commit()

    def handle_incoming_message(
        self,
        db: Session,
        from_phone: str,
        text: str,
        message_id: str
    ) -> str:
        """
        Main entry point for processing incoming WhatsApp messages.
        Returns the assistant's reply text.
        """
        clean_text = (text or "").strip()
        lower = clean_text.lower()
        session = self.get_or_create_session(db, from_phone)

        # 1. Global Reset / Cancel commands
        if lower in ["cancel", "reset", "stop", "restart", "start over"]:
            self.reset_session(db, session)
            reply = "Conversation reset. How can I help you today? You can:\n1. Report a campus issue\n2. Ask a question about campus\n3. Track an existing complaint"
            whatsapp_service.send_message(from_phone, reply, db=db)
            return reply

        # 2. Help command
        if lower in ["help", "hi", "hello", "menu", "hey", "options"] and session.step == "IDLE":
            reply = (
                "Hello! Welcome to CampusOps WhatsApp Assistant 🏛️\n\n"
                "I can assist you with:\n"
                "• *Registering a complaint* (e.g., 'The projector in Room 204 is broken')\n"
                "• *Campus information* (e.g., 'Where is Computer Science dept?', 'Who is the HOD of Engineering?', 'Where is the library?')\n"
                "• *Tracking your complaints* (e.g., 'Track my complaint', 'Status of CMP-1024')\n\n"
                "How may I assist you?"
            )
            whatsapp_service.send_message(from_phone, reply, db=db)
            return reply

        # 3. Handle active multi-turn session state
        if session.step != "IDLE":
            reply = self.handle_multi_turn_step(db, session, from_phone, clean_text)
            whatsapp_service.send_message(from_phone, reply, db=db)
            return reply

        # 4. Recognize Intent from IDLE state
        intent = self.detect_intent(clean_text)

        if intent == "TRACK_COMPLAINT":
            reply = self.handle_track_intent(db, session, from_phone, clean_text)
        elif intent == "CAMPUS_INFO":
            reply = self.handle_campus_info(db, clean_text)
        elif intent == "REGISTER_COMPLAINT":
            reply = self.start_complaint_registration(db, session, from_phone, clean_text)
        else:
            # Fallback to campus information retrieval or default guidance
            info_reply = self.handle_campus_info(db, clean_text)
            if "I couldn't find campus records" not in info_reply:
                reply = info_reply
            else:
                reply = (
                    "I didn't quite catch that. You can:\n"
                    "• Report an issue (e.g., 'Wi-Fi is not working in Lab A')\n"
                    "• Ask campus info (e.g., 'Where is the library?')\n"
                    "• Track a ticket (e.g., 'Track CMP-1024')\n"
                    "Or type 'help' for options."
                )

        whatsapp_service.send_message(from_phone, reply, db=db)
        return reply

    def detect_intent(self, text: str) -> str:
        lower = text.lower()

        # Track patterns
        if any(term in lower for term in ["track", "status of", "check ticket", "my complaint", "check complaint"]) or re.search(r"\b(cmp|rpt|inc)-[a-z0-9\-]+", lower):
            return "TRACK_COMPLAINT"

        # Complaint registration patterns
        complaint_triggers = [
            "not working", "broken", "issue", "fault", "damaged", "leak", "dirty", "power cut",
            "complaint", "report", "outage", "stopped", "no wifi", "no power", "spark", "flickering",
            "dropping continuously", "packet loss", "blackout"
        ]
        if any(term in lower for term in complaint_triggers):
            return "REGISTER_COMPLAINT"

        # Campus information patterns
        campus_triggers = [
            "where is", "who is", "which room", "which classroom", "available", "department",
            "hod", "head of", "faculty", "professor", "prof", "office", "library", "lab", "seminar hall",
            "building", "timing", "facility", "responsible", "contact"
        ]
        if any(term in lower for term in campus_triggers) or text.endswith("?"):
            return "CAMPUS_INFO"

        return "UNKNOWN"

    # =========================================================================
    # COMPLAINT REGISTRATION & MULTI-TURN FLOW
    # =========================================================================
    def start_complaint_registration(
        self,
        db: Session,
        session: WhatsAppSession,
        from_phone: str,
        text: str
    ) -> str:
        """Initiate natural language complaint intake and check for missing slots."""
        extraction = ai_service.extract_incident_entities(text)
        
        # Check if building is explicitly stated in user text
        explicit_building = None
        lower = text.lower()
        for b_name in ["engineering", "science", "library", "humanities", "administration", "innovation", "block a", "block b", "block c"]:
            if b_name in lower:
                explicit_building = b_name
                break

        ctx = {
            "initial_text": text,
            "category": extraction.get("category", "equipment"),
            "category_label": extraction.get("category_label", "Equipment"),
            "urgency": extraction.get("urgency", "medium"),
            "building_candidate": explicit_building,
            "room_candidate": extraction.get("location_room"),
            "asset_candidate": extraction.get("asset_candidate"),
            "resolved_building_id": None,
            "resolved_room_id": None,
            "resolved_asset_id": None,
            "issue_details": text
        }

        # Try to resolve room number/name from text (e.g. "Room 204", "101", "Lab A")
        room_match = re.search(r"\b(?:room|lab|hall)\s*([a-z0-9\-]+)\b", text, re.IGNORECASE)
        if room_match and not ctx["room_candidate"]:
            ctx["room_candidate"] = room_match.group(1)

        # Attempt database resolution
        self.resolve_locations_in_context(db, ctx)

        session.current_intent = "REGISTER_COMPLAINT"
        session.last_active_at = datetime.utcnow()

        # Slot filling checks
        # 1. Building missing -> ask user
        if not ctx["resolved_building_id"]:
            session.step = "AWAITING_BUILDING"
            session.context_data = json.dumps(ctx)
            db.commit()
            room_name = ctx.get("room_candidate") or "the room"
            return f"I can help you register this complaint. Which building is {room_name} in?"

        # 2. Room missing -> ask user
        if not ctx["resolved_room_id"]:
            session.step = "AWAITING_ROOM"
            session.context_data = json.dumps(ctx)
            db.commit()
            b_name = db.query(Building).filter(Building.id == ctx["resolved_building_id"]).first()
            b_str = b_name.name if b_name else "the building"
            return f"Thank you. What is the specific room number or lab name in {b_str}?"

        # 3. Ask for symptom details if user hasn't elaborated
        session.step = "AWAITING_DETAILS"
        session.context_data = json.dumps(ctx)
        db.commit()
        asset_str = ctx.get("asset_candidate") or "equipment"
        return f"Thank you. Is the {asset_str} completely not working or experiencing occasional problems?"

    def handle_multi_turn_step(
        self,
        db: Session,
        session: WhatsAppSession,
        from_phone: str,
        text: str
    ) -> str:
        """Handle user replies to clarifying questions."""
        ctx = json.loads(session.context_data or "{}")

        if session.step == "AWAITING_BUILDING":
            ctx["building_candidate"] = text
            self.resolve_locations_in_context(db, ctx)
            if not ctx["resolved_building_id"]:
                buildings = [b.name for b in db.query(Building).all()[:4]]
                return f"I couldn't locate that building. Please choose from: {', '.join(buildings)}."

            # Re-resolve room within the newly identified building
            if ctx.get("room_candidate"):
                self.resolve_locations_in_context(db, ctx)

            # Check if room is still missing
            if not ctx["resolved_room_id"]:
                session.step = "AWAITING_ROOM"
                session.context_data = json.dumps(ctx)
                db.commit()
                return "Thank you. What is the room number or name?"

            # Ask symptom details
            session.step = "AWAITING_DETAILS"
            session.context_data = json.dumps(ctx)
            db.commit()
            asset_str = ctx.get("asset_candidate") or "equipment"
            return f"Thank you. Is the {asset_str} completely not working or experiencing occasional problems?"

        elif session.step == "AWAITING_ROOM":
            ctx["room_candidate"] = text
            self.resolve_locations_in_context(db, ctx)
            if not ctx["resolved_room_id"]:
                return "I couldn't locate that room in the selected building. Please provide the room number (e.g., 204 or Lab A):"

            session.step = "AWAITING_DETAILS"
            session.context_data = json.dumps(ctx)
            db.commit()
            asset_str = ctx.get("asset_candidate") or "equipment"
            return f"Thank you. Is the {asset_str} completely not working or experiencing occasional problems?"

        elif session.step == "AWAITING_DETAILS":
            ctx["issue_details"] = f"{ctx.get('initial_text', '')}. Details: {text}"
            return self.finalize_complaint(db, session, from_phone, ctx)

        elif session.step == "AWAITING_TRACK_ID":
            return self.execute_complaint_tracking(db, session, from_phone, text)

        # Fallback
        self.reset_session(db, session)
        return "I've reset your request. How can I help you today?"

    def resolve_locations_in_context(self, db: Session, ctx: Dict[str, Any]):
        """Match candidates against database buildings, rooms, and assets."""
        # 1. Resolve building
        if ctx.get("building_candidate") and not ctx.get("resolved_building_id"):
            b_query = ctx["building_candidate"].strip().lower()
            b = db.query(Building).filter(
                or_(
                    Building.name.ilike(f"%{b_query}%"),
                    Building.code.ilike(f"%{b_query}%"),
                    Building.description.ilike(f"%{b_query}%")
                )
            ).first()
            # Handle block aliases e.g. "Block A" -> Engineering Block, "Block B" -> Science Block
            if not b:
                if "block a" in b_query or "eng" in b_query:
                    b = db.query(Building).filter(Building.code == "ENG").first()
                elif "block b" in b_query or "sci" in b_query:
                    b = db.query(Building).filter(Building.code == "SCI").first()
                elif "lib" in b_query:
                    b = db.query(Building).filter(Building.code == "LIB").first()
            if b:
                ctx["resolved_building_id"] = b.id
                ctx["building_name"] = b.name

        # 2. Resolve room
        if ctx.get("room_candidate") and not ctx.get("resolved_room_id"):
            r_query = ctx["room_candidate"].strip().lower()
            digits = re.findall(r"\d+", r_query)
            q = db.query(Room)
            if ctx.get("resolved_building_id"):
                q = q.filter(Room.building_id == ctx["resolved_building_id"])

            matched_room = None
            if digits:
                matched_room = q.filter(Room.room_number.ilike(f"%{digits[0]}%")).first()
            if not matched_room:
                matched_room = q.filter(
                    or_(
                        Room.name.ilike(f"%{r_query}%"),
                        Room.room_number.ilike(f"%{r_query}%")
                    )
                ).first()

            if matched_room:
                ctx["resolved_room_id"] = matched_room.id
                ctx["room_name"] = matched_room.name
                ctx["room_number"] = matched_room.room_number
                # Only set resolved_building_id if building_candidate was provided
                if ctx.get("building_candidate") and not ctx.get("resolved_building_id"):
                    ctx["resolved_building_id"] = matched_room.building_id
                    b = db.query(Building).filter(Building.id == matched_room.building_id).first()
                    ctx["building_name"] = b.name if b else "Campus"

        # 3. Resolve asset candidate
        if ctx.get("resolved_room_id") and not ctx.get("resolved_asset_id"):
            asset = db.query(Asset).filter(Asset.room_id == ctx["resolved_room_id"]).first()
            if asset:
                ctx["resolved_asset_id"] = asset.id
                ctx["asset_name"] = asset.name

    def finalize_complaint(
        self,
        db: Session,
        session: WhatsAppSession,
        from_phone: str,
        ctx: Dict[str, Any]
    ) -> str:
        """Persist complaint into existing CampusOps Incident/Report system."""
        user = None
        clean_p = from_phone.replace("+", "").strip()
        if session.user_id:
            user = db.query(User).filter(User.id == session.user_id).first()
        if not user:
            user = db.query(User).filter(
                or_(
                    User.phone_number == f"+{clean_p}",
                    User.phone_number == clean_p
                )
            ).first()

        # Default to key student if guest
        if not user:
            user = db.query(User).filter(User.role == "student").first()

        reporter_id = user.id if user else "u-whatsapp-guest"
        reporter_role = user.role if user else "student"

        building_name = ctx.get("building_name", "Campus")
        room_label = ctx.get("room_number") or ctx.get("room_name") or "Room"
        title = f"{ctx.get('category_label', 'Equipment')} Issue in {room_label}"
        desc = ctx.get("issue_details", ctx.get("initial_text", "WhatsApp complaint submission"))

        # Save via existing intake_service
        result = intake_service.process_incoming_report(
            db=db,
            reporter_id=reporter_id,
            reporter_role=reporter_role,
            title=title,
            description=desc,
            building_id=ctx.get("resolved_building_id"),
            room_id=ctx.get("resolved_room_id"),
            asset_id=ctx.get("resolved_asset_id"),
            category=ctx.get("category", "equipment"),
            urgency=ctx.get("urgency", "medium"),
            source="whatsapp",
            contact_phone=f"+{clean_p}"
        )
        report: Report = result["report"]

        # Check duplicate
        is_duplicate = result.get("matched_existing_incident", False)
        db.commit()

        display_code = report.report_code.replace("RPT-", "CMP-")
        priority_display = "Medium"
        if report.urgency == "critical":
            priority_display = "High"
        elif report.urgency == "low":
            priority_display = "Low"

        location_str = f"{building_name}, Room {ctx.get('room_number', room_label)}"

        self.reset_session(db, session)

        reply = (
            "Your complaint has been registered successfully.\n\n"
            f"Complaint ID: {display_code}\n"
            f"Category: {ctx.get('category_label', 'Equipment')}\n"
            f"Location: {location_str}\n"
            f"Priority: {priority_display}\n"
            "Status: Submitted"
        )

        if is_duplicate:
            reply += "\n\n*(Note: Our AI correlation engine identified similar active reports in this location. Your report has been merged for prioritized response.)*"

        return reply

    # =========================================================================
    # CAMPUS INFORMATION ASSISTANT (DB GROUNDED)
    # =========================================================================
    def handle_campus_info(self, db: Session, query: str) -> str:
        """Ground campus inquiries directly in database tables."""
        lower = query.lower()

        # 1. HOD / Department Head queries
        if any(term in lower for term in ["hod", "head of department", "head of"]):
            dept_managers = db.query(User).filter(User.sub_role == "department_manager").all()
            for dm in dept_managers:
                if (dm.department or "").lower() in lower or "engineering" in lower:
                    b = db.query(Building).filter(Building.id == dm.building_id).first()
                    b_str = b.name if b else "Engineering Block"
                    return f"The Head of Department for {dm.department} is {dm.name}.\nOffice: {b_str}, Level 1\nEmail: {dm.email}"

            if dept_managers:
                lines = [f"• {dm.department}: {dm.name} ({dm.email})" for dm in dept_managers]
                return "Campus Department Heads:\n" + "\n".join(lines)

        # 2. Specific Faculty member / Professor office or contact
        faculty_match = re.search(r"(?:prof|professor|dr|doctor)\.?\s+([a-z]+)", lower)
        if faculty_match or "finch" in lower or "smith" in lower or "chen" in lower or "kumar" in lower:
            name_term = faculty_match.group(1) if faculty_match else "finch"
            if "finch" in lower:
                name_term = "finch"
            elif "smith" in lower:
                name_term = "smith"
            elif "chen" in lower:
                name_term = "chen"
            elif "kumar" in lower:
                name_term = "kumar"

            faculty = db.query(User).filter(
                User.role == "faculty",
                User.name.ilike(f"%{name_term}%")
            ).first()

            if faculty:
                b = db.query(Building).filter(Building.id == faculty.building_id).first()
                b_str = b.name if b else "Campus Building"
                return (
                    f"Faculty Profile: {faculty.name}\n"
                    f"Department: {faculty.department}\n"
                    f"Office Location: {b_str}, Faculty Room (Level 1)\n"
                    f"Email: {faculty.email}"
                )

        # 3. Department location
        if "department" in lower or "dept" in lower:
            for dept_name, b_code in [
                ("computer science", "ENG"),
                ("engineering", "ENG"),
                ("robotics", "ENG"),
                ("physics", "SCI"),
                ("chemistry", "SCI"),
                ("science", "SCI"),
                ("humanities", "HUM"),
                ("arts", "HUM"),
                ("library", "LIB"),
                ("administration", "ADM"),
                ("innovation", "INN")
            ]:
                if dept_name in lower:
                    b = db.query(Building).filter(Building.code == b_code).first()
                    if b:
                        return f"The {dept_name.capitalize()} Department is located in the *{b.name}* ({b.description})."

        # 4. Library location & facilities
        if "library" in lower:
            lib = db.query(Building).filter(Building.code == "LIB").first()
            if lib:
                rooms = db.query(Room).filter(Room.building_id == lib.id).all()
                r_names = [r.name for r in rooms[:4]]
                return (
                    f"The Central Campus Library is in the *{lib.name}*.\n"
                    f"Floors: {lib.total_floors} levels\n"
                    f"Facilities: Central Reading Room, Digital Archives Lab, AV Suite, Quiet Graduate Study Rooms.\n"
                    f"Key Spaces: {', '.join(r_names)}"
                )

        # 5. Classrooms availability query
        if "available" in lower and ("classroom" in lower or "room" in lower):
            avail_rooms = db.query(Room).filter(
                Room.status == "available",
                Room.type.in_(["classroom", "seminar_hall", "lab"])
            ).limit(5).all()

            if avail_rooms:
                lines = []
                for r in avail_rooms:
                    b = db.query(Building).filter(Building.id == r.building_id).first()
                    lines.append(f"• {r.name} (Room {r.room_number}, {b.name if b else ''}) - Cap: {r.capacity}")
                return "Currently available campus spaces:\n" + "\n".join(lines)

        # 6. Specific Room or Seminar Hall query
        if "seminar hall" in lower or "auditorium" in lower or "exam hall" in lower or "lab" in lower:
            room_type = "seminar_hall"
            if "exam hall" in lower or "auditorium" in lower:
                room_type = "exam_hall"
            elif "lab" in lower:
                room_type = "lab"

            matched_rooms = db.query(Room).filter(Room.type == room_type).limit(4).all()
            if matched_rooms:
                lines = []
                for r in matched_rooms:
                    b = db.query(Building).filter(Building.id == r.building_id).first()
                    lines.append(f"• {r.name} in {b.name if b else 'Campus'} (Capacity: {r.capacity})")
                return f"Campus {room_type.replace('_', ' ').capitalize()} locations:\n" + "\n".join(lines)

        # 7. Building specific inquiry
        for b in db.query(Building).all():
            if b.name.lower() in lower or b.code.lower() in lower:
                rooms = db.query(Room).filter(Room.building_id == b.id).limit(5).all()
                room_list = ", ".join([f"{r.name} ({r.room_number})" for r in rooms])
                return (
                    f"*{b.name}* ({b.code}):\n"
                    f"Description: {b.description}\n"
                    f"Total Floors: {b.total_floors}\n"
                    f"Featured Rooms: {room_list}"
                )

        # 8. Maintenance / Facility responsibility
        if any(term in lower for term in ["responsible", "maintenance issue", "report issue", "who can i contact"]):
            fac_admin = db.query(User).filter(User.sub_role == "facilities_admin").first()
            floor_inc = db.query(User).filter(User.sub_role == "floor_incharge").first()
            admin_name = fac_admin.name if fac_admin else "Facilities Administration"
            inc_name = floor_inc.name if floor_inc else "Floor Incharge"
            return (
                "Facilities & Maintenance Contacts:\n"
                f"• Facilities Administrator: {admin_name} (facilities@campusops.edu)\n"
                f"• Operational Floor Incharge: {inc_name} (floor_incharge@campusops.edu)\n"
                "You can also report any physical fault directly in this WhatsApp chat!"
            )

        # Grounded truth fallback: never hallucinate!
        return (
            "I couldn't find campus records matching your exact inquiry. "
            "Please check the Administration Block (Level 1) or email helpdesk@campusops.edu."
        )

    # =========================================================================
    # COMPLAINT TRACKING & OWNERSHIP VERIFICATION
    # =========================================================================
    def handle_track_intent(
        self,
        db: Session,
        session: WhatsAppSession,
        from_phone: str,
        text: str
    ) -> str:
        """Handle tracking request. Extract ticket ID or prompt for it."""
        match = re.search(r"\b(cmp|rpt|inc)-[a-z0-9\-]+\b", text, re.IGNORECASE)
        if match:
            return self.execute_complaint_tracking(db, session, from_phone, match.group(0))

        # Check if user has complaints associated with their phone number
        clean_p = from_phone.replace("+", "").strip()
        user_reports = db.query(Report).filter(
            or_(
                Report.contact_phone.like(f"%{clean_p}%"),
                Report.reporter_id == (session.user_id or "none")
            )
        ).order_by(Report.created_at.desc()).limit(3).all()

        if user_reports:
            lines = [f"• {r.report_code.replace('RPT-', 'CMP-')} - {r.title} ({r.status.capitalize()})" for r in user_reports]
            session.step = "AWAITING_TRACK_ID"
            db.commit()
            return (
                "Here are your recent registered complaints:\n" +
                "\n".join(lines) +
                "\n\nPlease reply with the Complaint ID you would like to track in detail."
            )

        session.step = "AWAITING_TRACK_ID"
        db.commit()
        return "Please provide your complaint ID."

    def execute_complaint_tracking(
        self,
        db: Session,
        session: WhatsAppSession,
        from_phone: str,
        ticket_id: str
    ) -> str:
        """Search and verify authorization for complaint tracking."""
        clean_id = ticket_id.strip().upper()
        search_code = clean_id.replace("CMP-", "RPT-")

        report = db.query(Report).filter(
            or_(
                Report.report_code == search_code,
                Report.report_code == clean_id,
                Report.id == clean_id
            )
        ).first()

        incident = None
        if not report:
            incident = db.query(Incident).filter(
                or_(
                    Incident.incident_code == clean_id,
                    Incident.id == clean_id
                )
            ).first()

        if not report and not incident:
            self.reset_session(db, session)
            return f"No complaint record found matching ID '{clean_id}'. Please verify the ticket number and try again."

        # Ownership verification
        clean_from = from_phone.replace("+", "").strip()
        is_authorized = False

        # 1. Check if report's contact_phone matches sender
        if report and report.contact_phone:
            rep_clean_p = report.contact_phone.replace("+", "").strip()
            if rep_clean_p == clean_from or clean_from.endswith(rep_clean_p[-8:]):
                is_authorized = True

        # 2. Check if user account phone matches
        if not is_authorized and session.user_id:
            user = db.query(User).filter(User.id == session.user_id).first()
            if user:
                # Admins and technicians can track all complaints
                if user.role in ["admin", "technician"]:
                    is_authorized = True
                elif report and report.reporter_id == user.id:
                    is_authorized = True

        if not is_authorized:
            self.reset_session(db, session)
            return (
                "Unauthorized: This complaint is associated with another campus user. "
                "You can only track complaints submitted from your registered phone number."
            )

        # Retrieve status, technician, and location
        target_incident = None
        if report and report.incident_id:
            target_incident = db.query(Incident).filter(Incident.id == report.incident_id).first()
        elif incident:
            target_incident = incident

        assigned_tech_name = "Not yet assigned"
        status_display = report.status if report else incident.status

        if target_incident:
            status_display = target_incident.status
            # Check work orders for assigned technician
            wo = db.query(WorkOrder).filter(WorkOrder.incident_id == target_incident.id).first()
            if wo and wo.assigned_technician_id:
                tech = db.query(User).filter(User.id == wo.assigned_technician_id).first()
                if tech:
                    assigned_tech_name = tech.name

        # Location string
        b_id = report.building_id if report else target_incident.building_id
        r_id = report.room_id if report else target_incident.room_id
        building = db.query(Building).filter(Building.id == b_id).first()
        room = db.query(Room).filter(Room.id == r_id).first()

        location_str = f"{building.name if building else 'Campus'}, Room {room.room_number if room else 'General'}"
        category_str = (report.category if report else target_incident.category).capitalize()
        status_formatted = status_display.replace("_", " ").title()

        last_updated = (report.updated_at if report else target_incident.updated_at).strftime("%Y-%m-%d %H:%M UTC")

        self.reset_session(db, session)

        return (
            "Complaint Details:\n\n"
            f"ID: {clean_id}\n"
            f"Category: {category_str}\n"
            f"Location: {location_str}\n"
            f"Status: {status_formatted}\n"
            f"Assigned Technician: {assigned_tech_name}\n"
            f"Last Updated: {last_updated}"
        )

    # =========================================================================
    # AUTOMATIC STATUS NOTIFICATIONS
    # =========================================================================
    def notify_incident_state_change(
        self,
        db: Session,
        incident_id: str,
        event_type: str,  # assigned, in_progress, resolved
        technician_name: Optional[str] = None
    ):
        """
        Broadcast automatic WhatsApp status notifications to original complainants.
        Prevents duplicate notifications for the same state change.
        """
        reports = db.query(Report).filter(Report.incident_id == incident_id).all()
        for rep in reports:
            target_phone = rep.contact_phone
            if not target_phone and rep.reporter_id:
                u = db.query(User).filter(User.id == rep.reporter_id).first()
                if u and u.phone_number:
                    target_phone = u.phone_number

            if not target_phone:
                continue

            cmp_id = rep.report_code.replace("RPT-", "CMP-")

            if event_type == "assigned":
                msg = f"Your complaint {cmp_id} has been assigned to a technician ({technician_name or 'Field Support'})."
            elif event_type == "in_progress":
                msg = f"Your complaint {cmp_id} is now being addressed."
            elif event_type == "resolved":
                msg = f"Your complaint {cmp_id} has been marked as resolved."
            else:
                msg = f"Your complaint {cmp_id} status updated to: {event_type.replace('_', ' ').capitalize()}."

            already_sent = db.query(NotificationOutbox).filter(
                NotificationOutbox.recipient_phone == target_phone,
                NotificationOutbox.subject == f"whatsapp_{event_type}_{cmp_id}"
            ).first()

            if not already_sent:
                whatsapp_service.send_message(
                    to_phone=target_phone,
                    text=msg,
                    db=db,
                    notification_type=f"whatsapp_{event_type}_{cmp_id}"
                )

whatsapp_assistant = WhatsAppAssistant()
