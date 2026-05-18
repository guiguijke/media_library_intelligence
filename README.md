# 🎬 Media Library Intelligence (MLI)

Full-stack web application for intelligent Plex library development, deployable via Docker Compose.

## ✨ Features

- **Analytics Dashboard**: library stats, watch trends, incomplete saga completion
- **Smart Recommendations**: 3 pillars (saga completion, client tastes, missing classics) with 0-100 scoring
- **Visual Discovery**: responsive poster grid, detail sheets, multi-criteria filters (Movies, TV Shows, Animation)
- **Batch Management**: multi-select + direct send to Sonarr / Radarr
- **Download Queue**: track Sonarr/Radarr download status
- **Strict Exclusions**: horror and adult content automatically filtered
- **Auto Sync**: weekly classic refresh via Celery Beat
- **Web-based Settings**: configure all platform URLs and API keys directly in the UI
- **Plex-aware Discover**: recommendations automatically hide content already in your Plex library (via TMDb/TVDb ID matching)

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   FastAPI   │────▶│  PostgreSQL │
│  React+Vite │◀────│   Backend   │◀────│    + Redis  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
    ┌───────┐        ┌─────────┐       ┌──────────┐
    │  TMDB │        │ AniList │       │  Plex    │
    └───────┘        └─────────┘       ├──────────┤
                                       │ Tautulli │
                                       │  Sonarr  │
                                       │  Radarr  │
                                       └──────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

- Docker + Docker Compose

### 2. Launch

```bash
git clone <repo-url>
cd media_library_intelligence
docker compose up --build
```

The app is available at: **http://localhost:3000**

### 3. First-time Configuration

1. Open the app and go to **Settings** (gear icon in the navbar)
2. Fill in your platform credentials:

| Platform | Required fields | How to obtain |
|----------|----------------|---------------|
| **Plex** | URL, Token | Plex Web → Settings → General → Advanced → "Show token" |
| **Tautulli** | URL, API Key | Tautulli → Settings → Web Interface → API |
| **TMDB** | API Key | [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api) |
| **Sonarr** | URL, API Key | Sonarr → Settings → General → Security |
| **Radarr** | URL, API Key | Radarr → Settings → General → Security |

3. Click **Save**, then go to the **Dashboard** and click **Sync** to scan your library

> ⚠️ **Security note**: API keys and tokens are stored in the PostgreSQL database. They are masked (*****) in the public settings view and only exposed to the backend connectors.

## 📁 Project Structure

```
.
├── docker-compose.yml          # Full stack (only DB/Redis env vars needed)
├── .env.example                # Empty - all config is in the UI
├── app/
│   ├── Dockerfile              # Multi-stage build (Node + Python)
│   ├── backend/                # FastAPI
│   │   ├── main.py
│   │   ├── app/
│   │   │   ├── connectors/     # Plex, Tautulli, TMDB, AniList, Sonarr, Radarr
│   │   │   ├── routers/        # API endpoints
│   │   │   ├── services/       # DB-based settings service
│   │   │   ├── tasks/          # Celery tasks
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   └── requirements.txt
│   └── frontend/               # React + TailwindCSS
│       ├── src/
│       │   ├── components/     # Reusable UI
│       │   ├── pages/          # Dashboard, Discover, Queue, Wishlist, Settings
│       │   └── hooks/          # React Query hooks
│       └── package.json
```

## ⚙️ Environment Variables (optional)

Only `DATABASE_URL` and `REDIS_URL` are read from the environment (handled automatically by Docker Compose). All other settings are managed via the web UI.

```env
# Only needed if you run outside Docker
DATABASE_URL=postgresql+asyncpg://mli:mli@localhost:5432/mli
REDIS_URL=redis://localhost:6379
```

## 🔄 Scheduled Tasks (Celery Beat)

| Task | Frequency | Description |
|------|-----------|-------------|
| `refresh_external_classics` | Weekly | Fetch TMDB + AniList top rated & animation discover |
| `sync_plex_library` | Manual/Startup | Full Plex library scan with external GUID extraction |
| `sync_tautulli_stats` | Manual | Fetch watch statistics |

## 🛡️ Content Exclusions

- ❌ **Horror** (TMDB genre id 27)
- ❌ **Adult / Erotic** (Adult, Erotica genres, explicit keywords)
- ❌ **Hentai / Ecchi** (corresponding AniList genres)

## 📜 License

MIT
