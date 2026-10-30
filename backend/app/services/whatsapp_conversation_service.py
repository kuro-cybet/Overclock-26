import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database.models.whatsapp import WhatsAppConversation

logger = logging.getLogger("whatsapp_conversation_service")

SESSION_TIMEOUT_MINUTES = 30

class WhatsAppConversationService:
    def get_or_create(
        self,
        db: Session,
        phone_number: str,
        user_id: Optional[str] = None
    ) -> WhatsAppConversation:
        clean_phone = phone_number.replace("+", "").strip()
        conv = (
            db.query(WhatsAppConversation)
            .filter(WhatsAppConversation.phone_number == clean_phone)
            .first()
        )

        now = datetime.utcnow()
        if not conv:
            conv = WhatsAppConversation(
                phone_number=clean_phone,
                user_id=user_id,
                state="idle",
                last_interaction_at=now,
                expires_at=now + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)
            return conv

        # Check if previous session expired
        if conv.expires_at and conv.expires_at < now:
            logger.info(f"[WhatsAppConversation] Session expired for {clean_phone}, resetting to idle.")
            conv.state = "idle"
            conv.current_intent = None
            conv.extracted_data_json = None

        if user_id and not conv.user_id:
            conv.user_id = user_id

        conv.last_interaction_at = now
        conv.expires_at = now + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        db.commit()
        db.refresh(conv)
        return conv

    def update_state(
        self,
        db: Session,
        conv: WhatsAppConversation,
        state: str,
        intent: Optional[str] = None,
        extracted_data: Optional[Dict[str, Any]] = None,
        last_message_id: Optional[str] = None
    ):
        conv.state = state
        if intent:
            conv.current_intent = intent
        if extracted_data is not None:
            conv.extracted_data_json = json.dumps(extracted_data)
        if last_message_id:
            conv.last_message_id = last_message_id

        now = datetime.utcnow()
        conv.last_interaction_at = now
        conv.expires_at = now + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        db.commit()
        db.refresh(conv)

    def get_extracted_data(self, conv: WhatsAppConversation) -> Dict[str, Any]:
        if not conv.extracted_data_json:
            return {}
        try:
            return json.loads(conv.extracted_data_json)
        except Exception:
            return {}

    def reset_to_idle(self, db: Session, conv: WhatsAppConversation):
        conv.state = "idle"
        conv.current_intent = None
        conv.extracted_data_json = None
        conv.last_interaction_at = datetime.utcnow()
        conv.expires_at = datetime.utcnow() + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        db.commit()
        db.refresh(conv)

whatsapp_conversation_service = WhatsAppConversationService()

