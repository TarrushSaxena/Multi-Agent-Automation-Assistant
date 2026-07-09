from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Multi-Agent Automation Assistant"
    environment: str = "development"
    api_prefix: str = "/api"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # SQLAlchemy uses the asyncpg driver; LangGraph's checkpointer uses psycopg directly,
    # so both URLs are derived from the same components but keep distinct driver prefixes.
    database_url: str = "postgresql+asyncpg://agents:agents@postgres:5432/agents"
    database_url_psycopg: str = "postgresql://agents:agents@postgres:5432/agents"

    chat_rate_limit: str = "30/hour"
    max_agent_steps: int = 6

    # Groq is the default LLM provider (free tier). OpenAI remains supported as a drop-in swap.
    llm_provider: str = "groq"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-4o-mini"

    tavily_api_key: str | None = None

    sendgrid_api_key: str | None = None
    sendgrid_from_email: str | None = None
    email_allowlist_domains: str = ""
    email_allowlist_addresses: str = ""

    google_client_secrets_path: Path = Path("secrets/credentials.json")
    google_token_path: Path = Path("secrets/token.json")
    google_calendar_timezone: str = "UTC"

    @property
    def email_allowlist_domain_set(self) -> set[str]:
        return {d.strip().lower() for d in self.email_allowlist_domains.split(",") if d.strip()}

    @property
    def email_allowlist_address_set(self) -> set[str]:
        return {a.strip().lower() for a in self.email_allowlist_addresses.split(",") if a.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
