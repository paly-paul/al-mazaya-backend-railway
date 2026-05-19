from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class TicketBase(BaseModel):
    tenant_name: Optional[str] = None
    tower: Optional[str] = None
    floor: Optional[str] = None
    clinic_number: Optional[str] = None
    category: str
    description: str
    priority: Optional[str] = None


class TicketCreate(TicketBase):
    session_id: Optional[str] = None


class TicketUpdate(BaseModel):
    tenant_name: Optional[str] = None
    tower: Optional[str] = None
    floor: Optional[str] = None
    clinic_number: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    vendor_id: Optional[int] = None
    resolution_note: Optional[str] = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ref: str
    session_id: Optional[str] = None
    tenant_name: Optional[str] = None
    tower: Optional[str] = None
    floor: Optional[str] = None
    clinic_number: Optional[str] = None
    category: str
    description: str
    priority: str
    status: str
    vendor_id: Optional[int] = None
    sla_deadline: Optional[datetime] = None
    resolution_note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
