"""
Dashboard endpoints — require JWT auth.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from database import get_db
from models import ChatSession, ChatMessage
from agent.tools import handle_get_dashboard_stats
from routers.auth import get_current_admin

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _envelope(data=None, error=None):
    return {"success": error is None, "data": data, "error": error}


@router.get("/stats")
async def get_dashboard_stats(
    tower: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """Get all KPIs for the dashboard."""
    stats = handle_get_dashboard_stats(db, {"tower_filter": tower})
    return _envelope(data=stats)


@router.get("/live-chats")
async def get_live_chats(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """Get recent/active chat sessions for the Live Chats page."""
    from datetime import datetime, timedelta, timezone

    # Sessions with activity in the last 24h
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.updated_at >= cutoff)
        .order_by(ChatSession.updated_at.desc())
        .limit(50)
        .all()
    )

    result = []
    for session in sessions:
        # Get the last message
        last_msg = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session.session_id,
                ChatMessage.role.in_(["user", "assistant"]),
            )
            .order_by(ChatMessage.id.desc())
            .first()
        )

        # Count messages
        msg_count = (
            db.query(sql_func.count(ChatMessage.id))
            .filter(ChatMessage.session_id == session.session_id)
            .scalar()
        )

        result.append({
            "session_id": session.session_id,
            "language": session.language,
            "use_case": session.use_case,
            "message_count": msg_count or 0,
            "last_message": {
                "role": last_msg.role if last_msg else None,
                "content": (last_msg.content or "")[:200] if last_msg else None,
                "created_at": last_msg.created_at.isoformat() if last_msg and last_msg.created_at else None,
            },
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        })

    return _envelope(data=result)
