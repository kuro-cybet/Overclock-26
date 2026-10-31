from typing import Dict, Set
from app.core.exceptions import InvalidStateTransitionError

# Valid status transitions for domain entities
REPORT_TRANSITIONS: Dict[str, Set[str]] = {
    "submitted": {"triaged", "correlated", "rejected"},
    "triaged": {"correlated", "in_progress", "resolved", "rejected"},
    "correlated": {"in_progress", "resolved", "rejected"},
    "in_progress": {"resolved", "rejected"},
    "resolved": {"closed"},
    "rejected": set(),
    "closed": set(),
}

INCIDENT_TRANSITIONS: Dict[str, Set[str]] = {
    "open": {"in_progress", "resolved", "cancelled", "merged"},
    "in_progress": {"pending_parts", "pending_approval", "resolved", "cancelled", "merged"},
    "pending_parts": {"in_progress", "resolved", "merged"},
    "pending_approval": {"in_progress", "resolved", "open", "merged"},
    "resolved": {"closed", "in_progress"},  # can reopen if needed
    "closed": set(),
    "cancelled": set(),
    "merged": set(),
}

WORK_ORDER_TRANSITIONS: Dict[str, Set[str]] = {
    "unassigned": {"assigned", "in_progress", "blocked", "cancelled"},
    "assigned": {"in_progress", "blocked", "cancelled"},
    "in_progress": {"pending_parts", "blocked", "completed"},
    "pending_parts": {"in_progress", "blocked"},
    "blocked": {"in_progress", "assigned", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}

BOOKING_TRANSITIONS: Dict[str, Set[str]] = {
    "confirmed": {"relocated", "cancelled"},
    "relocated": {"cancelled", "completed"},
    "cancelled": set(),
    "completed": set(),
}

APPROVAL_TRANSITIONS: Dict[str, Set[str]] = {
    "pending": {"approved", "rejected"},
    "approved": set(),
    "rejected": set(),
}

def validate_transition(entity_type: str, current_state: str, new_state: str):
    if current_state == new_state:
        return
        
    rules = {
        "report": REPORT_TRANSITIONS,
        "incident": INCIDENT_TRANSITIONS,
        "work_order": WORK_ORDER_TRANSITIONS,
        "booking": BOOKING_TRANSITIONS,
        "approval": APPROVAL_TRANSITIONS,
    }.get(entity_type)
    
    if not rules:
        return
        
    allowed = rules.get(current_state, set())
    if new_state not in allowed:
        raise InvalidStateTransitionError(
            current_state=current_state,
            attempted_state=new_state,
            allowed_states=list(allowed)
        )
