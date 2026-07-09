import sys
import types

import pytest

from app.tools.email_tool import SendGridEmailTool


@pytest.mark.asyncio
async def test_email_rejects_non_allowlisted_recipient():
    # example.com is allowlisted in conftest; evil.com is not.
    result = await SendGridEmailTool().run(to="attacker@evil.com", subject="hi", body="x")
    assert result.ok is False
    assert "not allowlisted" in result.error


@pytest.mark.asyncio
async def test_email_success_for_allowlisted_recipient(monkeypatch):
    sent = {}

    class FakeResponse:
        status_code = 202

    class FakeClient:
        def __init__(self, api_key):
            sent["api_key"] = api_key

        def send(self, message):
            sent["sent"] = True
            return FakeResponse()

    sendgrid_mod = types.ModuleType("sendgrid")
    sendgrid_mod.SendGridAPIClient = FakeClient
    helpers_mod = types.ModuleType("sendgrid.helpers")
    mail_mod = types.ModuleType("sendgrid.helpers.mail")
    mail_mod.Mail = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, "sendgrid", sendgrid_mod)
    monkeypatch.setitem(sys.modules, "sendgrid.helpers", helpers_mod)
    monkeypatch.setitem(sys.modules, "sendgrid.helpers.mail", mail_mod)

    result = await SendGridEmailTool().run(to="analyst@example.com", subject="Kickoff", body="Hello")
    assert result.ok is True
    assert result.data["status_code"] == 202
    assert sent["sent"] is True
