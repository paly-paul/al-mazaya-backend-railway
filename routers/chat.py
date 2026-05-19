"""
Chat endpoints:
  POST /api/chat             — standard request/response (public)
  POST /api/chat/stream      — SSE streaming (public)
  GET  /api/chat/sessions/{sid}
"""
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models import ChatSession, ChatMessage
from schemas.chat import ChatRequest
from agent.agent import process_chat, process_chat_stream

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


def _envelope(data=None, error=None):
    return {"success": error is None, "data": data, "error": error}


@router.post("/api/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a message to the AI agent and receive a full response."""
    session_id = request.session_id or str(uuid.uuid4())
    language = request.language or "en"

    try:
        result = await process_chat(
            session_id=session_id,
            message=request.message,
            language=language,
        )
        return _envelope(data={
            "session_id": session_id,
            "message": result["message"],
            "quick_replies": result.get("quick_replies", []),
            "structured_output": None,
            "actions_taken": result.get("actions_taken", []),
        })
    except Exception as e:
        logger.exception(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    SSE streaming endpoint.  The client sends the same JSON body as POST /api/chat
    but receives a text/event-stream response.

    Event format:
        data: {"token": "Hello"}\n\n
        data: {"done": true, "quick_replies": [...], "actions_taken": [...]}\n\n
    """
    session_id = request.session_id or str(uuid.uuid4())
    language = request.language or "en"

    async def event_generator():
        # Yield the session_id first so the client can capture it
        yield f"data: {json.dumps({'session_id': session_id})}\n\n"
        try:
            async for chunk in process_chat_stream(session_id, request.message, language):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.exception(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield f"data: {json.dumps({'done': True, 'quick_replies': [], 'actions_taken': []})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",       # disable Nginx buffering
            "Connection": "keep-alive",
        },
    )


@router.get("/api/chat/sessions/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get full conversation history for a session."""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role.in_(["user", "assistant"]),
        )
        .order_by(ChatMessage.id.asc())
        .all()
    )

    msg_list = [
        {
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
        for msg in messages
    ]

    return _envelope(data={
        "session_id": session.session_id,
        "use_case": session.use_case,
        "language": session.language,
        "messages": msg_list,
    })
