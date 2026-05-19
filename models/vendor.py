from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    categories = Column(Text, nullable=True)  # JSON array stored as string
    towers_covered = Column(Text, nullable=True)  # JSON array stored as string
    contact_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    trade_licence = Column(String(255), nullable=True)
    score = Column(Float, nullable=False, default=80.0)
    status = Column(
        String(50), nullable=False, default="onboarding"
    )  # active/onboarding/suspended/below_threshold
    jobs_completed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
