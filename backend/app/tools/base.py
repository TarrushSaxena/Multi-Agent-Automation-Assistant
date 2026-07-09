from abc import ABC, abstractmethod

from pydantic import BaseModel


class ToolResult(BaseModel):
    ok: bool
    data: dict | None = None
    error: str | None = None


class BaseTool(ABC):
    """Contract every tool adapter implements.

    `name` is what the LLM references; `sensitive` decides whether the graph pauses
    for human approval before `run()` is called.
    """

    name: str
    description: str
    sensitive: bool = False

    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        """Execute the tool. Never raise for expected failures — return ToolResult(ok=False, ...)."""

    @abstractmethod
    def args_schema(self) -> dict:
        """JSON schema of the tool's arguments, used to bind the tool to the LLM."""

    def openai_tool_spec(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.args_schema(),
            },
        }
