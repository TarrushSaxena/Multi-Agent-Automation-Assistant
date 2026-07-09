import json

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.tests.conftest import build_test_graph, final_message, tool_call_message
from app.tools.base import ToolResult
from app.tools.registry import TOOL_REGISTRY


def _parse_events(body: str) -> list[dict]:
    events = []
    for block in body.split("\n\n"):
        line = next((l for l in block.split("\n") if l.startswith("data: ")), None)
        if line:
            events.append(json.loads(line[6:]))
    return events


@pytest_asyncio.fixture
async def client():
    from app.config import get_settings
    from app.db.session import engine, init_db
    from app.db.models import Base
    from app.api import approvals, audit, chat, health
    from app.utils.rate_limit import limiter

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await init_db()

    app = FastAPI()
    app.state.limiter = limiter
    limiter.enabled = False
    prefix = get_settings().api_prefix
    for module in (health, chat, approvals, audit):
        app.include_router(module.router, prefix=prefix)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_email_approval_round_trip(client, monkeypatch):
    sent = []

    async def fake_run(**kwargs):
        sent.append(kwargs)
        return ToolResult(ok=True, data={"to": kwargs.get("to"), "status_code": 202})

    monkeypatch.setattr(TOOL_REGISTRY["send_email"], "run", fake_run)

    test_graph = build_test_graph(
        monkeypatch,
        planner_messages=[
            tool_call_message("send_email", {"to": "a@example.com", "subject": "Hi", "body": "Yo"}),
            final_message("Email sent."),
        ],
        responder_text="Email sent.",
    )

    async def fake_get_graph():
        return test_graph

    monkeypatch.setattr("app.agent.runner.get_compiled_graph", fake_get_graph)

    # 1. Stream a turn that proposes a sensitive tool -> expect a pending_approval event.
    resp = await client.post("/api/chat/stream", json={"message": "email a@example.com"})
    assert resp.status_code == 200
    events = _parse_events(resp.text)
    pending = next(e for e in events if e["type"] == "pending_approval")
    assert pending["tool_name"] == "send_email"
    assert sent == []  # nothing sent yet

    tool_call_id = pending["tool_call_id"]

    # 2. Approve -> the tool runs and the ToolCall row flips to executed.
    resp2 = await client.post(f"/api/chat/approvals/{tool_call_id}/approve")
    assert resp2.status_code == 200
    assert len(sent) == 1

    audit = await client.get("/api/audit")
    record = next(item for item in audit.json()["items"] if item["id"] == tool_call_id)
    assert record["status"] == "executed"
