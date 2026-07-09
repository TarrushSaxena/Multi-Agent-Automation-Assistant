import pytest
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.tests.conftest import build_test_graph, final_message, tool_call_message
from app.tools.base import ToolResult
from app.tools.registry import TOOL_REGISTRY


def _install_tool_spy(monkeypatch, tool_name: str):
    calls = []

    async def fake_run(**kwargs):
        calls.append(kwargs)
        return ToolResult(ok=True, data={"echo": kwargs})

    monkeypatch.setattr(TOOL_REGISTRY[tool_name], "run", fake_run)
    return calls


async def _drain(graph, graph_input, config):
    """Run astream and report whether an interrupt fired."""
    interrupted = False
    async for mode, chunk in graph.astream(graph_input, config, stream_mode=["updates", "messages"]):
        if mode == "updates" and "__interrupt__" in chunk:
            interrupted = True
            break
    return interrupted


@pytest.mark.asyncio
async def test_sensitive_tool_pauses_before_execution(monkeypatch):
    calls = _install_tool_spy(monkeypatch, "send_email")
    graph = build_test_graph(
        monkeypatch,
        planner_messages=[
            tool_call_message("send_email", {"to": "a@example.com", "subject": "Hi", "body": "Yo"}),
            final_message("Sent."),
        ],
    )
    config = {"configurable": {"thread_id": "t-sensitive"}}
    graph_input = {"messages": [HumanMessage(content="email a@example.com")], "step_count": 0}

    interrupted = await _drain(graph, graph_input, config)
    assert interrupted is True
    # The email must NOT have been sent while awaiting approval.
    assert calls == []


@pytest.mark.asyncio
async def test_denied_sensitive_tool_never_executes(monkeypatch):
    calls = _install_tool_spy(monkeypatch, "send_email")
    graph = build_test_graph(
        monkeypatch,
        planner_messages=[
            tool_call_message("send_email", {"to": "a@example.com", "subject": "Hi", "body": "Yo"}),
            final_message("Understood, not sending."),
        ],
    )
    config = {"configurable": {"thread_id": "t-denied"}}
    graph_input = {"messages": [HumanMessage(content="email a@example.com")], "step_count": 0}

    await _drain(graph, graph_input, config)
    await _drain(graph, Command(resume={"approved": False}), config)
    assert calls == []  # denial means the tool is never invoked


@pytest.mark.asyncio
async def test_non_sensitive_tool_runs_without_interrupt(monkeypatch):
    calls = _install_tool_spy(monkeypatch, "web_search")
    graph = build_test_graph(
        monkeypatch,
        planner_messages=[
            tool_call_message("web_search", {"query": "latest news"}),
            final_message("Here is what I found."),
        ],
    )
    config = {"configurable": {"thread_id": "t-search"}}
    graph_input = {"messages": [HumanMessage(content="search the web")], "step_count": 0}

    interrupted = await _drain(graph, graph_input, config)
    assert interrupted is False
    assert len(calls) == 1  # read-only tool executed directly
