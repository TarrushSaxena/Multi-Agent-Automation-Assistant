import os

# Point every settings-derived component at a throwaway sqlite DB BEFORE app modules import.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_agents.db")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily")
os.environ.setdefault("SENDGRID_API_KEY", "test-sendgrid")
os.environ.setdefault("SENDGRID_FROM_EMAIL", "agent@example.com")
os.environ.setdefault("EMAIL_ALLOWLIST_DOMAINS", "example.com")

from langchain_core.messages import AIMessage  # noqa: E402


class FakeSequenceLLM:
    """Returns a preset sequence of AIMessages on successive ainvoke calls (last one repeats)."""

    def __init__(self, responses: list[AIMessage]):
        self._responses = responses
        self._i = 0

    async def ainvoke(self, _messages):
        response = self._responses[min(self._i, len(self._responses) - 1)]
        self._i += 1
        return response


def tool_call_message(name: str, args: dict, call_id: str = "call_test") -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id, "type": "tool_call"}])


def final_message(text: str) -> AIMessage:
    return AIMessage(content=text)


def build_test_graph(monkeypatch, planner_messages: list[AIMessage], responder_text: str = "Done."):
    """Compile the real agent graph with fake LLMs and an in-memory checkpointer for fast tests."""
    from langgraph.checkpoint.memory import MemorySaver

    from app.agent import llm
    from app.agent.graph import build_graph

    # A single persistent fake — get_planner_llm() is called on every planner step, so the
    # sequence must advance across calls rather than reset each time.
    planner_llm = FakeSequenceLLM(planner_messages)
    responder_llm = FakeSequenceLLM([final_message(responder_text)])
    monkeypatch.setattr(llm, "get_planner_llm", lambda: planner_llm)
    monkeypatch.setattr(llm, "get_responder_llm", lambda: responder_llm)
    return build_graph(checkpointer=MemorySaver())
