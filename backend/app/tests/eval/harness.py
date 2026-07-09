"""Lightweight scripted-scenario eval harness (stands in for OpenAI Evals).

Runs each scenario in scenarios.yaml through the real agent graph with mocked tools and a scripted
planner, then scores three rubric dimensions:

  1. tool_match          — the agent proposed exactly the expected tools (all within the whitelist)
  2. approval_respected  — every sensitive tool interrupted for approval before executing
  3. rubric_keywords     — the final reply contains the required keywords

Usage (from the backend/ directory):
    python -m app.tests.eval.harness
"""
import asyncio
import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./eval_agents.db")
os.environ.setdefault("OPENAI_API_KEY", "eval-key")
os.environ.setdefault("EMAIL_ALLOWLIST_DOMAINS", "example.com")

import yaml  # noqa: E402
from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402
from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from langgraph.types import Command  # noqa: E402

from app.agent import llm  # noqa: E402
from app.agent.graph import build_graph  # noqa: E402
from app.tools.base import ToolResult  # noqa: E402
from app.tools.registry import TOOL_REGISTRY, is_sensitive  # noqa: E402

SCENARIOS_PATH = Path(__file__).with_name("scenarios.yaml")


class _FakeSeq:
    def __init__(self, responses):
        self._responses = responses
        self._i = 0

    async def ainvoke(self, _messages):
        response = self._responses[min(self._i, len(self._responses) - 1)]
        self._i += 1
        return response


def _install_tool_spies():
    executed = []

    def make(name):
        async def _run(**kwargs):
            executed.append(name)
            return ToolResult(ok=True, data={"tool": name, **kwargs})

        return _run

    for name, tool in TOOL_REGISTRY.items():
        tool.run = make(name)  # type: ignore[method-assign]
    return executed


async def run_scenario(scenario: dict) -> dict:
    plan = scenario["plan"]
    planner_messages = [
        AIMessage(content="", tool_calls=[{"name": step["tool"], "args": step["args"], "id": f"c{i}", "type": "tool_call"}])
        for i, step in enumerate(plan)
    ]
    summary = f"Completed: {scenario['prompt']}"
    planner_messages.append(AIMessage(content=summary))

    planner_llm = _FakeSeq(planner_messages)
    responder_llm = _FakeSeq([AIMessage(content=summary)])
    llm.get_planner_llm = lambda: planner_llm
    llm.get_responder_llm = lambda: responder_llm

    executed = _install_tool_spies()
    graph = build_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": f"eval-{scenario['name']}"}}

    approvals_requested: list[str] = []
    graph_input = {"messages": [HumanMessage(content=scenario["prompt"])], "step_count": 0}

    # Drive the graph, auto-approving each interrupt, until it completes.
    for _ in range(len(plan) + 2):
        interrupted = False
        async for mode, chunk in graph.astream(graph_input, config, stream_mode=["updates"]):
            if "__interrupt__" in chunk:
                approvals_requested.append(chunk["__interrupt__"][0].value["tool_name"])
                interrupted = True
                break
        if not interrupted:
            break
        graph_input = Command(resume={"approved": True})

    state = await graph.aget_state(config)
    final_reply = ""
    for message in reversed(state.values.get("messages", [])):
        if isinstance(message, AIMessage) and message.content:
            final_reply = message.content
            break

    expected_tools = set(scenario["expected_tools"])
    tool_match = set(executed) == expected_tools and all(t in TOOL_REGISTRY for t in executed)
    must_approve = set(scenario.get("must_request_approval_for", []))
    approval_respected = must_approve.issubset(set(approvals_requested)) and all(
        is_sensitive(t) for t in approvals_requested
    )
    rubric_keywords = all(kw.lower() in final_reply.lower() for kw in scenario.get("must_contain", []))

    return {
        "name": scenario["name"],
        "tool_match": tool_match,
        "approval_respected": approval_respected,
        "rubric_keywords": rubric_keywords,
        "passed": tool_match and approval_respected and rubric_keywords,
    }


async def main() -> int:
    scenarios = yaml.safe_load(SCENARIOS_PATH.read_text())["scenarios"]
    results = [await run_scenario(s) for s in scenarios]

    print(f"\n{'scenario':<26} {'tools':>6} {'approval':>9} {'rubric':>7} {'result':>7}")
    print("-" * 62)
    for r in results:
        mark = lambda b: "PASS" if b else "FAIL"  # noqa: E731
        print(
            f"{r['name']:<26} {mark(r['tool_match']):>6} {mark(r['approval_respected']):>9} "
            f"{mark(r['rubric_keywords']):>7} {mark(r['passed']):>7}"
        )
    passed = sum(1 for r in results if r["passed"])
    print("-" * 62)
    print(f"{passed}/{len(results)} scenarios passed\n")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
