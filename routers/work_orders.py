"""
Work order (facility services) endpoints — all require JWT auth.
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import WorkOrder, Vendor
from schemas.work_order import WorkOrderCreate, WorkOrderUpdate, WorkOrderResponse
from routers.auth import get_current_admin

router = APIRouter(prefix="/api/work-orders", tags=["work_orders"])


def _envelope(data=None, error=None):
    return {"success": error is None, "data": data, "error": error}


def _parse_json_field(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


def _wo_dict(wo: WorkOrder, db: Session) -> dict:
    d = {
        "id": wo.id,
        "ref": wo.ref,
        "session_id": wo.session_id,
        "tenant_name": wo.tenant_name,
        "tower": wo.tower,
        "floor": wo.floor,
        "service_type": wo.service_type,
        "specification": _parse_json_field(wo.specification),
        "quote_amount": wo.quote_amount,
        "quote_breakdown": _parse_json_field(wo.quote_breakdown),
        "status": wo.status,
        "vendor_id": wo.vendor_id,
        "approved_by": wo.approved_by,
        "rejected_by": wo.rejected_by,
        "rejection_reason": wo.rejection_reason,
        "created_at": wo.created_at.isoformat() if wo.created_at else None,
        "updated_at": wo.updated_at.isoformat() if wo.updated_at else None,
    }
    if wo.vendor_id:
        vendor = db.query(Vendor).filter(Vendor.id == wo.vendor_id).first()
        if vendor:
            d["vendor"] = {
                "id": vendor.id,
                "company_name": vendor.company_name,
                "contact_name": vendor.contact_name,
                "phone": vendor.phone,
            }
    return d


@router.get("")
async def list_work_orders(
    status: Optional[str] = Query(None),
    tower: Optional[str] = Query(None),
    service_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    q = db.query(WorkOrder)
    if status:
        q = q.filter(WorkOrder.status == status)
    if tower:
        q = q.filter(WorkOrder.tower.ilike(f"%{tower}%"))
    if service_type:
        q = q.filter(WorkOrder.service_type.ilike(f"%{service_type}%"))

    work_orders = q.order_by(WorkOrder.created_at.desc()).all()
    return _envelope(data=[_wo_dict(wo, db) for wo in work_orders])


@router.get("/{wo_id}")
async def get_work_order(
    wo_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    return _envelope(data=_wo_dict(wo, db))


@router.post("")
async def create_work_order(
    payload: WorkOrderCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    from config import settings

    quote_amount = payload.quote_amount or 0
    auto_approve = quote_amount <= settings.auto_approval_threshold_kd

    wo = WorkOrder(
        session_id=payload.session_id,
        tenant_name=payload.tenant_name,
        tower=payload.tower,
        floor=payload.floor,
        service_type=payload.service_type,
        specification=json.dumps(payload.specification or {}),
        quote_amount=quote_amount,
        quote_breakdown=json.dumps(payload.quote_breakdown or {}),
        status="approved" if auto_approve else "pending_approval",
        approved_by="auto" if auto_approve else None,
        ref="WO-TEMP",
    )
    db.add(wo)
    db.flush()
    wo.ref = f"WO-{wo.id:04d}"
    db.commit()
    db.refresh(wo)
    return _envelope(data=_wo_dict(wo, db))


@router.patch("/{wo_id}/approve")
async def approve_work_order(
    wo_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    if wo.status not in ("pending_approval",):
        raise HTTPException(status_code=400, detail=f"Cannot approve work order with status '{wo.status}'")

    wo.status = "approved"
    wo.approved_by = payload.get("approved_by", "admin")

    # Dispatch vendor after approval
    from agent.tools import handle_dispatch_vendor
    dispatch_result = handle_dispatch_vendor(db, {
        "job_id": wo.id,
        "job_type": "work_order",
        "category": wo.service_type.lower(),
        "tower": wo.tower or "",
    })
    db.commit()
    db.refresh(wo)

    result = _wo_dict(wo, db)
    result["vendor_dispatched"] = dispatch_result
    return _envelope(data=result)


@router.patch("/{wo_id}/reject")
async def reject_work_order(
    wo_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    if wo.status not in ("pending_approval",):
        raise HTTPException(status_code=400, detail=f"Cannot reject work order with status '{wo.status}'")

    wo.status = "rejected"
    wo.rejected_by = payload.get("rejected_by", "admin")
    wo.rejection_reason = payload.get("reason", "")
    db.commit()
    db.refresh(wo)
    return _envelope(data=_wo_dict(wo, db))


@router.patch("/{wo_id}")
async def update_work_order(
    wo_id: int,
    payload: WorkOrderUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ("specification", "quote_breakdown") and isinstance(value, dict):
            value = json.dumps(value)
        setattr(wo, field, value)
    db.commit()
    db.refresh(wo)
    return _envelope(data=_wo_dict(wo, db))


@router.delete("/{wo_id}")
async def delete_work_order(
    wo_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    db.delete(wo)
    db.commit()
    return _envelope(data={"deleted": True, "id": wo_id})
