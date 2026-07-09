from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """State threaded through the agent graph and persisted by the checkpointer."""

    messages: Annotated[list[AnyMessage], add_messages]
    session_id: str
    user_id: str
    step_count: int
    # The tool call the planner most recently proposed: {"tool_call_id", "tool_name", "args"}
    pending_tool_call: dict | None
    # Result of the last executed tool: {"tool_name", "ok", "data"/"error"}
    tool_result: dict | None
    # Approval decision surfaced back from the human-in-the-loop interrupt.
    approved: bool | None
