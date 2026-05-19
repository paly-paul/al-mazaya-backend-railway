from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    specialty = Column(String(255), nullable=True)
    clinic_size = Column(String(100), nullable=True)
    tower_preference = Column(String(100), nullable=True)
    budget_range = Column(String(100), nullable=True)
    timeline = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True, default="chat")
    score = Column(Float, nullable=True, default=0.0)
    tier = Column(String(20), nullable=True, default="cold")  # hot/warm/cold
    status = Column(
        String(50), nullable=False, default="new"
    )  # new/follow_up/meeting_set/proposal_sent/nurture/closed_won/closed_lost
    assigned_to = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
