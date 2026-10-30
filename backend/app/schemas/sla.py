from typing import List, Dict, Any
from pydantic import BaseModel

class SlaStatusResponse(BaseModel):
    total_active: int
    breached: int
    warning: int
    escalations: List[Dict[str, Any]] = []

