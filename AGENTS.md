# Agent Context — Media Library Intelligence

## Architecture

- **Backend**: Python 3.11, FastAPI, SQLAlchemy async, Celery + Redis
- **Frontend**: React 18, Vite, TailwindCSS, React Query, React Router
- **Database**: PostgreSQL 15 (migrations via `Base.metadata.create_all` + raw `ALTER TABLE` for drift)
- **Container**: Docker Compose (`app`, `worker`, `scheduler`, `db`, `redis`)
- **API prefix**: `/api` — no trailing slashes on routes (SPA fallback conflict)

## Critical Technical Constraints

### SPA Fallback Conflict
FastAPI serves static files with a `/{full_path:path}` catch-all fallback for the SPA.
**API routes must be registered BEFORE the SPA catch-all.**
Router definitions must use `@router.get("")` (not `"/"`) when mounted with `prefix="/api"`, otherwise the trailing-slash route `/api/recommendations/` falls through to the SPA fallback.

### Celery Chain Argument Passing
Chained tasks receive the previous task result as the **first positional argument**.
Task signatures must accept `(self, previous_result=None)`.

### Database Schema Drift
`Base.metadata.create_all` only creates **new tables**, never alters existing ones.
All column additions must be done via raw `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` in `main.py` startup.

### Category System
Internal categories (`CategoryEnum`):
- `movie`, `series`, `anime`, `cartoon`, `ignore`

Plex uses `movie`/`show`. The sync task maps `show` → `series`/`anime`/`cartoon` based on genres and `original_language`.
The Discover UI exposes: **All | Movies | TV Shows | Animation** (where Animation = `anime` + `cartoon`).

### External GUID Extraction (Plex)
Plex `guid` fields are internal (`plex://...`). External IDs (TMDb, TVDb, IMDb) are only returned when `includeGuids=1` is passed to section/item endpoints.
The `PlexConnector.get_library()` **must** pass `params={"includeGuids": "1"}`.

### Recommendations Deduplication
Recommendations filter out already-owned content by checking:
1. `tmdb_id` match between `PlexLibrary` and `ExternalClassics`
2. `tvdb_id` match
3. `anilist_id` match
4. Exact normalized title match
5. Root title match (part before `:` or `-`)

## Build & Deploy

```bash
docker compose build app worker scheduler
docker compose up -d
```

The frontend is built into `app/frontend/dist` during Docker build and served from `/app/static`.
No hot-reload: code changes require `docker compose build` + `docker compose up -d`.

## Testing External APIs

You can test connectors directly inside the `app` container:

```bash
docker compose exec app python -c "
import asyncio
from app.connectors.plex import PlexConnector
async def main():
    c = PlexConnector()
    items = await c.get_library()
    print(len(items))
asyncio.run(main())
"
```

## Common Gotchas

- **Redis connection retry**: Celery worker logs `CPendingDeprecationWarning` about `broker_connection_retry_on_startup`. Non-blocking.
- **TMDB animation discover**: `original_language` field must be explicitly extracted from TMDB results. Missing it causes all animation to be classified as `cartoon`.
- **Radarr/Sonarr root folders**: Hardcoded paths (`/movies`, `/tv`) will fail if the *arr instance uses custom root folders. Always query `/api/v3/rootfolder` dynamically.
- **Radarr/Sonarr add**: The APIs expect the **full lookup object** with overrides, not a minimal payload.
- **Batch actions**: `BatchActionBar` filters recommendations client-side by `category === 'movie' || category === 'cartoon'` for Radarr and `category === 'series' || category === 'anime'` for Sonarr.
