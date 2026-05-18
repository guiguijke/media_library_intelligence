import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routers import dashboard, recommendations, batch, queue, sync, settings, tasks, test, plex, activity
from app.database import engine
from app.models import Base
from app.services.settings import init_default_settings
from sqlalchemy import text

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
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


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add missing columns to existing tables (create_all doesn't alter)
        await conn.execute(text("""
            ALTER TABLE plex_library
            ADD COLUMN IF NOT EXISTS collections JSON,
            ADD COLUMN IF NOT EXISTS rating_key VARCHAR,
            ADD COLUMN IF NOT EXISTS tvdb_id INTEGER,
            ADD COLUMN IF NOT EXISTS imdb_id VARCHAR,
            ADD COLUMN IF NOT EXISTS collection_id INTEGER,
            ADD COLUMN IF NOT EXISTS collection_name VARCHAR
        """))
        await conn.execute(text("""
            ALTER TABLE external_classics
            ADD COLUMN IF NOT EXISTS tvdb_id INTEGER
        """))
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

