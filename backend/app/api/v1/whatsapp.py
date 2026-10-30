import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, BackgroundTasks, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import get_db, SessionLocal
from app.database.models.user import User
from app.database.models.whatsapp import WhatsAppUserLink, WhatsAppConversation, WhatsAppMessageLog, WhatsAppSession
from app.database.models.notification import NotificationOutbox
from app.services.whatsapp_service import whatsapp_service
from app.services.whatsapp_ticket_service import whatsapp_ticket_service
from app.services.whatsapp_message_processor import whatsapp_message_processor
from app.services.whatsapp_ai_client import whatsapp_ai_client
from app.schemas.whatsapp import (
    WhatsAppSendRequest,
    WhatsAppSendResponse,
    WhatsAppStatusResponse,
    WhatsAppLinkCodeResponse,
    WhatsAppVerifyCodeRequest,
    WhatsAppVerifyCodeResponse
)
from app.api.deps import get_current_user

logger = logging.getLogger("whatsapp_router")

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# -------------------------------------------------------------
# 1. Meta Webhook Verification Handshake
# -------------------------------------------------------------
@router.get(
    "/webhook",
    summary="Meta WhatsApp Webhook Handshake Verification",
    description="Validates the hub.verify_token sent by Meta during WhatsApp Cloud API endpoint configuration and echoes hub.challenge."
)
@router.get(
    "/webhook/",
    include_in_schema=False
)
def verify_webhook(
    request: Request,
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """
    Handles Meta webhook verification GET handshake.
    """
    mode = hub_mode or request.query_params.get("hub.mode") or request.query_params.get("hub_mode")
    token = hub_verify_token or request.query_params.get("hub.verify_token") or request.query_params.get("hub_verify_token")
    challenge = hub_challenge or request.query_params.get("hub.challenge") or request.query_params.get("hub_challenge")

    if whatsapp_service.verify_hub_token(mode, token):
        logger.info("[WhatsApp Webhook] Handshake verified successfully with Meta. Echoing hub.challenge.")
        return Response(content=str(challenge or ""), media_type="text/plain", status_code=200)

    logger.warning(f"[WhatsApp Webhook] Handshake failed: mode={mode}, token={token}")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token mismatch"
    )

# -------------------------------------------------------------
# 2. Meta Inbound Message Webhook Receiver
# -------------------------------------------------------------
async def _async_process_inbound_message(msg: Dict[str, Any]):
    """Background task worker processing incoming WhatsApp message."""
    db = SessionLocal()
    try:
        await whatsapp_message_processor.process_inbound_message(
            db=db,
            message_id=msg["message_id"],
            sender_phone=msg["sender_phone"],
            recipient_phone=msg["recipient_phone"],
            text=msg["text"]
        )
    except Exception as e:
        logger.error(f"[WhatsApp Worker] Error processing inbound message {msg.get('message_id')}: {e}", exc_info=True)
    finally:
        db.close()

@router.post(
    "/webhook",
    summary="Receive WhatsApp Inbound Message Webhook",
    description="Receives incoming user messages from Meta WhatsApp Cloud API with HMAC signature verification and deduplication."
)
@router.post(
    "/webhook/",
    include_in_schema=False
)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receives incoming Meta WhatsApp messages.
    Validates X-Hub-Signature-256 header and dispatches asynchronous message processing.
    """
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    # Verify signature
    if not whatsapp_service.verify_signature(raw_body, signature):
        logger.warning("[WhatsApp Webhook] Signature verification failed.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook HMAC signature"
        )

    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored", "reason": "non-json"}

    parsed_messages = whatsapp_service.parse_webhook_messages(payload)
    for msg in parsed_messages:
        background_tasks.add_task(_async_process_inbound_message, msg)

    return {"status": "received", "count": len(parsed_messages)}

# -------------------------------------------------------------
# 3. Direct Outbound Message Sender
# -------------------------------------------------------------
@router.post(
    "/send",
    response_model=WhatsAppSendResponse,
    summary="Send WhatsApp Message",
    description="Sends an outbound message to a recipient phone number through Meta WhatsApp Cloud API."
)
async def send_message(
    payload: WhatsAppSendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Direct outbound message trigger.
    """
    res = await whatsapp_service.send_text_message(payload.recipient_phone, payload.message)
    return WhatsAppSendResponse(
        status=res.get("status", "sent"),
        recipient=payload.recipient_phone,
        data=res.get("data"),
        error=res.get("error")
    )

# -------------------------------------------------------------
# 4. WhatsApp System & AI Status
# -------------------------------------------------------------
@router.get(
    "/status",
    response_model=WhatsAppStatusResponse,
    summary="Get WhatsApp Assistant & AI Service Status",
    description="Reports the operational status of Meta WhatsApp Cloud API connectivity, the local Qwen AI service, and conversation counts."
)
async def get_status(db: Session = Depends(get_db)):
    """
    Returns WhatsApp and AI status overview.
    """
    ai_health = await whatsapp_ai_client.check_health()
    active_convs = db.query(WhatsAppConversation).filter(WhatsAppConversation.state != "idle").count()
    linked_users = db.query(WhatsAppUserLink).filter(WhatsAppUserLink.is_verified == True).count()
    msgs_count = db.query(WhatsAppMessageLog).count()
    pending_wa_notifs = db.query(NotificationOutbox).filter(NotificationOutbox.channel == "whatsapp", NotificationOutbox.status == "queued").count()

    return WhatsAppStatusResponse(
        platform="CampusOps WhatsApp Assistant",
        whatsapp_cloud_api_configured=bool(settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID),
        ai_service_status=ai_health.get("status", "unknown"),
        ai_service_endpoint=settings.AI_SERVICE_URL,
        model=settings.AI_MODEL,
        active_conversations_count=active_convs,
        linked_users_count=linked_users,
        messages_processed_count=msgs_count,
        pending_whatsapp_notifications=pending_wa_notifs
    )

