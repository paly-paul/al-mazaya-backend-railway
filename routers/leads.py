"""
Lead management endpoints — all require JWT auth.
"""
import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Lead
from schemas.lead import LeadCreate, LeadUpdate, LeadResponse
from routers.auth import get_current_admin

router = APIRouter(prefix="/api/leads", tags=["leads"])


def _envelope(data=None, error=None):
    return {"success": error is None, "data": data, "error": error}


@router.get("")
async def list_leads(
    score_tier: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    tower: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """List all leads with optional filters."""
    q = db.query(Lead)

    if score_tier:
        q = q.filter(Lead.tier == score_tier)
    if status:
        q = q.filter(Lead.status == status)
    if tower:
        q = q.filter(Lead.tower_preference.ilike(f"%{tower}%"))
    if source:
        q = q.filter(Lead.source == source)
    if assigned_to:
        q = q.filter(Lead.assigned_to.ilike(f"%{assigned_to}%"))
    if from_date:
        q = q.filter(Lead.created_at >= from_date)
    if to_date:
        q = q.filter(Lead.created_at <= to_date)

    leads = q.order_by(Lead.created_at.desc()).all()

    if format == "csv":
        return _leads_to_csv(leads)

    data = [LeadResponse.model_validate(l) for l in leads]
    return _envelope(data=[d.model_dump() for d in data])


@router.get("/{lead_id}")
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _envelope(data=LeadResponse.model_validate(lead).model_dump())


@router.post("")
async def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    lead = Lead(**payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return _envelope(data=LeadResponse.model_validate(lead).model_dump())


@router.patch("/{lead_id}/assign")
async def assign_lead(
    lead_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    assigned_to = payload.get("assigned_to")
    if not assigned_to:
        raise HTTPException(status_code=400, detail="assigned_to is required")
    lead.assigned_to = assigned_to
    db.commit()
    db.refresh(lead)
    return _envelope(data=LeadResponse.model_validate(lead).model_dump())


@router.patch("/{lead_id}/status")
async def update_lead_status(
    lead_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    new_status = payload.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="status is required")
    valid_statuses = [
        "new", "follow_up", "meeting_set", "proposal_sent",
        "nurture", "closed_won", "closed_lost",
    ]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
    lead.status = new_status
    db.commit()
    db.refresh(lead)
    return _envelope(data=LeadResponse.model_validate(lead).model_dump())


@router.patch("/{lead_id}")
async def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    db.commit()
    db.refresh(lead)
    return _envelope(data=LeadResponse.model_validate(lead).model_dump())


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()
    return _envelope(data={"deleted": True, "id": lead_id})


def _leads_to_csv(leads: list) -> StreamingResponse:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "name", "phone", "specialty", "clinic_size",
        "tower_preference", "budget_range", "timeline", "source",
        "score", "tier", "status", "assigned_to", "created_at",
    ])
    for lead in leads:
        writer.writerow([
            lead.id, lead.name, lead.phone, lead.specialty, lead.clinic_size,
            lead.tower_preference, lead.budget_range, lead.timeline, lead.source,
            lead.score, lead.tier, lead.status, lead.assigned_to, lead.created_at,
        ])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )
