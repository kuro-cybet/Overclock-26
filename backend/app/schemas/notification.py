from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class NotificationResponse(BaseModel):
    id: str
    recipient_id: str
    recipient_role: str
    title: str
    message: str
    type: str
    read: bool
    link_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class OutboxResponse(BaseModel):
    id: str
    recipient_email: str
    channel: str
    subject: str
    body: str
    status: str
    attempts: int
    last_attempt_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

