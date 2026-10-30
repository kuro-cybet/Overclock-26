from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class WhatsAppSendRequest(BaseModel):
    recipient_phone: str
    message: str

class WhatsAppSendResponse(BaseModel):
    status: str
    recipient: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class WhatsAppStatusResponse(BaseModel):
    platform: str = "CampusOps WhatsApp Assistant"
    whatsapp_cloud_api_configured: bool
    ai_service_status: str
    ai_service_endpoint: str
    model: str
    active_conversations_count: int
    linked_users_count: int
    messages_processed_count: int
    pending_whatsapp_notifications: int

class WhatsAppLinkCodeResponse(BaseModel):
    user_id: str
    user_email: str
    link_code: str
    expires_in_minutes: int
    instructions: str
    is_verified: bool
    phone_number: Optional[str] = None

class WhatsAppVerifyCodeRequest(BaseModel):
    phone_number: str
    code: str

class WhatsAppVerifyCodeResponse(BaseModel):
    success: bool
    message: str
    user_name: Optional[str] = None
    user_role: Optional[str] = None

