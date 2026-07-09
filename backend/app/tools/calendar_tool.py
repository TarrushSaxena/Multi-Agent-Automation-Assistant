from app.config import get_settings
from app.tools.base import BaseTool, ToolResult

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def _load_credentials():
    """Load OAuth credentials from the bootstrapped token file, refreshing if needed."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    settings = get_settings()
    token_path = settings.google_token_path
    if not token_path.exists():
        raise FileNotFoundError(
            f"Google token not found at {token_path}. Run scripts/google_oauth_bootstrap.py first."
        )
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json())
    return creds


class GoogleCalendarTool(BaseTool):
    name = "create_calendar_event"
    description = (
        "Create an event on the user's primary Google Calendar. Sensitive: requires human approval. "
        "start/end are ISO-8601 datetimes."
    )
    sensitive = True

    def args_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Event title."},
                "start": {"type": "string", "description": "ISO-8601 start datetime, e.g. 2026-07-13T10:00:00."},
                "end": {"type": "string", "description": "ISO-8601 end datetime."},
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional attendee email addresses.",
                },
                "description": {"type": "string", "description": "Optional event description."},
            },
            "required": ["summary", "start", "end"],
        }

    async def run(self, **kwargs) -> ToolResult:
        summary = kwargs.get("summary")
        start = kwargs.get("start")
        end = kwargs.get("end")
        if not (summary and start and end):
            return ToolResult(ok=False, error="summary, start and end are required")

        settings = get_settings()
        attendees = kwargs.get("attendees") or []
        event_body = {
            "summary": summary,
            "description": kwargs.get("description", ""),
            "start": {"dateTime": start, "timeZone": settings.google_calendar_timezone},
            "end": {"dateTime": end, "timeZone": settings.google_calendar_timezone},
            "attendees": [{"email": a} for a in attendees],
        }

        try:
            import anyio
            from googleapiclient.discovery import build

            def _create():
                creds = _load_credentials()
                service = build("calendar", "v3", credentials=creds, cache_discovery=False)
                # Hard-coded to "primary" and insert-only — the LLM cannot target another calendar or delete.
                return service.events().insert(calendarId="primary", body=event_body).execute()

            created = await anyio.to_thread.run_sync(_create)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(ok=False, error=f"calendar insert failed: {exc}")

        return ToolResult(
            ok=True,
            data={"event_id": created.get("id"), "html_link": created.get("htmlLink"), "summary": summary},
        )
