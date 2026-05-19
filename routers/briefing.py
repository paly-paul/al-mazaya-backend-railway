"""
Briefing endpoints — require JWT auth.
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Briefing
from agent.tools import handle_generate_briefing
from routers.auth import get_current_admin

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


def _envelope(data=None, error=None):
    return {"success": error is None, "data": data, "error": error}


def _briefing_dict(briefing: Briefing) -> dict:
    alerts = []
    if briefing.alerts:
        try:
            alerts = json.loads(briefing.alerts)
        except (json.JSONDecodeError, TypeError):
            alerts = []
    return {
        "id": briefing.id,
        "period": briefing.period,
        "generated_at": briefing.generated_at.isoformat() if briefing.generated_at else None,
        "briefing_en": briefing.briefing_en,
        "briefing_ar": briefing.briefing_ar,
        "alerts": alerts,
        "created_at": briefing.created_at.isoformat() if briefing.created_at else None,
    }


@router.get("/latest")
async def get_latest_briefing(
    period: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """Get the most recent management briefing."""
    q = db.query(Briefing)
    if period:
        q = q.filter(Briefing.period == period)
    briefing = q.order_by(Briefing.created_at.desc()).first()

    if not briefing:
        return _envelope(data=None, error="No briefing found")

    return _envelope(data=_briefing_dict(briefing))


@router.get("")
async def list_briefings(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """List all briefings."""
    briefings = db.query(Briefing).order_by(Briefing.created_at.desc()).limit(20).all()
    return _envelope(data=[_briefing_dict(b) for b in briefings])


@router.post("/generate")
async def generate_briefing(
    payload: dict,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """Manually trigger briefing generation."""
    period = payload.get("period", "daily")
    language = payload.get("language", "en")

    if period not in ("daily", "weekly"):
        raise HTTPException(status_code=400, detail="period must be 'daily' or 'weekly'")

    try:
        result = handle_generate_briefing(db, {"period": period, "language": language})
        # Fetch the newly created briefing for full response
        briefing = db.query(Briefing).filter(Briefing.id == result["briefing_id"]).first()
        return _envelope(data=_briefing_dict(briefing))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{briefing_id}")
async def get_briefing(
    briefing_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")
    return _envelope(data=_briefing_dict(briefing))
