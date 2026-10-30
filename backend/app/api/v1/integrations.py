from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models.notification import NotificationOutbox
from app.integrations.simulated_email import simulated_email_service
from app.schemas.notification import OutboxResponse
from app.schemas.integration import IncomingEmailPayload, SimulatedEmailProcessResponse

router = APIRouter(prefix="/integrations", tags=["integrations"])

@router.post(
    "/email/inbox",
    response_model=SimulatedEmailProcessResponse,
    summary="Simulate Incoming Email Intake",
    description="Simulates incoming external email intake for facility problem reporting. Employs AI text parsing to extract issue location, category, and urgency, and enqueues acknowledgment emails."
)
def receive_simulated_email(
    payload: IncomingEmailPayload,
    db: Session = Depends(get_db)
):
    """
    Ingest simulated email from campus user, extracting ticket metadata and dispatching outbox confirmation.
    """
    result = simulated_email_service.process_incoming_email(
        db=db,
        sender_email=payload.sender_email,
        subject=payload.subject,
        body=payload.body
    )
    db.commit()
    return result

@router.get(
    "/email/outbox",
    response_model=List[OutboxResponse],
    summary="List External Email Outbox Queue",
    description="Retrieves sent and pending simulated external email notification logs."
)
def get_outbox_queue(db: Session = Depends(get_db)):
    """
    List dispatched email outbox messages.
    """
    return db.query(NotificationOutbox).order_by(NotificationOutbox.created_at.desc()).limit(50).all()
