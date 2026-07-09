from functools import lru_cache

from app.config import get_settings
from app.tools.registry import TOOL_REGISTRY


def _base_llm(temperature: float):
    settings = get_settings()
    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=settings.openai_chat_model, api_key=settings.openai_api_key, temperature=temperature)

    from langchain_groq import ChatGroq

    return ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=temperature)


@lru_cache
def get_planner_llm():
    """LLM bound to the tool specs; used by the planner node to decide the next tool call."""
    tools = [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.args_schema(),
            },
        }
        for tool in TOOL_REGISTRY.values()
    ]
    return _base_llm(temperature=0).bind_tools(tools)


@lru_cache
def get_responder_llm():
    """Plain LLM (no tools) used to synthesize the final natural-language reply."""
    return _base_llm(temperature=0.2)
