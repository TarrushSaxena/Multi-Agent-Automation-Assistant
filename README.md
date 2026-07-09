# Multi-Agent Automation Assistant

An agentic AI co-pilot that turns a high-level intent (*"Summarize last week's meeting and schedule a follow-up next Monday at 10am"*) into an autonomous, multi-step workflow across real tools — web search, email, and calendar — with human-in-the-loop approval on sensitive actions and a full audit log.

This is the MVP slice of a larger planned system (see [Phase 2](#phase-2--not-built-yet) below for what's deliberately deferred).

## Architecture

- **Agent core**: [LangGraph](https://github.com/langchain-ai/langgraph) (Python) — a stateful graph (`planner → guardrail_check → human_approval | tool_execute → respond`) with Postgres-backed checkpointing for real multi-turn memory.
- **Backend**: FastAPI, SQLAlchemy (async) + Alembic on Postgres, SSE streaming to the frontend.
- **Tools**: Tavily (web search, read-only), SendGrid (email, gated), Google Calendar (event creation, gated).
- **Guardrails**: sending email or creating a calendar event pauses the graph (`interrupt`) until a human approves or denies via the UI. Every proposed tool call — approved or not — is written to an audit log (`tool_calls` table) with full arguments, status, and timestamps.
- **Frontend**: Next.js + Tailwind chat UI (adapted from a sibling project), plus an `/audit` activity-log page.

## Local setup

### 1. Prerequisites

- Docker + Docker Compose
- API keys/credentials for the three tools (see below) — the app runs without them, but tool calls will fail until configured.

### 2. Environment

```
cp .env.example .env
cp backend/.env.example backend/.env
```

Fill in `backend/.env`:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string (defaults to the compose service) |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) — free tier, single API key |
| `SENDGRID_API_KEY` | [SendGrid](https://sendgrid.com) — free tier (100 emails/day), needs one verified sender identity |
| `SENDGRID_FROM_EMAIL` | The verified sender address |
| `EMAIL_ALLOWLIST_DOMAINS` / `EMAIL_ALLOWLIST_ADDRESSES` | Comma-separated allowlist — the agent refuses to email anyone outside this list |
| `GOOGLE_CLIENT_SECRETS_PATH` | Path to the OAuth client secrets JSON (see below) |
| `GOOGLE_TOKEN_PATH` | Where the bootstrapped refresh token is stored (default `backend/secrets/token.json`) |

### 3. Google Calendar OAuth (one-time)

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/), enable the **Google Calendar API**.
2. Create an OAuth **Desktop app** client ID, download the client secrets JSON to `backend/secrets/credentials.json` (gitignored).
3. Run the bootstrap script once, locally (not in Docker, so a browser can open):
   ```
   cd backend
   python scripts/google_oauth_bootstrap.py
   ```
   This opens a consent screen and writes a refresh token to `backend/secrets/token.json`.

### 4. Run

```
docker compose up --build
```

- Backend: http://localhost:8000/docs
- Frontend: http://localhost:3000

### 5. Tests

```
pip install -r backend/requirements.txt
pytest
python -m app.tests.eval.harness   # scripted scenario eval, run from backend/
```

## Safety model

- **Whitelisted tools only** — the agent can only call tools in `TOOL_REGISTRY`; there is no free-form code execution or arbitrary API access.
- **Human approval on sensitive actions** — `send_email` and `create_calendar_event` always interrupt the graph for explicit approval before executing.
- **Allowlisted recipients** — email sends are rejected before hitting the SendGrid API if the recipient isn't covered by `EMAIL_ALLOWLIST_DOMAINS`/`EMAIL_ALLOWLIST_ADDRESSES`.
- **Create-only calendar scope** — the calendar tool only creates events on the primary calendar; it cannot update or delete anything.
- **Full audit trail** — every proposed tool call is logged with arguments, approval status, and result, queryable via `/api/audit` and the `/audit` UI page.

## Phase 2 (not built yet)

Documented here so scope is explicit, not silently dropped:

- Kubernetes manifests / Helm chart, Terraform for cloud infra
- A Slack bot front-end reusing the same backend
- Full OpenAI Agents SDK / OpenAI Evals adoption (this MVP uses LangGraph + a custom eval harness instead)
- Celery-backed scheduled/background jobs (e.g. digest emails)
- Calendar event update/delete support
- Multi-user auth (currently a single `demo-user`, matching the sibling project's convention)
