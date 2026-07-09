from app.config import get_settings
from app.tools.base import BaseTool, ToolResult


class TavilySearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for current information. Read-only; returns a list of result snippets."
    sensitive = False

    def args_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."},
            },
            "required": ["query"],
        }

    async def run(self, **kwargs) -> ToolResult:
        query = (kwargs.get("query") or "").strip()
        if not query:
            return ToolResult(ok=False, error="query is required")

        settings = get_settings()
        if not settings.tavily_api_key:
            return ToolResult(ok=False, error="TAVILY_API_KEY not configured")

        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=settings.tavily_api_key)
            # tavily-python is sync; run it off the event loop.
            import anyio

            response = await anyio.to_thread.run_sync(
                lambda: client.search(query=query, max_results=5, include_answer=True)
            )
        except Exception as exc:  # noqa: BLE001 - surface any client/network error as a ToolResult
            return ToolResult(ok=False, error=f"search failed: {exc}")

        results = [
            {"title": r.get("title"), "url": r.get("url"), "content": r.get("content")}
            for r in response.get("results", [])
        ]
        return ToolResult(ok=True, data={"answer": response.get("answer"), "results": results})