# -------------------------------------------------------------
# 5. User Phone Linking & Verification Endpoints
# -------------------------------------------------------------
@router.get(
    "/link-code",
    response_model=WhatsAppLinkCodeResponse,
    summary="Generate WhatsApp Account Link Code",
    description="Generates a 6-digit one-time linking code for the currently authenticated student or faculty member."
)
def get_link_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates or retrieves 6-digit WhatsApp link code.
    """
    link_info = whatsapp_ticket_service.generate_link_code(db, current_user)
    existing_link = db.query(WhatsAppUserLink).filter(WhatsAppUserLink.user_id == current_user.id).first()

    return WhatsAppLinkCodeResponse(
        user_id=current_user.id,
        user_email=current_user.email,
        link_code=link_info["link_code"],
        expires_in_minutes=link_info["expires_in_minutes"],
        instructions=link_info["instructions"],
        is_verified=bool(existing_link and existing_link.is_verified),
        phone_number=existing_link.phone_number if (existing_link and existing_link.is_verified) else current_user.phone_number
    )

@router.post(
    "/link",
    response_model=WhatsAppVerifyCodeResponse,
    summary="Verify WhatsApp Link Code via Web Portal",
    description="Allows users to link their WhatsApp phone number by entering their phone number and confirmation code in the portal."
)
def verify_link_code(
    payload: WhatsAppVerifyCodeRequest,
    db: Session = Depends(get_db)
):
    """
    Verifies code and links phone number.
    """
    user = whatsapp_ticket_service.verify_link_code(db, payload.phone_number, payload.code)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code."
        )

    return WhatsAppVerifyCodeResponse(
        success=True,
        message=f"Phone number {payload.phone_number} successfully linked to {user.name}.",
        user_name=user.name,
        user_role=user.role
    )

# -------------------------------------------------------------
# 6. Ticket Queries
# -------------------------------------------------------------
@router.get(
    "/tickets",
    summary="Query WhatsApp Linked Tickets",
    description="Returns tickets belonging to the authenticated user formatted for display."
)
def get_tickets(
    query_code: Optional[str] = Query(None, description="Optional ticket code (e.g., COP-1042 or INC-2026-0001)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns authenticated user's tickets.
    """
    return {
        "user_email": current_user.email,
        "response": whatsapp_ticket_service.query_user_tickets(db, current_user, query_code)
    }

# -------------------------------------------------------------
# 7. Simulator & Session Inspection Endpoints
# -------------------------------------------------------------
class WhatsAppSimulatePayload(BaseModel):
    from_phone: str
    message: str

@router.post(
    "/simulate",
    summary="Simulate Inbound WhatsApp Message",
    description="Simulates incoming WhatsApp chat interactions using the unified WhatsApp message processor."
)
async def simulate_whatsapp_message(
    payload: WhatsAppSimulatePayload,
    db: Session = Depends(get_db)
):
    import uuid
    sim_msg_id = f"sim_{uuid.uuid4().hex[:12]}"
    clean_phone = payload.from_phone.replace("+", "").replace("-", "").replace(" ", "").strip()

    reply = await whatsapp_message_processor.process_inbound_message(
        db=db,
        message_id=sim_msg_id,
        sender_phone=clean_phone,
        recipient_phone="CampusOps",
        text=payload.message
    )

    conv = db.query(WhatsAppConversation).filter(WhatsAppConversation.phone_number == clean_phone).first()
    state = conv.state if conv else "idle"
    intent = conv.current_intent if conv else None

    return {
        "status": "ok",
        "reply": reply or "",
        "from_phone": payload.from_phone,
        "session_step": state.upper(),
        "state": state,
        "current_intent": intent
    }

@router.get(
    "/session/{phone_number}",
    summary="Get WhatsApp Session State",
    description="Returns the active conversation session for a given phone number."
)
def get_whatsapp_session(
    phone_number: str,
    db: Session = Depends(get_db)
):
    clean = phone_number.replace("+", "").replace("-", "").replace(" ", "").strip()
    conv = db.query(WhatsAppConversation).filter(WhatsAppConversation.phone_number == clean).first()
    if conv:
        return {
            "phone_number": phone_number,
            "step": conv.state.upper(),
            "state": conv.state,
            "current_intent": conv.current_intent,
            "user_id": conv.user_id,
            "last_active_at": conv.last_interaction_at.isoformat() if conv.last_interaction_at else None
        }

    session = db.query(WhatsAppSession).filter(WhatsAppSession.phone_number == clean).first()
    if session:
        return {
            "phone_number": session.phone_number,
            "step": session.step,
            "state": session.step.lower(),
            "current_intent": session.current_intent,
            "user_id": session.user_id,
            "last_active_at": session.last_active_at.isoformat() if session.last_active_at else None
        }

    return {"phone_number": phone_number, "step": "IDLE", "state": "idle", "current_intent": None}

@router.get(
    "/logs",
    summary="Get WhatsApp Message Logs",
    description="Returns recent inbound and outbound WhatsApp message logs."
)
def get_whatsapp_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    logs = db.query(WhatsAppMessageLog).order_by(WhatsAppMessageLog.created_at.desc()).limit(limit).all()
    return logs
