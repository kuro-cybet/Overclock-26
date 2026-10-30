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
            return

        # 3. Resolve user identity
        user = whatsapp_ticket_service.get_user_by_phone(db, sender_phone)

        # 4. Handle Unverified Senders
        if not user:
            # Check if user is asking a general or campus question
            classification = await whatsapp_ai_client.classify_message(clean_text, sender_role="guest")
            if classification.get("intent") in ["CAMPUS_INFORMATION", "GENERAL_QUESTION"]:
                response_text = await whatsapp_qa_service.answer_query(db, clean_text, sender_role="guest")
            else:
                response_text = (
                    "👋 *Welcome to CampusOps Assistant!*\n\n"
                    "Your WhatsApp number is not yet linked to an active CampusOps student or faculty account.\n\n"
                    "To report official tickets or check your private ticket status:\n"
                    "1. Sign into the CampusOps portal.\n"
                    "2. Open Settings / Profile to generate your 6-digit WhatsApp Link Code.\n"
                    "3. Reply here with: *LINK <code>*\n\n"
                    "In the meantime, feel free to ask any general campus or facility questions!"
                )

            await self._send_and_log(db, sender_phone, recipient_phone, response_text, message_id)
            return

        # 5. Verified User: Retrieve conversation state
        conv = whatsapp_conversation_service.get_or_create(db, sender_phone, user_id=user.id)
        current_state = conv.state

        # Multi-turn State: Awaiting Ticket Creation Confirmation
        if current_state == "awaiting_confirmation":
            if any(w in lower_text for w in ["yes", "confirm", "proceed", "sure", "ok", "yep", "do it"]):
                extracted_data = whatsapp_conversation_service.get_extracted_data(conv)
                incident = whatsapp_ticket_service.create_ticket_from_whatsapp(db, user, extracted_data)
                whatsapp_conversation_service.reset_to_idle(db, conv)

                loc = whatsapp_ticket_service.resolve_location(db, extracted_data.get("location", {}))
                response_text = (
                    "✅ *Your issue has been successfully registered.*\n\n"
                    f"• *Ticket ID:* {incident.incident_code}\n"
                    f"• *Category:* {incident.category.title()}\n"
                    f"• *Location:* {loc['room_code']} ({loc['building_name']})\n"
                    f"• *Priority:* {incident.priority}\n"
                    f"• *Status:* Open\n\n"
                    "You will receive updates about the progress of your ticket."
                )
            elif any(w in lower_text for w in ["no", "cancel", "abort", "nevermind", "stop"]):
                whatsapp_conversation_service.reset_to_idle(db, conv)
                response_text = "Your ticket request has been cancelled. Let me know if you need assistance with anything else."
            else:
                response_text = "Please reply with *'Yes'* to confirm ticket registration, or *'Cancel'* to abort."

            await self._send_and_log(db, sender_phone, recipient_phone, response_text, message_id)
            return

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
            return

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
            ticket_code_match = re.search(r"(?:cop|inc)-\d{3,5}", clean_text, re.IGNORECASE)
            ticket_code = ticket_code_match.group(0) if ticket_code_match else None
            response_text = whatsapp_ticket_service.query_user_tickets(db, user, query_code=ticket_code)

        elif intent == "REPORT_ISSUE":
            missing_fields = classification.get("missing_fields", [])
            location = classification.get("location", {})
            has_location = bool(location.get("room") or location.get("building"))

            if not has_location or "location" in missing_fields:
                whatsapp_conversation_service.update_state(
                    db=db,
                    conv=conv,
                    state="collecting_location",
                    intent="REPORT_ISSUE",
                    extracted_data=classification
                )
                category = classification.get("category", "maintenance")
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

