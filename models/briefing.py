from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class Briefing(Base):
    __tablename__ = "briefings"

    id = Column(Integer, primary_key=True, index=True)
    period = Column(String(20), nullable=False)  # daily/weekly
    generated_at = Column(DateTime(timezone=True), nullable=True)
    briefing_en = Column(Text, nullable=True)
    briefing_ar = Column(Text, nullable=True)
    alerts = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
