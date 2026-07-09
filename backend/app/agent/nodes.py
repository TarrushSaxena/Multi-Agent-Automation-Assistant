import uuid

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.types import interrupt

from app.agent.prompts import SYSTEM_PLANNER_PROMPT, SYSTEM_RESPOND_PROMPT
from app.agent.state import AgentState
from app.config import get_settings
from app.tools.registry import get_tool, is_sensitive

settings = get_settings()


async def planner_node(state: AgentState) -> dict:
    """Ask the LLM for the next step. Either it proposes a tool call or produces a final answer."""
    from app.agent.llm import get_planner_llm

    messages = [SystemMessage(content=SYSTEM_PLANNER_PROMPT)] + list(state.get("messages", []))
    ai: AIMessage = await get_planner_llm().ainvoke(messages)

    tool_calls = ai.tool_calls or []
    if not tool_calls:
        # No tool requested — planner is done, fall through to respond.
        return {"messages": [ai], "pending_tool_call": None}

    call = tool_calls[0]
    pending = {
        "tool_call_id": call.get("id") or str(uuid.uuid4()),
        "tool_name": call["name"],
        "args": call.get("args", {}),
    }
    return {"messages": [ai], "pending_tool_call": pending}


def route_after_planner(state: AgentState) -> str:
    if state.get("pending_tool_call"):
        return "guardrail_check"
    return "respond"


async def guardrail_node(state: AgentState) -> dict:
    """No-op transform node; routing decision lives in route_after_guardrail."""
    return {}


def route_after_guardrail(state: AgentState) -> str:
    pending = state.get("pending_tool_call")
    if pending and is_sensitive(pending["tool_name"]):
        return "human_approval"
    return "tool_execute"


def human_approval_node(state: AgentState) -> dict:
    """Pause the graph and surface the pending tool call for a human decision.

    `interrupt` suspends execution; LangGraph persists state via the checkpointer and the API
    layer resumes with Command(resume={"approved": bool}).
    """
    pending = state.get("pending_tool_call")
    decision = interrupt(
        {
            "type": "approval_request",
            "tool_call_id": pending["tool_call_id"],
            "tool_name": pending["tool_name"],
            "args": pending["args"],
        }
    )
    approved = bool(decision.get("approved")) if isinstance(decision, dict) else bool(decision)
    return {"approved": approved}


def route_after_approval(state: AgentState) -> str:
    return "tool_execute" if state.get("approved") else "denied"


async def tool_execute_node(state: AgentState) -> dict:
    """Run the approved (or non-sensitive) tool and append the result as a ToolMessage."""
    pending = state["pending_tool_call"]
    tool = get_tool(pending["tool_name"])
    if tool is None:
        result = {"tool_name": pending["tool_name"], "ok": False, "error": "unknown tool"}
    else:
        outcome = await tool.run(**pending["args"])
        result = {"tool_name": pending["tool_name"], "ok": outcome.ok, "data": outcome.data, "error": outcome.error}

    tool_message = ToolMessage(
        content=str(result.get("data") if result["ok"] else result.get("error")),
        tool_call_id=pending["tool_call_id"],
    )
    return {
        "messages": [tool_message],
        "tool_result": result,
        "pending_tool_call": None,
        "approved": None,
        "step_count": state.get("step_count", 0) + 1,
    }


def route_after_execute(state: AgentState) -> str:
    if state.get("step_count", 0) >= settings.max_agent_steps:
        return "respond"
    return "planner"


def denied_node(state: AgentState) -> dict:
    """Record that the user declined the pending action, then let the responder acknowledge it."""
    pending = state.get("pending_tool_call")
    note = ToolMessage(
        content=f"The user DENIED the '{pending['tool_name']}' action. It was not performed.",
        tool_call_id=pending["tool_call_id"],
    )
    return {
        "messages": [note],
        "tool_result": {"tool_name": pending["tool_name"], "ok": False, "error": "denied by user"},
        "pending_tool_call": None,
        "approved": None,
    }


async def respond_node(state: AgentState) -> dict:
    """Synthesize the final natural-language reply from the conversation so far."""
    from app.agent.llm import get_responder_llm

    messages = [SystemMessage(content=SYSTEM_RESPOND_PROMPT)] + list(state.get("messages", []))
    reply = await get_responder_llm().ainvoke(messages)
    return {"messages": [reply]}
