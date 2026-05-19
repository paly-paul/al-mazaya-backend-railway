"""
Vendor registry endpoints.
  GET /api/vendors/dispatch  — public (used by agent dispatch)
  POST /api/vendors          — requires auth
  GET /api/vendors           — requires auth
  GET /api/vendors/{id}      — requires auth
  PATCH /api/vendors/{id}/status — requires auth
  PATCH /api/vendors/{id}/score  — requires auth

IMPORTANT: /dispatch route must come BEFORE /{id} to avoid routing conflict.
"""
import json
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Vendor
from schemas.vendor import VendorCreate, VendorUpdate, VendorResponse
from routers.auth import get_current_admin

router = APIRouter(prefix="/api/vendors", tags=["vendors"])


def _envelope(data=None, error=None):
    return {"success": error is None, "data": data, "error": error}


def _parse_json(value, default=None):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default if default is not None else []
    return value if value is not None else (default if default is not None else [])


def _vendor_dict(vendor: Vendor) -> dict:
    return {
        "id": vendor.id,
        "company_name": vendor.company_name,
        "categories": _parse_json(vendor.categories, []),
        "towers_covered": _parse_json(vendor.towers_covered, []),
        "contact_name": vendor.contact_name,
        "phone": vendor.phone,
        "email": vendor.email,
        "trade_licence": vendor.trade_licence,
        "score": vendor.score,
        "status": vendor.status,
        "jobs_completed": vendor.jobs_completed,
        "created_at": vendor.created_at.isoformat() if vendor.created_at else None,
        "updated_at": vendor.updated_at.isoformat() if vendor.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Dispatch endpoint — must come BEFORE /{vendor_id}
# ---------------------------------------------------------------------------

@router.get("/dispatch")
async def dispatch_vendor(
    category: str = Query(...),
    tower: str = Query(...),
    exclude_ids: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get the best available vendor for a job category + tower."""
    excluded = set()
    if exclude_ids:
        for id_str in exclude_ids.split(","):
            try:
                excluded.add(int(id_str.strip()))
            except ValueError:
                pass

    vendors = db.query(Vendor).filter(Vendor.status == "active").all()
    best_vendor = None
    best_score = -1

    for vendor in vendors:
        if vendor.id in excluded:
            continue

        vendor_cats = _parse_json(vendor.categories, [])
        vendor_towers = _parse_json(vendor.towers_covered, [])

        cats_lower = [c.lower() for c in vendor_cats]
        towers_lower = [t.lower() for t in vendor_towers]

        category_match = category.lower() in cats_lower or "all" in cats_lower
        tower_match = tower.lower() in towers_lower or "all" in towers_lower

        if category_match and tower_match and vendor.score > best_score:
            best_score = vendor.score
            best_vendor = vendor

    if not best_vendor:
        return _envelope(data=None, error="No suitable vendor found")

    return _envelope(data={
        "vendor_id": best_vendor.id,
        "company_name": best_vendor.company_name,
        "score": best_vendor.score,
        "contact_phone": best_vendor.phone,
        "contact_name": best_vendor.contact_name,
    })


# ---------------------------------------------------------------------------
# Standard CRUD
# ---------------------------------------------------------------------------

@router.get("")
async def list_vendors(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tower: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    format: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    q = db.query(Vendor)
    if status:
        q = q.filter(Vendor.status == status)
    if min_score is not None:
        q = q.filter(Vendor.score >= min_score)

    vendors = q.order_by(Vendor.score.desc()).all()

    # Filter by category and tower (in Python since they're JSON strings)
    results = []
    for v in vendors:
        if category:
            cats = [c.lower() for c in _parse_json(v.categories, [])]
            if category.lower() not in cats and "all" not in cats:
                continue
        if tower:
            towers = [t.lower() for t in _parse_json(v.towers_covered, [])]
            if tower.lower() not in towers and "all" not in towers:
                continue
        results.append(v)

    if format == "csv":
        return _vendors_to_csv(results)

    return _envelope(data=[_vendor_dict(v) for v in results])


@router.post("")
async def create_vendor(
    payload: VendorCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    vendor = Vendor(
        company_name=payload.company_name,
        categories=json.dumps(payload.categories or []),
        towers_covered=json.dumps(payload.towers_covered or ["all"]),
        contact_name=payload.contact_name,
        phone=payload.phone,
        email=payload.email,
        trade_licence=payload.trade_licence,
        status="onboarding",
        score=80.0,
        jobs_completed=0,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return _envelope(data=_vendor_dict(vendor))


@router.get("/{vendor_id}")
async def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return _envelope(data=_vendor_dict(vendor))


@router.patch("/{vendor_id}/status")
async def update_vendor_status(
    vendor_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    new_status = payload.get("status")
    valid_statuses = ["active", "onboarding", "suspended", "below_threshold"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
    vendor.status = new_status
    db.commit()
    db.refresh(vendor)
    return _envelope(data=_vendor_dict(vendor))


@router.patch("/{vendor_id}/score")
async def update_vendor_score(
    vendor_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    score = payload.get("score")
    if score is None or not (0 <= float(score) <= 100):
        raise HTTPException(status_code=400, detail="score must be between 0 and 100")
    vendor.score = float(score)
    # Auto-flag below threshold
    if vendor.score < 60 and vendor.status == "active":
        vendor.status = "below_threshold"
    elif vendor.score >= 60 and vendor.status == "below_threshold":
        vendor.status = "active"
    db.commit()
    db.refresh(vendor)
    return _envelope(data=_vendor_dict(vendor))


@router.patch("/{vendor_id}")
async def update_vendor(
    vendor_id: int,
    payload: VendorUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ("categories", "towers_covered") and isinstance(value, list):
            value = json.dumps(value)
        setattr(vendor, field, value)
    db.commit()
    db.refresh(vendor)
    return _envelope(data=_vendor_dict(vendor))


@router.delete("/{vendor_id}")
async def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    db.delete(vendor)
    db.commit()
    return _envelope(data={"deleted": True, "id": vendor_id})


def _vendors_to_csv(vendors: list):
    import csv
    import io
    from fastapi.responses import StreamingResponse

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "company_name", "categories", "towers_covered",
        "contact_name", "phone", "email", "trade_licence",
        "score", "status", "jobs_completed", "created_at",
    ])
    for v in vendors:
        writer.writerow([
            v.id, v.company_name, v.categories, v.towers_covered,
            v.contact_name, v.phone, v.email, v.trade_licence,
            v.score, v.status, v.jobs_completed, v.created_at,
        ])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=vendors.csv"},
    )
