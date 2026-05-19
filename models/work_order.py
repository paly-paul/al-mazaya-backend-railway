from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    ref = Column(String(20), unique=True, index=True, nullable=False)
    session_id = Column(String(255), index=True, nullable=True)
    tenant_name = Column(String(255), nullable=True)
    tower = Column(String(100), nullable=True)
    floor = Column(String(50), nullable=True)
    service_type = Column(String(255), nullable=False)
    specification = Column(Text, nullable=True)  # JSON
    quote_amount = Column(Float, nullable=True)
    quote_breakdown = Column(Text, nullable=True)  # JSON
    status = Column(
        String(50), nullable=False, default="pending_approval"
    )  # pending_approval/approved/in_progress/completed/cancelled/rejected
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    approved_by = Column(String(255), nullable=True)
    rejected_by = Column(String(255), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vendor = relationship("Vendor", foreign_keys=[vendor_id])
