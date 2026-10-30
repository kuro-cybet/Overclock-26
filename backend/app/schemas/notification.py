from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recipient_id: str
    recipient_role: str
    title: str
    message: str
    type: str
    read: bool
    link_url: Optional[str] = None
    created_at: datetime

class OutboxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recipient_email: str
    channel: str
    event_type: Optional[str] = None
    subject: str
    body: str
    status: str
    attempts: int
    last_attempt_at: Optional[datetime] = None
    created_at: datetime

class ReadAllResponse(BaseModel):
    status: str

class OutboxProcessResponse(BaseModel):
    processed: int
    sent: int
    failed: int
    skipped_backoff: int
    simulated: int
    delivery_mode: str
    timestamp: str

class OutboxStatusResponse(BaseModel):
    queued: int
    sent: int
    failed: int
    simulated: int
    delivery_mode: str
