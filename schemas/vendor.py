from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class VendorBase(BaseModel):
    company_name: str
    categories: Optional[List[str]] = None
    towers_covered: Optional[List[str]] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    trade_licence: Optional[str] = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    company_name: Optional[str] = None
    categories: Optional[List[str]] = None
    towers_covered: Optional[List[str]] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    trade_licence: Optional[str] = None
    score: Optional[float] = None
    status: Optional[str] = None
    jobs_completed: Optional[int] = None


class VendorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    categories: Optional[List[str]] = None
    towers_covered: Optional[List[str]] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    trade_licence: Optional[str] = None
    score: float
    status: str
    jobs_completed: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        import json
        if hasattr(obj, '__dict__') or hasattr(obj, '__table__'):
            data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
            # Parse JSON fields
            for field in ('categories', 'towers_covered'):
                val = data.get(field)
                if isinstance(val, str):
                    try:
                        data[field] = json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        data[field] = []
                elif val is None:
                    data[field] = []
            return cls(**data)
        return super().model_validate(obj, *args, **kwargs)
