import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from app.database.base import Base

class WhatsAppUserLink(Base):
    """
    Secure mapping between verified university users and their WhatsApp phone numbers.
    Prevents unauthorized access to private ticket data by requiring two-step verification.
    """
    __tablename__ = "whatsapp_user_links"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    phone_number = Column(String(30), unique=True, nullable=False, index=True)
    verification_code = Column(String(10), nullable=True)
    code_expires_at = Column(DateTime, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class WhatsAppConversation(Base):
    """
    Durable database-backed conversation state for WhatsApp sessions.
    Preserves multi-turn state (clarifications, confirmations) across server restarts.
    """
    __tablename__ = "whatsapp_conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String(30), unique=True, nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    state = Column(String(50), default="idle", nullable=False)  # idle, collecting_location, collecting_category, awaiting_confirmation
    current_intent = Column(String(50), nullable=True)
    extracted_data_json = Column(Text, nullable=True)  # JSON payload of in-flight issue details
    last_message_id = Column(String(100), nullable=True)
    last_interaction_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class WhatsAppSession(Base):
    """
    Tracks multi-turn complaint and inquiry state machine for WhatsApp conversations.
    Steps: IDLE, AWAITING_BUILDING, AWAITING_ROOM, AWAITING_DETAILS, AWAITING_TRACK_ID.
    """
    __tablename__ = "whatsapp_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String(30), unique=True, nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    current_intent = Column(String(50), nullable=True)
    step = Column(String(50), default="IDLE", nullable=False)
    context_data = Column(Text, default="{}", nullable=False)
    last_active_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WhatsAppMessageLog(Base):
    """
    Audit log of inbound and outbound WhatsApp messages with idempotency tracking.
    """
    __tablename__ = "whatsapp_messages_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(100), unique=True, nullable=False, index=True)
    sender_phone = Column(String(30), nullable=False, index=True)
    recipient_phone = Column(String(30), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # inbound, outbound
    message_type = Column(String(20), default="text", nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(20), default="received", nullable=False)  # received, processed, sent, failed
    error_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

