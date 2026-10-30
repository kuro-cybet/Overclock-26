import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import get_db, SessionLocal
from app.database.models.user import User
from app.database.models.whatsapp import WhatsAppUserLink, WhatsAppConversation, WhatsAppMessageLog
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
def verify_webhook(
    request: Request,
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """
    Handles Meta webhook verification GET handshake.
    """
    if whatsapp_service.verify_hub_token(hub_mode, hub_verify_token):
        logger.info("[WhatsApp Webhook] Handshake verified successfully with Meta.")
        return Response(content=hub_challenge or "", media_type="text/plain", status_code=200)

    logger.warning(f"[WhatsApp Webhook] Handshake failed: mode={hub_mode}, token={hub_verify_token}")
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

