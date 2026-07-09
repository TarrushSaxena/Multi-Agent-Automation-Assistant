import sys
import types

import pytest

from app.tools import calendar_tool
from app.tools.calendar_tool import GoogleCalendarTool


@pytest.mark.asyncio
async def test_calendar_requires_core_fields():
    result = await GoogleCalendarTool().run(summary="Sync")
    assert result.ok is False
    assert "required" in result.error


@pytest.mark.asyncio
async def test_calendar_success(monkeypatch):
    captured = {}

    class FakeEvents:
        def insert(self, calendarId, body):
            captured["calendarId"] = calendarId
            captured["body"] = body

            class _Exec:
                def execute(self_inner):
                    return {"id": "evt123", "htmlLink": "http://cal/evt123"}

            return _Exec()

    class FakeService:
        def events(self):
            return FakeEvents()

    fake_discovery = types.ModuleType("googleapiclient.discovery")
    fake_discovery.build = lambda *a, **k: FakeService()
    fake_pkg = types.ModuleType("googleapiclient")
    monkeypatch.setitem(sys.modules, "googleapiclient", fake_pkg)
    monkeypatch.setitem(sys.modules, "googleapiclient.discovery", fake_discovery)
    monkeypatch.setattr(calendar_tool, "_load_credentials", lambda: object())

    result = await GoogleCalendarTool().run(
        summary="Follow-up", start="2026-07-13T10:00:00", end="2026-07-13T10:30:00", attendees=["a@example.com"]
    )
    assert result.ok is True
    assert result.data["event_id"] == "evt123"
    # Hard-coded to primary calendar — the LLM cannot target another calendar.
    assert captured["calendarId"] == "primary"
