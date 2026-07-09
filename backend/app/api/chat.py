import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.runner import run_turn
from app.config import get_settings
from app.db.models import Message, Session
from app.db.session import get_db
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@router.post("/stream")
@limiter.limit(settings.chat_rate_limit)
async def chat_stream(
    request: Request,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    session = await _get_or_create_session(db, payload.session_id)
    db.add(Message(session_id=session.id, role="user", content=payload.message))
    await db.commit()

    graph_input = {
        "messages": [HumanMessage(content=payload.message)],
        "session_id": session.id,
        "user_id": session.user_id,
        "step_count": 0,
    }
    return StreamingResponse(
        run_turn(session.id, graph_input),
        media_type="text/event-stream",
    )


@router.get("/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = await db.execute(
        select(Session).where(Session.user_id == "demo-user").order_by(Session.created_at.desc())
    )
    result = []
    for session in rows.scalars():
        first = await db.execute(
            select(Message.content)
            .where(Message.session_id == session.id, Message.role == "user")
            .order_by(Message.created_at.asc())
            .limit(1)
        )
        preview = first.scalar_one_or_none()
        result.append(
            {
                "id": session.id,
                "created_at": session.created_at,
                "preview": (preview or "New conversation")[:80],
            }
        )
    return result


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
    )
    return [
        {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at}
        for m in rows.scalars()
    ]


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    session = await db.get(Session, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return {"status": "deleted"}


async def _get_or_create_session(db: AsyncSession, session_id: str | None) -> Session:
    if session_id:
        session = await db.get(Session, session_id)
        if session:
            return session
    session = Session(id=str(uuid.uuid4()), user_id="demo-user")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session
