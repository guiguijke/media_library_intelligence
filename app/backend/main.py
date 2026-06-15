import asyncio
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.routers import (
    activity,
    auth,
    batch,
    dashboard,
    media,
    plex,
    queue,
    recommendations,
    search,
    settings,
    sync,
    tasks,
    test,
)
from app.database import engine
from app.models import Base
from app.services.settings import init_default_settings
from app.config import settings as app_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Media Library Intelligence",
    description="MLI - Recommendations and Plex library management",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


def _get_cors_origins() -> list:
    """Return allowed CORS origins. Never returns ['*'] when credentials are enabled."""
    if app_settings.DEBUG:
        return ["http://localhost:3000", "http://127.0.0.1:3000"]
    origins_str = app_settings.ALLOWED_ORIGINS or ""
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add baseline HTTP security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        if not app_settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# Auth router must be registered before the SPA catch-all.
app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(batch.router, prefix="/api")
app.include_router(queue.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(test.router, prefix="/api")
app.include_router(plex.router, prefix="/api")
app.include_router(activity.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


def run_alembic_stamp_head() -> None:
    alembic_cfg = Config("alembic.ini")
    command.stamp(alembic_cfg, "head")


def run_alembic_upgrade() -> None:
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@app.on_event("startup")
async def startup():
    # Alembic owns schema creation and migration. On a fresh database there is no
    # alembic_version table yet, so stamp at head then run migrations to create
    # all tables. On an existing database we simply migrate to head.
    async with engine.begin() as conn:
        has_version_table = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).has_table("alembic_version")
        )

    if not has_version_table:
        await asyncio.to_thread(run_alembic_stamp_head)

    await asyncio.to_thread(run_alembic_upgrade)
    await init_default_settings()

# Serve static frontend files
static_dir = "/app/static"
if os.path.isdir(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # API routes are already handled above by include_router
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"detail": "Not found"}
