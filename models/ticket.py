from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ref = Column(String(20), unique=True, index=True, nullable=False)
    session_id = Column(String(255), index=True, nullable=True)
    tenant_name = Column(String(255), nullable=True)
    tower = Column(String(100), nullable=True)
    floor = Column(String(50), nullable=True)
    clinic_number = Column(String(50), nullable=True)
    category = Column(
        String(50), nullable=False
    )  # hvac/electrical/plumbing/lift/fire/medical_gas/civil/cleaning/pest/other
    description = Column(Text, nullable=False)
    priority = Column(String(5), nullable=False, default="P3")  # P1/P2/P3
    status = Column(
        String(50), nullable=False, default="open"
    )  # open/dispatched/en_route/in_progress/completed/closed
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vendor = relationship("Vendor", foreign_keys=[vendor_id])
