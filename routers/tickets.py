"""
Maintenance ticket endpoints — all require JWT auth.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Ticket, Vendor
from schemas.ticket import TicketCreate, TicketUpdate, TicketResponse
from routers.auth import get_current_admin

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


def _envelope(data=None, error=None):
    return {"success": error is None, "data": data, "error": error}


def _ticket_dict(ticket: Ticket, db: Session) -> dict:
    d = TicketResponse.model_validate(ticket).model_dump()
    # Include vendor info if available
    if ticket.vendor_id:
        vendor = db.query(Vendor).filter(Vendor.id == ticket.vendor_id).first()
        if vendor:
            d["vendor"] = {
                "id": vendor.id,
                "company_name": vendor.company_name,
                "contact_name": vendor.contact_name,
                "phone": vendor.phone,
            }
    return d


@router.get("")
async def list_tickets(
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    tower: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    q = db.query(Ticket)
    if priority:
        q = q.filter(Ticket.priority == priority)
    if status:
        q = q.filter(Ticket.status == status)
    if tower:
        q = q.filter(Ticket.tower.ilike(f"%{tower}%"))
    if category:
        q = q.filter(Ticket.category == category.lower())
    if from_date:
        q = q.filter(Ticket.created_at >= from_date)

    tickets = q.order_by(Ticket.created_at.desc()).all()
    return _envelope(data=[_ticket_dict(t, db) for t in tickets])


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return _envelope(data=_ticket_dict(ticket, db))


@router.post("")
async def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    from datetime import datetime, timedelta, timezone
    from config import settings

    category = payload.category.lower()
    p1_cats = {"hvac", "electrical", "lift", "fire", "medical_gas"}
    p2_cats = {"plumbing", "civil"}
    priority = "P1" if category in p1_cats else "P2" if category in p2_cats else "P3"
    hours_map = {"P1": settings.p1_sla_hours, "P2": settings.p2_sla_hours, "P3": settings.p3_sla_hours}
    sla_deadline = datetime.now(timezone.utc) + timedelta(hours=hours_map[priority])

    ticket = Ticket(
        session_id=payload.session_id,
        tenant_name=payload.tenant_name,
        tower=payload.tower,
        floor=payload.floor,
        clinic_number=payload.clinic_number,
        category=category,
        description=payload.description,
        priority=payload.priority or priority,
        sla_deadline=sla_deadline,
        status="open",
        ref="MX-TEMP",
    )
    db.add(ticket)
    db.flush()
    ticket.ref = f"MX-{ticket.id:04d}"
    db.commit()
    db.refresh(ticket)
    return _envelope(data=_ticket_dict(ticket, db))


@router.patch("/{ticket_id}/vendor")
async def reassign_vendor(
    ticket_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    vendor_id = payload.get("vendor_id")
    if not vendor_id:
        raise HTTPException(status_code=400, detail="vendor_id is required")
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    ticket.vendor_id = vendor_id
    ticket.status = "dispatched"
    db.commit()
    db.refresh(ticket)
    return _envelope(data=_ticket_dict(ticket, db))


@router.patch("/{ticket_id}/priority")
async def escalate_priority(
    ticket_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    new_priority = payload.get("priority")
    if new_priority not in ("P1", "P2", "P3"):
        raise HTTPException(status_code=400, detail="priority must be P1, P2, or P3")
    ticket.priority = new_priority
    # Recalculate SLA
    from datetime import datetime, timedelta, timezone
    from config import settings
    hours_map = {"P1": settings.p1_sla_hours, "P2": settings.p2_sla_hours, "P3": settings.p3_sla_hours}
    ticket.sla_deadline = datetime.now(timezone.utc) + timedelta(hours=hours_map[new_priority])
    db.commit()
    db.refresh(ticket)
    return _envelope(data=_ticket_dict(ticket, db))


@router.patch("/{ticket_id}/close")
async def close_ticket(
    ticket_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "closed"
    ticket.resolution_note = payload.get("resolution_note", "")
    db.commit()
    db.refresh(ticket)
    return _envelope(data=_ticket_dict(ticket, db))


@router.patch("/{ticket_id}")
async def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return _envelope(data=_ticket_dict(ticket, db))


@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    db.delete(ticket)
    db.commit()
    return _envelope(data={"deleted": True, "id": ticket_id})
