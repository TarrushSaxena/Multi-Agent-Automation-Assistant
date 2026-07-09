from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse

from app.agent.checkpointer import close_checkpointer, get_checkpointer
from app.api import approvals, audit, chat, health
from app.config import get_settings
from app.db.session import init_db
from app.utils.logger import configure_logging
from app.utils.rate_limit import limiter

settings = get_settings()
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await get_checkpointer()  # create LangGraph checkpoint tables + open the pool
    yield
    await close_checkpointer()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "message": "Multi-Agent Automation Assistant backend", "docs": "/docs"}


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(_, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": str(exc.detail)})


app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(chat.router, prefix=settings.api_prefix)
app.include_router(approvals.router, prefix=settings.api_prefix)
app.include_router(audit.router, prefix=settings.api_prefix)
