from app.config import get_settings
from app.tools.base import BaseTool, ToolResult


class SendGridEmailTool(BaseTool):
    name = "send_email"
    description = "Send an email via SendGrid. Sensitive: requires human approval before sending."
    sensitive = True

    def args_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address."},
                "subject": {"type": "string", "description": "Email subject line."},
                "body": {"type": "string", "description": "Plain-text email body."},
            },
            "required": ["to", "subject", "body"],
        }

    @staticmethod
    def _is_allowlisted(address: str) -> bool:
        settings = get_settings()
        address = address.strip().lower()
        if address in settings.email_allowlist_address_set:
            return True
        domain = address.split("@")[-1] if "@" in address else ""
        return domain in settings.email_allowlist_domain_set

    async def run(self, **kwargs) -> ToolResult:
        to = (kwargs.get("to") or "").strip()
        subject = kwargs.get("subject") or ""
        body = kwargs.get("body") or ""
        if not to:
            return ToolResult(ok=False, error="recipient 'to' is required")

        # Whitelist check happens BEFORE any network call — the agent may only email allowlisted recipients.
        if not self._is_allowlisted(to):
            return ToolResult(ok=False, error=f"recipient not allowlisted: {to}")

        settings = get_settings()
        if not settings.sendgrid_api_key or not settings.sendgrid_from_email:
            return ToolResult(ok=False, error="SENDGRID_API_KEY / SENDGRID_FROM_EMAIL not configured")

        try:
            import anyio
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            message = Mail(
                from_email=settings.sendgrid_from_email,
                to_emails=to,
                subject=subject,
                plain_text_content=body,
            )
            client = SendGridAPIClient(settings.sendgrid_api_key)
            response = await anyio.to_thread.run_sync(lambda: client.send(message))
        except Exception as exc:  # noqa: BLE001
            return ToolResult(ok=False, error=f"send failed: {exc}")

        return ToolResult(ok=True, data={"to": to, "subject": subject, "status_code": response.status_code})
