from typing import List, Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.notification import NotificationOutbox
from app.integrations.simulated_email import simulated_email_service
from app.schemas.notification import OutboxResponse

router = APIRouter(prefix="/integrations", tags=["integrations"])

class IncomingEmailPayload(BaseModel):
    sender_email: EmailStr
    subject: str
    body: str

@router.post("/email/inbox")
def receive_simulated_email(
    payload: IncomingEmailPayload,
    db: Session = Depends(get_db)
):
    result = simulated_email_service.process_incoming_email(
        db=db,
        sender_email=payload.sender_email,
        subject=payload.subject,
        body=payload.body
    )
    db.commit()
    return result

@router.get("/email/outbox", response_model=List[OutboxResponse])
def get_outbox_queue(db: Session = Depends(get_db)):
    return db.query(NotificationOutbox).order_by(NotificationOutbox.created_at.desc()).limit(50).all()

