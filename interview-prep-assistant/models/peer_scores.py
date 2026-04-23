from sqlalchemy import Column, String, Float, JSON, DateTime
import uuid
from datetime import datetime
from models.database import Base

class PeerScore(Base):
    __tablename__ = "peer_scores"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String)
    company = Column(String)
    role = Column(String)
    score = Column(Float)
    breakdown = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
