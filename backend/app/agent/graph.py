from langgraph.graph import END, START, StateGraph

from app.agent import nodes
from app.agent.checkpointer import get_checkpointer
from app.agent.state import AgentState

_compiled = None


def build_graph(checkpointer=None):
    """Assemble the agent graph:

    planner -> (tool needed?) -> guardrail_check -> (sensitive?) -> human_approval -> (approved?) ->
    tool_execute -> (loop / cap) -> planner ... -> respond -> END
    """
    graph = StateGraph(AgentState)

    graph.add_node("planner", nodes.planner_node)
    graph.add_node("guardrail_check", nodes.guardrail_node)
    graph.add_node("human_approval", nodes.human_approval_node)
    graph.add_node("tool_execute", nodes.tool_execute_node)
    graph.add_node("denied", nodes.denied_node)
    graph.add_node("respond", nodes.respond_node)

    graph.add_edge(START, "planner")
    graph.add_conditional_edges(
        "planner",
        nodes.route_after_planner,
        {"guardrail_check": "guardrail_check", "respond": "respond"},
    )
    graph.add_conditional_edges(
        "guardrail_check",
        nodes.route_after_guardrail,
        {"human_approval": "human_approval", "tool_execute": "tool_execute"},
    )
    graph.add_conditional_edges(
        "human_approval",
        nodes.route_after_approval,
        {"tool_execute": "tool_execute", "denied": "denied"},
    )
    graph.add_conditional_edges(
        "tool_execute",
        nodes.route_after_execute,
        {"planner": "planner", "respond": "respond"},
    )
    graph.add_edge("denied", "respond")
    graph.add_edge("respond", END)

    return graph.compile(checkpointer=checkpointer)


async def get_compiled_graph():
    """Process-wide compiled graph backed by the Postgres checkpointer."""
    global _compiled
    if _compiled is None:
        checkpointer = await get_checkpointer()
        _compiled = build_graph(checkpointer=checkpointer)
    return _compiled
