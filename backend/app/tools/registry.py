from app.tools.base import BaseTool
from app.tools.calendar_tool import GoogleCalendarTool
from app.tools.email_tool import SendGridEmailTool
from app.tools.search_tool import TavilySearchTool

# The agent may ONLY call tools registered here — this is the whitelist enforcement point.
TOOL_REGISTRY: dict[str, BaseTool] = {
    tool.name: tool
    for tool in (TavilySearchTool(), SendGridEmailTool(), GoogleCalendarTool())
}

SENSITIVE_TOOLS: set[str] = {name for name, tool in TOOL_REGISTRY.items() if tool.sensitive}


def get_tool(name: str) -> BaseTool | None:
    return TOOL_REGISTRY.get(name)


def is_sensitive(name: str) -> bool:
    return name in SENSITIVE_TOOLS


def openai_tool_specs() -> list[dict]:
    return [tool.openai_tool_spec() for tool in TOOL_REGISTRY.values()]
