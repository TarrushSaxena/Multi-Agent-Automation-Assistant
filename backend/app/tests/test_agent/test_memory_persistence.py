import pytest
from langchain_core.messages import HumanMessage

from app.tests.conftest import build_test_graph, final_message


@pytest.mark.asyncio
async def test_state_persists_across_turns_on_same_thread(monkeypatch):
    """Two separate invocations on the same thread_id should accumulate conversation state."""
    graph = build_test_graph(
        monkeypatch,
        planner_messages=[final_message("ack"), final_message("ack")],
        responder_text="ok",
    )
    config = {"configurable": {"thread_id": "mem-thread"}}

    await graph.ainvoke({"messages": [HumanMessage(content="my name is Dana")], "step_count": 0}, config)
    await graph.ainvoke({"messages": [HumanMessage(content="what did I say?")], "step_count": 0}, config)

    state = await graph.aget_state(config)
    contents = [m.content for m in state.values["messages"]]
    # The first turn's message is still present when the second turn runs — memory persisted.
    assert "my name is Dana" in contents
    assert "what did I say?" in contents
