from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langgraph.types import Command
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.runner import finalize_tool_call, mark_tool_call, run_turn
from app.db.models import ToolCall
from app.db.session import get_db

router = APIRouter(prefix="/chat/approvals", tags=["approvals"])


async def _resume(db: AsyncSession, tool_call_id: str, approved: bool) -> StreamingResponse:
    tool_call = await db.get(ToolCall, tool_call_id)
    if tool_call is None:
        raise HTTPException(status_code=404, detail="tool call not found")
    if tool_call.status != "pending":
        raise HTTPException(status_code=409, detail=f"tool call already {tool_call.status}")

    await mark_tool_call(db, tool_call, approved=approved, user_id="demo-user")
    session_id = tool_call.session_id

    async def stream():
        async for event in run_turn(session_id, Command(resume={"approved": approved})):
            yield event
        await finalize_tool_call(session_id, tool_call_id)

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.post("/{tool_call_id}/approve")
async def approve(tool_call_id: str, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    return await _resume(db, tool_call_id, approved=True)


@router.post("/{tool_call_id}/deny")
async def deny(tool_call_id: str, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    return await _resume(db, tool_call_id, approved=False)
