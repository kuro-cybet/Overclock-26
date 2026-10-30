import json
import logging
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.database.models.operational_event import OperationalEvent

logger = logging.getLogger(__name__)

class EventService:
    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        entity_type: str,
        entity_id: str,
        severity: str = "info",
        payload: Optional[dict[str, Any]] = None,
        actor_id: Optional[str] = None
    ) -> Optional[OperationalEvent]:
        """
        Record a structured operational event into the operational_events ledger.
        Never raises exceptions to callers; logs error and returns None if failed.
        """
        try:
            payload_str = json.dumps(payload, default=str) if payload else None
            ev = OperationalEvent(
                event_type=event_type,
                entity_type=entity_type,
                entity_id=str(entity_id),
                severity=severity,
                payload_json=payload_str,
                actor_id=actor_id
            )
            db.add(ev)
            db.flush()
            return ev
        except Exception as e:
            logger.error(f"[EventService] Failed to record operational event {event_type}: {e}")
            return None

event_service = EventService()

