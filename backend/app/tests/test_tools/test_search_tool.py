import sys
import types

import pytest

from app.tools.search_tool import TavilySearchTool


@pytest.mark.asyncio
async def test_search_requires_query():
    result = await TavilySearchTool().run(query="  ")
    assert result.ok is False
    assert "required" in result.error


@pytest.mark.asyncio
async def test_search_success(monkeypatch):
    captured = {}

    class FakeClient:
        def __init__(self, api_key):
            captured["api_key"] = api_key

        def search(self, query, max_results, include_answer):
            captured["query"] = query
            return {"answer": "42", "results": [{"title": "T", "url": "u", "content": "c"}]}

    fake_module = types.ModuleType("tavily")
    fake_module.TavilyClient = FakeClient
    monkeypatch.setitem(sys.modules, "tavily", fake_module)

    result = await TavilySearchTool().run(query="meaning of life")
    assert result.ok is True
    assert result.data["answer"] == "42"
    assert result.data["results"][0]["title"] == "T"
    assert captured["query"] == "meaning of life"
