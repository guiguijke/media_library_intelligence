# Changelog

All notable changes to this project will be documented in this file.

## [1.1.5] - 2026-06-16

### Added

- **Actionable saga completion**: Dashboard saga cards now expose `actionable_missing_count`, counting only missing movies not already in Radarr.
- Added a loading skeleton to the **Saga Completion** section while stats are loading.

### Changed

- Dashboard `/stats` now hides:
  - complete TMDB collections (`owned == total`);
  - incomplete collections whose missing items are already monitored in Radarr.
- Heuristic title-based sagas now return `missing_count` and `actionable_missing_count`.

### Fixed

- The Dashboard showed "All sagas are complete" during the initial stats loading state.

## [1.1.4] - 2026-06-16

### Added

- **Plex sync incremental mode**: unchanged movies and series are now skipped during Plex library sync.
- Added `PlexLibrary.sync_hash` column and Alembic migration `0005_plex_library_sync_hash`.

### Changed

- `sync_plex_library` now computes a stable hash from synced fields and compares it with the stored `sync_hash` before writing.
- TMDB collection enrichment cache now skips re-lookup for movies already known to have no collection.

### Fixed

- Plex library sync re-processed every item on every run, causing unnecessary database writes and TMDB API calls.

## [1.1.3] - 2026-06-15

### Added

- **Saga completion actions** on the Dashboard: incomplete TMDB collections now show "Add X missing" and "View missing" buttons.
- `GET /api/dashboard/collections/{collection_id}/missing` returns the list of missing movies for a TMDB collection.
- `POST /api/dashboard/collections/{collection_id}/add-to-radarr` adds all missing collection movies to Radarr in one click.
- `useCollectionMissing` and `useAddCollectionToRadarr` React Query hooks for the new saga actions.

### Changed

- TMDB `get_collection_details` now returns each part with `tmdb_id`, `title`, `year` and `poster_url`.
- `IncompleteCollection` schema now exposes `collection_id` and `missing_count`.

## [1.1.2] - 2026-06-15

### Fixed

- Anime genre filtering now works by mapping AniList genres to TMDB genre IDs during external classics refresh.

## [1.1.1] - 2026-06-15

### Added

- **Anime** category in Discover, separate from TV Shows and Animation.

### Fixed

- Discover filters now initialize from URL query parameters (`category`, `genre`, `year_min`, etc.).
- TV Shows genre filter now works correctly when accessed via direct link or refreshed page.

## [1.1.0] - 2026-06-15

### Added

- **Discover genre filtering** now relies on persisted `genre_ids` in `ExternalClassics`.
- **Queue pagination** for Radarr/Sonarr connectors handles paginated `/api/v3/queue` responses.
- **Queue metadata** enrichment: Radarr `includeMovie=true`, Sonarr `includeSeries=true&includeEpisode=true`.
- **Queue pruning**: imported Radarr movies (`hasFile=true`) are automatically removed from the local queue tracking.

### Changed

- All `*.png` files are now ignored by Git; screenshot removed from README.

### Fixed

- Discover genre filter returned no results because `genre_ids` was missing from `ExternalClassics`.
- Radarr/Sonarr queue could miss items beyond the default API page size.
- Sonarr queue items showed "Unknown" titles and no posters due to missing `series`/`episode` includes.
- Imported Radarr movies added via MLI remained visible in the Queue page as "added".

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
