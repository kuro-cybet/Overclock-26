from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

class ClassificationRequest(BaseModel):
    message: str
    sender_role: Optional[str] = "student"
    conversation_history: Optional[List[Dict[str, str]]] = []

class LocationEntity(BaseModel):
    building: Optional[str] = None
    room: Optional[str] = None

class ClassificationResponse(BaseModel):
    intent: Literal[
        "REPORT_ISSUE",
        "TICKET_STATUS",
        "MY_TICKETS",
        "GENERAL_QUESTION",
        "CAMPUS_INFORMATION",
        "FOLLOW_UP",
        "GREETING",
        "UNKNOWN"
    ]
    category: Optional[str] = None
    subcategory: Optional[str] = None
    location: Optional[LocationEntity] = Field(default_factory=LocationEntity)
    description: Optional[str] = None
    priority_recommendation: Optional[str] = "NORMAL"
    confidence: float = 0.90
    missing_fields: List[str] = []
    requires_clarification: bool = False
    clarification_question: Optional[str] = None

class AnswerRequest(BaseModel):
    query: str
    context: Optional[str] = None
    source_urls: Optional[List[str]] = []
    sender_role: Optional[str] = "student"

class AnswerResponse(BaseModel):
    answer: str
    grounded: bool = True
    source_refs: List[str] = []
    confidence: float = 0.90
    fallback_required: bool = False

class HealthResponse(BaseModel):
    status: str
    llama_cpp_connected: bool
    model: str
    endpoint: str

