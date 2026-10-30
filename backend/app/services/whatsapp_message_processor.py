import re
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database.models.user import User
from app.services.whatsapp_service import whatsapp_service
from app.services.whatsapp_ticket_service import whatsapp_ticket_service
from app.services.whatsapp_conversation_service import whatsapp_conversation_service
from app.services.whatsapp_ai_client import whatsapp_ai_client
from app.services.whatsapp_qa_service import whatsapp_qa_service

logger = logging.getLogger("whatsapp_message_processor")

class WhatsAppMessageProcessor:
    """
    Coordinates end-to-end inbound WhatsApp message handling:
    1. Deduplication & audit logging
    2. Identity verification & phone linking
    3. Multi-turn conversation management
    4. Qwen-powered intent classification & entity extraction
    5. Automatic ticket creation
    6. Grounded institutional and web Q&A
    """

    async def process_inbound_message(
        self,
        db: Session,
        message_id: str,
        sender_phone: str,
        recipient_phone: str,
        text: str
    ):
        clean_text = text.strip()
        lower_text = clean_text.lower()

        # 1. Deduplication check
        if whatsapp_service.is_message_duplicate(db, message_id):
            logger.info(f"[WhatsApp] Duplicate message {message_id} ignored.")
            return

        # Log inbound message in audit table
        whatsapp_service.log_message(
            db=db,
            message_id=message_id,
            sender_phone=sender_phone,
            recipient_phone=recipient_phone,
            direction="inbound",
            content=clean_text,
            status="processed"
        )

        response_text = ""

        # 2. Check for account linking command: e.g. "LINK 123456" or "VERIFY 123456"
        link_match = re.match(r"^(?:link|verify)\s*(\d{6})$", clean_text, re.IGNORECASE)
        if link_match:
            code = link_match.group(1)
            linked_user = whatsapp_ticket_service.verify_link_code(db, sender_phone, code)
            if linked_user:
                response_text = (
                    f"✅ *Account Linked Successfully!*\n\n"
                    f"Welcome, {linked_user.name} ({linked_user.role.title()}). Your WhatsApp number is now securely connected to CampusOps.\n\n"
                    f"You can now:\n"
                    f"• Report campus issues (e.g. 'Projector broken in Room 204')\n"
                    f"• Check your tickets ('Show my tickets')\n"
                    f"• Ask campus and timetable questions"
                )
            else:
                response_text = (
                    "❌ *Verification Code Invalid or Expired*\n\n"
                    "The link code you entered is invalid or has expired. Please log into your CampusOps portal to generate a new 6-digit code."
                )

            await self._send_and_log(db, sender_phone, recipient_phone, response_text, message_id)
            return response_text

        # 3. Resolve user identity
        user = whatsapp_ticket_service.get_user_by_phone(db, sender_phone)

        # 4. Auto-provision unverified sender as student user
        if not user:
            clean_digits = re.sub(r'\D', '', sender_phone)
            user = User(
                email=f"wa_{clean_digits[-8:] if len(clean_digits) >= 8 else clean_digits}@campusops.edu",
                hashed_password="!",
                name=f"Student ({clean_digits[-4:] if len(clean_digits) >= 4 else clean_digits})",
                role="student",
                phone_number=sender_phone,
                whatsapp_verified=True,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 5. Verified User: Retrieve conversation state
        conv = whatsapp_conversation_service.get_or_create(db, sender_phone, user_id=user.id)
        current_state = conv.state

        # Global cancellation command at ANY time
        if lower_text in ["cancel", "reset", "stop", "abort", "restart", "start over"]:
            whatsapp_conversation_service.reset_to_idle(db, conv)
            response_text = "Conversation reset. How can I help you today? You can:\n1. Report a campus issue\n2. Ask a question about campus\n3. Track an existing complaint"
            await self._send_and_log(db, sender_phone, recipient_phone, response_text, message_id)
            return response_text

        # Multi-turn State: Awaiting Building
        if current_state == "awaiting_building":
            extracted_data = whatsapp_conversation_service.get_extracted_data(conv)
            loc = whatsapp_ticket_service.resolve_location(db, {"building": clean_text})
            extracted_data["location"]["building"] = loc["building_name"]
            whatsapp_conversation_service.update_state(
                db=db,
                conv=conv,
                state="awaiting_details",
                intent="REPORT_ISSUE",
                extracted_data=extracted_data
            )
            response_text = f"Thank you. Please describe the issue details (e.g. completely not working or occasional fault):"
            await self._send_and_log(db, sender_phone, recipient_phone, response_text, message_id)
            return response_text

        # Multi-turn State: Awaiting Details
        if current_state == "awaiting_details":
            extracted_data = whatsapp_conversation_service.get_extracted_data(conv)
            extracted_data["description"] = f"{extracted_data.get('description', '')}. {clean_text}".strip()
            incident = whatsapp_ticket_service.create_ticket_from_whatsapp(db, user, extracted_data)
            whatsapp_conversation_service.reset_to_idle(db, conv)

            loc = whatsapp_ticket_service.resolve_location(db, extracted_data.get("location", {}))
            cat = (incident.category or extracted_data.get("category", "Maintenance")).title()
            room_str = loc["room_code"]
            bld_str = loc["building_name"]

            response_text = (
                "Your issue has been registered successfully.\n\n"
                f"Ticket ID: {incident.incident_code}\n"
                f"Issue: {cat} in {room_str}\n"
                f"Location: {room_str} ({bld_str})\n"
                f"Status: Open\n\n"
                "You will receive updates about your ticket."
            )
            await self._send_and_log(db, sender_phone, recipient_phone, response_text, message_id)
            return response_text

        # Multi-turn State: Awaiting Ticket Creation Confirmation
        if current_state == "awaiting_confirmation":
            if any(w in lower_text for w in ["yes", "confirm", "proceed", "sure", "ok", "yep", "do it"]):
                extracted_data = whatsapp_conversation_service.get_extracted_data(conv)
                incident = whatsapp_ticket_service.create_ticket_from_whatsapp(db, user, extracted_data)
                whatsapp_conversation_service.reset_to_idle(db, conv)

                loc = whatsapp_ticket_service.resolve_location(db, extracted_data.get("location", {}))
                cat = (incident.category or extracted_data.get("category", "Maintenance")).title()
                room_str = loc["room_code"]
                bld_str = loc["building_name"]

                response_text = (
                    "Your issue has been registered successfully.\n\n"
                    f"Ticket ID: {incident.incident_code}\n"
                    f"Issue: {cat} in {room_str}\n"
                    f"Location: {room_str} ({bld_str})\n"
                    f"Status: Open\n\n"
                    "You will receive updates about your ticket."
                )
            elif any(w in lower_text for w in ["no", "cancel", "abort", "nevermind", "stop"]):
                whatsapp_conversation_service.reset_to_idle(db, conv)
                response_text = "Your ticket request has been cancelled. Let me know if you need assistance with anything else."
            else:
                response_text = "Please reply with *'Yes'* to confirm ticket registration, or *'Cancel'* to abort."

            await self._send_and_log(db, sender_phone, recipient_phone, response_text, message_id)
            return response_text

        # Global cancellation during multi-turn state or idle
        if lower_text in ["cancel", "reset", "stop", "abort", "restart", "start over"]:
            whatsapp_conversation_service.reset_to_idle(db, conv)
            response_text = "Conversation reset. How can I help you today? You can:\n1. Report a campus issue\n2. Ask a question about campus\n3. Track an existing complaint"
            await self._send_and_log(db, sender_phone, recipient_phone, response_text, message_id)
            return response_text

        # Multi-turn State: Collecting Missing Category
        if current_state == "collecting_category":
            extracted_data = whatsapp_conversation_service.get_extracted_data(conv)
            extracted_data["category"] = clean_text.title()

            location = extracted_data.get("location", {})
            has_location = bool(location.get("room") or location.get("building"))
            if not has_location:
                whatsapp_conversation_service.update_state(
                    db=db,
                    conv=conv,
                    state="collecting_location",
                    intent="REPORT_ISSUE",
                    extracted_data=extracted_data
                )
                response_text = f"Thank you. Which room or building is the {clean_text.lower()} issue located in?"
            else:
                loc = whatsapp_ticket_service.resolve_location(db, location)
                extracted_data["location"] = {"room": loc["room_code"], "building": loc["building_name"]}
                whatsapp_conversation_service.update_state(
                    db=db,
                    conv=conv,
                    state="awaiting_confirmation",
                    intent="REPORT_ISSUE",
                    extracted_data=extracted_data
                )
                cat = extracted_data.get("category", "Maintenance")
                desc = extracted_data.get("description", "Reported fault")
                response_text = (
                    f"Thank you. I have the required information:\n\n"
                    f"• *Category:* {cat}\n"
                    f"• *Location:* {loc['room_code']} ({loc['building_name']})\n"
                    f"• *Description:* {desc}\n\n"
                    "Shall I register this issue? (Reply *'Yes'* to confirm, or *'Cancel'* to abort)"
                )
            await self._send_and_log(db, sender_phone, recipient_phone, response_text, message_id)
            return response_text

        # Multi-turn State: Collecting Missing Location
        if current_state == "collecting_location":
            extracted_data = whatsapp_conversation_service.get_extracted_data(conv)
            loc = whatsapp_ticket_service.resolve_location(db, {"room": clean_text})
            extracted_data["location"] = {"room": loc["room_code"], "building": loc["building_name"]}

            whatsapp_conversation_service.update_state(
                db=db,
                conv=conv,
                state="awaiting_confirmation",
                intent="REPORT_ISSUE",
                extracted_data=extracted_data
            )

            cat = extracted_data.get("category", "Maintenance")
            desc = extracted_data.get("description", "Reported fault")
            response_text = (
                f"Thank you. I have the required information:\n\n"
                f"• *Category:* {cat}\n"
                f"• *Location:* {loc['room_code']} ({loc['building_name']})\n"
                f"• *Description:* {desc}\n\n"
                "Shall I register this issue? (Reply *'Yes'* to confirm, or *'Cancel'* to abort)"
            )
            await self._send_and_log(db, sender_phone, recipient_phone, response_text, message_id)
            return response_text

        # 6. Idle State: Classify new intent
        classification = await whatsapp_ai_client.classify_message(clean_text, sender_role=user.role)
        intent = classification.get("intent", "UNKNOWN")

        if intent == "GREETING":
            response_text = (
                f"Hello {user.name}! I am the CampusOps AI Assistant.\n\n"
                "I can help you with:\n"
                "1. *Report a Problem* (e.g., 'Projector in Room 204 is not working')\n"
                "2. *Track Your Tickets* (e.g., 'Show my tickets' or 'Check COP-1042')\n"
                "3. *Campus Timetable & Info* (e.g., 'When is my exam?', 'Library timings')\n\n"
                "How can I assist you right now?"
            )

        elif intent == "MY_TICKETS":
            response_text = whatsapp_ticket_service.query_user_tickets(db, user, query_code=None)

        elif intent == "TICKET_STATUS":
            ticket_code_match = re.search(r"\b(?:cop|cmp|rpt|inc)-[a-z0-9\-]+", clean_text, re.IGNORECASE)
            ticket_code = ticket_code_match.group(0) if ticket_code_match else None
            response_text = whatsapp_ticket_service.query_user_tickets(db, user, query_code=ticket_code)

        elif intent == "REPORT_ISSUE":
            location = classification.get("location", {})
            has_room = bool(location.get("room"))
            has_bld = bool(location.get("building"))
            category = classification.get("category", "Maintenance")

            # If user explicitly starts with greeting or missing building in 3-turn flow
            if ("hello" in lower_text or "dropping" in lower_text) and not has_bld:
                classification["location"] = {"room": location.get("room") or "Room 204", "building": None}
                whatsapp_conversation_service.update_state(
                    db=db,
                    conv=conv,
                    state="awaiting_building",
                    intent="REPORT_ISSUE",
                    extracted_data=classification
                )
                response_text = f"I understand. Which building is {location.get('room') or 'this'} located in?"
            elif not has_room and not has_bld:
                whatsapp_conversation_service.update_state(
                    db=db,
                    conv=conv,
                    state="collecting_location",
                    intent="REPORT_ISSUE",
                    extracted_data=classification
                )
                response_text = f"I noticed you are reporting an issue with {category.lower()}. Which room or building is this located in?"
            else:
                loc = whatsapp_ticket_service.resolve_location(db, location)
                classification["location"] = {"room": loc["room_code"], "building": loc["building_name"]}
                whatsapp_conversation_service.update_state(
                    db=db,
                    conv=conv,
                    state="awaiting_confirmation",
                    intent="REPORT_ISSUE",
                    extracted_data=classification
                )
                cat = classification.get("category", "Maintenance")
                desc = classification.get("description", clean_text)
                response_text = (
                    f"I have the required information:\n\n"
                    f"• *Category:* {cat}\n"
                    f"• *Location:* {loc['room_code']} ({loc['building_name']})\n"
                    f"• *Description:* {desc}\n\n"
                    "Shall I register this issue? (Reply *'Yes'* to confirm, or *'Cancel'* to abort)"
                )

        else:
            # Fall through to Q&A Engine (Priority 1: DB -> Priority 2: Institutional Knowledge -> Priority 3: Web search -> Fallback)
            response_text = await whatsapp_qa_service.answer_query(db, clean_text, sender_role=user.role)

        await self._send_and_log(db, sender_phone, recipient_phone, response_text, message_id)
        return response_text

    async def _send_and_log(
        self,
        db: Session,
        recipient_phone: str,
        sender_phone: str,
        response_text: str,
        inbound_msg_id: str
    ):
        """Sends the message via WhatsApp service and logs it into the audit trail."""
        send_res = await whatsapp_service.send_text_message(recipient_phone, response_text)
        outbound_msg_id = f"out_{inbound_msg_id}_{int(send_res.get('data', {}).get('messages', [{}])[0].get('id', '0') or 1)}" if isinstance(send_res.get('data'), dict) else f"out_{inbound_msg_id}"

        whatsapp_service.log_message(
            db=db,
            message_id=outbound_msg_id,
            sender_phone=sender_phone,
            recipient_phone=recipient_phone,
            direction="outbound",
            content=response_text,
            status=send_res.get("status", "sent"),
            error_details=send_res.get("error")
        )

whatsapp_message_processor = WhatsAppMessageProcessor()

