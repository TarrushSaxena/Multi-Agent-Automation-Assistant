"""One-time Google Calendar OAuth bootstrap.

Run locally (NOT in Docker) so a browser can open:

    cd backend
    python scripts/google_oauth_bootstrap.py

Requires secrets/credentials.json (a Desktop-app OAuth client secrets file downloaded from
Google Cloud Console). Writes a refresh token to secrets/token.json, which the calendar tool
reads at runtime. Both files are gitignored.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: E402

from app.config import get_settings  # noqa: E402

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def main() -> None:
    settings = get_settings()
    secrets_path = settings.google_client_secrets_path
    token_path = settings.google_token_path

    if not secrets_path.exists():
        raise SystemExit(
            f"Client secrets not found at {secrets_path}. Download a Desktop-app OAuth client "
            "secrets JSON from Google Cloud Console and place it there."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
    creds = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    print(f"Saved credentials to {token_path}")


if __name__ == "__main__":
    main()
