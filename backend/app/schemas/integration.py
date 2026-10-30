from typing import Dict, Any
from pydantic import BaseModel, EmailStr

class IncomingEmailPayload(BaseModel):
    sender_email: EmailStr
    subject: str
    body: str

class SimulatedEmailProcessResponse(BaseModel):
    status: str
    report_code: str
    category: str
    urgency: str
    outbox_id: str
    delivery_status: str
    ai_extracted: Dict[str, Any]

