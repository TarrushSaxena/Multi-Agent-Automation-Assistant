import json
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from langchain_core.messages import AIMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import get_compiled_graph
from app.db.models import Message, ToolCall
from app.db.session import AsyncSessionLocal


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


async def run_turn(session_id: str, graph_input) -> AsyncGenerator[str, None]:
    """Stream one agent turn (fresh message or an approval resume) as SSE events.

    DB writes use their own short-lived sessions (not a request-scoped one) so they remain valid
    for the full lifetime of this streaming generator.

    Emits `token` events for the final reply, a `pending_approval` event if the graph pauses for
    human approval (persisting a ToolCall row), and a terminal `done` event.
    """
    graph = await get_compiled_graph()
    config = {"configurable": {"thread_id": session_id}}

    answer_parts: list[str] = []
    interrupted_payload: dict | None = None

    async for mode, chunk in graph.astream(graph_input, config, stream_mode=["updates", "messages"]):
        if mode == "messages":
            message_chunk, meta = chunk
            if meta.get("langgraph_node") == "respond" and getattr(message_chunk, "content", ""):
                token = message_chunk.content
                answer_parts.append(token)
                yield _sse({"type": "token", "value": token})
        elif mode == "updates":
            if "__interrupt__" in chunk:
                interrupted_payload = chunk["__interrupt__"][0].value
                break

    if interrupted_payload is not None:
        async with AsyncSessionLocal() as db:
            tool_call = ToolCall(
                session_id=session_id,
                tool_name=interrupted_payload["tool_name"],
                arguments=interrupted_payload.get("args", {}),
                is_sensitive=True,
                status="pending",
            )
            db.add(tool_call)
            await db.commit()
            await db.refresh(tool_call)
            tool_call_id = tool_call.id
            tool_name = tool_call.tool_name
            arguments = tool_call.arguments
        yield _sse(
            {"type": "pending_approval", "tool_call_id": tool_call_id, "tool_name": tool_name, "args": arguments}
        )
        yield _sse({"type": "done", "session_id": session_id, "status": "awaiting_approval"})
        return

    # No interrupt: the turn completed. Persist the assistant reply.
    answer = "".join(answer_parts)
    if not answer:
        state = await graph.aget_state(config)
        for message in reversed(state.values.get("messages", [])):
            if isinstance(message, AIMessage) and message.content:
                answer = message.content
                break

    async with AsyncSessionLocal() as db:
        assistant = Message(session_id=session_id, role="assistant", content=answer or "")
        db.add(assistant)
        await db.commit()
        await db.refresh(assistant)
        message_id = assistant.id
    yield _sse({"type": "done", "session_id": session_id, "message_id": message_id, "status": "complete"})


async def mark_tool_call(db: AsyncSession, tool_call: ToolCall, *, approved: bool, user_id: str) -> None:
    tool_call.status = "approved" if approved else "denied"
    tool_call.approved_by = user_id
    tool_call.approved_at = datetime.now(timezone.utc)
    await db.commit()


async def finalize_tool_call(session_id: str, tool_call_id: str) -> None:
    """After a resume, read the graph's tool_result and record execution status on the ToolCall row.

    Uses its own session because it runs at the tail of a streaming response, after the request
    session may already be closed.
    """
    graph = await get_compiled_graph()
    state = await graph.aget_state({"configurable": {"thread_id": session_id}})
    result = state.values.get("tool_result")
    async with AsyncSessionLocal() as db:
        tool_call = await db.get(ToolCall, tool_call_id)
        if tool_call is None or not result or result.get("tool_name") != tool_call.tool_name:
            return
        if result.get("ok"):
            tool_call.status = "executed"
            tool_call.result = result.get("data")
            tool_call.executed_at = datetime.now(timezone.utc)
        elif tool_call.status != "denied":
            tool_call.status = "failed"
            tool_call.error = result.get("error")
        await db.commit()
