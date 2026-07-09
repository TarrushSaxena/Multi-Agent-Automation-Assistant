import pytest
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.tests.conftest import build_test_graph, final_message, tool_call_message
from app.tools.base import ToolResult
from app.tools.registry import TOOL_REGISTRY


@pytest.mark.asyncio
async def test_summarize_then_schedule_scenario(monkeypatch):
    """The spec demo: search for context, then schedule a follow-up (approved by the human)."""
    executed = []

    async def spy(name):
        async def _run(**kwargs):
            executed.append((name, kwargs))
            return ToolResult(ok=True, data={"name": name, **kwargs})

        return _run

    monkeypatch.setattr(TOOL_REGISTRY["web_search"], "run", await spy("web_search"))
    monkeypatch.setattr(TOOL_REGISTRY["create_calendar_event"], "run", await spy("create_calendar_event"))

    graph = build_test_graph(
        monkeypatch,
        planner_messages=[
            tool_call_message("web_search", {"query": "team meeting notes last week"}, "c1"),
            tool_call_message(
                "create_calendar_event",
                {"summary": "Follow-up", "start": "2026-07-13T10:00:00", "end": "2026-07-13T10:30:00"},
                "c2",
            ),
            final_message("Summarized the notes and scheduled the follow-up for Monday 10am."),
        ],
        responder_text="Summarized the notes and scheduled the follow-up for Monday 10am.",
    )
    config = {"configurable": {"thread_id": "e2e-demo"}}

    async def drain(graph_input):
        async for mode, chunk in graph.astream(graph_input, config, stream_mode=["updates", "messages"]):
            if mode == "updates" and "__interrupt__" in chunk:
                return True
        return False

    # web_search runs unguarded, then the calendar event pauses for approval.
    interrupted = await drain({"messages": [HumanMessage(content="summarize and schedule")], "step_count": 0})
    assert interrupted is True
    assert executed[0][0] == "web_search"

    # Approve the calendar event -> it executes and the run completes.
    await drain(Command(resume={"approved": True}))
    tool_names = [name for name, _ in executed]
    assert "web_search" in tool_names
    assert "create_calendar_event" in tool_names
