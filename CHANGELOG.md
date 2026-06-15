# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-06-15

### Added

- **Search**: global title search with category/year filters and pagination (`/api/search`).
- **Navbar search**: search from any page, navigates to `/discover?q=...`.
- **Actionable wishlist**: send wishlist items directly to Radarr or Sonarr.
- **Infinite pagination**: offset/limit backend + `useInfiniteQuery` frontend.
- **TMDB collections**: model, migration, sync enrichment and dashboard integration.
- **Media detail page**: full detail view with backdrop, cast, similar, trailer and providers.
- **Tests**: 26 backend tests (pytest) and 6 frontend tests (Vitest).
- **Docker Compose** full stack: app, worker, scheduler, PostgreSQL, Redis.
- **Documentation** with screenshots and architecture diagrams.

### Changed

- README rewritten with badges, quick start, configuration table and feature cards.
- Settings UI now shows helpful placeholders for default URLs (TMDB, AniList).
- TMDB connector supports both legacy `api_key` and modern JWT `Bearer` tokens.

### Fixed

- Radarr/Sonarr test buttons showed "Connected" even when empty or failing.
- Tautulli test used non-existent `get_servers` command; now uses `get_servers_info`.
- TMDB base URL fallback was ignored when saved as empty.
- Plex sync now skips libraries mapped to **Ignore**.

## [0.1.0] - Initial release

- Basic dashboard, Discover, batch actions, Plex sync and external classics refresh.
