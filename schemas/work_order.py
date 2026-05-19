from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime


class WorkOrderBase(BaseModel):
    tenant_name: Optional[str] = None
    tower: Optional[str] = None
    floor: Optional[str] = None
    service_type: str
    specification: Optional[Dict[str, Any]] = None
    quote_amount: Optional[float] = None
    quote_breakdown: Optional[Dict[str, Any]] = None


class WorkOrderCreate(WorkOrderBase):
    session_id: Optional[str] = None


class WorkOrderUpdate(BaseModel):
    tenant_name: Optional[str] = None
    tower: Optional[str] = None
    floor: Optional[str] = None
    service_type: Optional[str] = None
    specification: Optional[Dict[str, Any]] = None
    quote_amount: Optional[float] = None
    quote_breakdown: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    vendor_id: Optional[int] = None
    approved_by: Optional[str] = None
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None


class WorkOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ref: str
    session_id: Optional[str] = None
    tenant_name: Optional[str] = None
    tower: Optional[str] = None
    floor: Optional[str] = None
    service_type: str
    specification: Optional[Any] = None
    quote_amount: Optional[float] = None
    quote_breakdown: Optional[Any] = None
    status: str
    vendor_id: Optional[int] = None
    approved_by: Optional[str] = None
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
