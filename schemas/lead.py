from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class LeadBase(BaseModel):
    name: str
    phone: Optional[str] = None
    specialty: Optional[str] = None
    clinic_size: Optional[str] = None
    tower_preference: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    source: Optional[str] = "chat"
    assigned_to: Optional[str] = None


class LeadCreate(LeadBase):
    session_id: Optional[str] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    specialty: Optional[str] = None
    clinic_size: Optional[str] = None
    tower_preference: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    source: Optional[str] = None
    score: Optional[float] = None
    tier: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: Optional[str] = None
    name: str
    phone: Optional[str] = None
    specialty: Optional[str] = None
    clinic_size: Optional[str] = None
    tower_preference: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    source: Optional[str] = None
    score: Optional[float] = None
    tier: Optional[str] = None
    status: str
    assigned_to: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
