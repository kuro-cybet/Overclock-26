import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text
from app.database.base import Base

class DecisionExplanation(Base):
    __tablename__ = "decision_explanations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    decision_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    actor_id = Column(String(36), nullable=True)
    chosen_option = Column(String(150), nullable=False)
    alternative_options_json = Column(Text, nullable=True)
    factors_json = Column(Text, nullable=True)
    explanation_text = Column(Text, nullable=False)
    confidence_score = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
