# 🎬 Media Library Intelligence

<p align="center">
  <strong>Discover, organize, and expand your Plex library intelligently.</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-development">Development</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Celery-37814A?logo=celery&logoColor=white" alt="Celery">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

---

## ✨ Features

| | |
|:---|:---|
| 🧠 **Smart Recommendations** | 0-100 score based on three pillars: incomplete sagas, user tastes, and missing classics. |
| 🔍 **Global Search** | Search bar in the navbar to instantly find a title across the entire catalog. |
| 🎨 **Immersive Discover** | Responsive poster grid, detail sheets, trailers, and streaming providers. |
| 📚 **Saga Management** | Automatic TMDB collection detection and suggestions to complete a movie series. |
| ⚡ **Quick Actions** | One-click add to **Radarr** (movies) or **Sonarr** (series), or save to the wishlist. |
| 📦 **Download Queue** | Real-time tracking of Radarr/Sonarr requests and their progress. |
| 💖 **Actionable Wishlist** | Wishlist with direct send to Radarr/Sonarr. |
| 🚫 **Strict Content Filtering** | Horror, adult, hentai/ecchi automatically filtered out. |
| 🔄 **Plex Sync** | Full library scan with external GUID extraction (TMDb, TVDb, IMDb). |
| ⚙️ **100% Web Configuration** | URLs and API keys entered directly in the UI, encrypted at rest in the database. |

## 🚀 Quick Start

### Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### 1. Clone the project

```bash
git clone <repo-url>
cd media_library_intelligence
```

### 2. Launch the stack

```bash
docker compose up --build -d
```

> The first build compiles the React frontend and installs Python dependencies.

### 3. Open the app

Go to: **http://localhost:3000**

Default credentials:

- **Username**: `admin`
- **Password**: `admin`

> Change the admin password in Settings on first login.

## ⚙️ Configuration

Once the app is running, click **Settings** (⚙️ in the navbar) and fill in your connectors:

| Platform | Required fields | Where to find the key |
|----------|----------------|-----------------------|
| **Plex** | Server URL, Token | Plex Web → Settings → General → Advanced → Show token |
| **Tautulli** | URL, API Key | Tautulli → Settings → Web Interface → API |
| **TMDB** | API Key / Read Access Token | [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api) |
| **Sonarr** | URL, API Key | Sonarr → Settings → General → Security |
| **Radarr** | URL, API Key | Radarr → Settings → General → Security |
| **AniList** | Client ID (optional) | [anilist.co/settings/developer](https://anilist.co/settings/developer) |

After saving:

1. Go to the **Dashboard**.
2. Click **Sync** to run a full Plex library scan.
3. Go to **Discover** to explore your recommendations.

> 🔐 **Security**: API keys and tokens are encrypted in PostgreSQL and never exposed to the client.

## 🏗️ Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│    Frontend     │◄────►│    FastAPI      │◄────►│   PostgreSQL    │
│  React + Vite   │      │    Backend      │      │     + Redis     │
│ TailwindCSS +   │      │   SQLAlchemy    │      │                 │
│   React Query   │      │  Celery + JWT   │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           ▼                    ▼                    ▼
      ┌─────────┐         ┌───────────┐        ┌───────────┐
      │  TMDB   │         │  AniList  │        │   Plex    │
      └─────────┘         └───────────┘        ├───────────┤
                                               │ Tautulli  │
                                               │  Sonarr   │
                                               │  Radarr   │
                                               └───────────┘
```

### Docker Services

| Service | Role | Exposed Port |
|---------|------|--------------|
| `app` | FastAPI backend + static frontend | `3000` |
| `worker` | Celery workers for background tasks | — |
| `scheduler` | Celery Beat for scheduled tasks | — |
| `db` | PostgreSQL 17 | `5432` (internal) |
| `redis` | Redis 7.4 (Celery broker + cache) | `6379` (internal) |

## 📁 Project Structure

```
media_library_intelligence/
├── docker-compose.yml          # Full Docker stack
├── .env.example                # Minimal infrastructure variables
├── CHANGELOG.md                # Release notes
├── app/
│   ├── Dockerfile              # Multi-stage Node + Python build
│   ├── backend/
│   │   ├── main.py             # FastAPI entry point
│   │   ├── app/
│   │   │   ├── connectors/     # Plex, Tautulli, TMDB, AniList, Sonarr, Radarr
│   │   │   ├── routers/        # API endpoints (/api/...)
│   │   │   ├── services/       # Business logic & encrypted settings
│   │   │   ├── tasks/          # Celery tasks
│   │   │   ├── models.py       # SQLAlchemy models
│   │   │   └── schemas.py      # Pydantic schemas
│   │   ├── tests/              # Backend tests (pytest)
│   │   └── alembic/            # Database migrations
│   └── frontend/
│       ├── src/
│       │   ├── components/     # Reusable UI components
│       │   ├── pages/          # Dashboard, Discover, Queue, Wishlist, Settings, Media
│       │   └── hooks/          # React Query hooks
│       └── package.json
└── README.md
```

## 🔄 Scheduled Tasks (Celery Beat)

| Task | Frequency | Description |
|------|-----------|-------------|
| `refresh_external_classics` | Weekly | Fetch popular & top-rated movies, series, and animation from TMDB + AniList. |
| `sync_plex_library` | Manual / nightly | Full Plex library scan with external GUID extraction. |
| `sync_tautulli_stats` | Manual | Fetch watch statistics from Tautulli. |

## 🛠️ Development

### Run tests

**Backend:**

```bash
docker compose --env-file .env run --rm --no-deps worker python -m pytest tests/ -v
```

**Frontend:**

```bash
cd app/frontend
npm test
```

### Rebuild after changes

```bash
docker compose build app worker scheduler
docker compose up -d
```

> The frontend is built once into the Docker image. There is no hot-reload inside the container.

## 🛡️ Content Exclusions

- ❌ **Horror** (TMDB genre id 27)
- ❌ **Adult / Erotic** (Adult, Erotica genres, explicit keywords)
- ❌ **Hentai / Ecchi** (corresponding AniList genres)

## 📝 Environment Variables

Only infrastructure variables are required. All platform keys are configured through the UI.

```env
DATABASE_URL=postgresql+asyncpg://mli:mli@db:5432/mli
REDIS_URL=redis://redis:6379
SECRET_KEY=change-me-to-a-random-string-of-at-least-32-characters
```

## 📜 License

MIT — see the [LICENSE](LICENSE) file.

---

<p align="center">
  Made with ❤️ for slightly chaotic Plex libraries.
</p>
