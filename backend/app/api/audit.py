from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ToolCall
from app.db.session import get_db

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def list_tool_calls(
    session_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> dict:
    query = select(ToolCall).order_by(ToolCall.requested_at.desc())
    if session_id:
        query = query.where(ToolCall.session_id == session_id)
    if status:
        query = query.where(ToolCall.status == status)
    rows = await db.execute(query.limit(limit).offset(offset))
    items = [
        {
            "id": tc.id,
            "session_id": tc.session_id,
            "tool_name": tc.tool_name,
            "arguments": tc.arguments,
            "is_sensitive": tc.is_sensitive,
            "status": tc.status,
            "requested_at": tc.requested_at,
            "approved_by": tc.approved_by,
            "approved_at": tc.approved_at,
            "executed_at": tc.executed_at,
            "result": tc.result,
            "error": tc.error,
        }
        for tc in rows.scalars()
    ]

    counts_rows = await db.execute(select(ToolCall.status, func.count()).group_by(ToolCall.status))
    counts = {status_name: count for status_name, count in counts_rows.all()}
    total = sum(counts.values())
    return {
        "items": items,
        "summary": {
            "total": total,
            "pending": counts.get("pending", 0),
            "executed": counts.get("executed", 0),
            "denied": counts.get("denied", 0),
            "failed": counts.get("failed", 0),
        },
    }
