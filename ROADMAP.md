# MLI Roadmap

## ✅ Done (v1.0)
- [x] Dashboard with stats, trends, saga completion
- [x] Discover page with category filters (Movies, TV Shows, Animation)
- [x] Plex-aware deduplication (TMDb/TVDb/title matching)
- [x] Batch actions (Radarr/Sonarr/Wishlist)
- [x] Activity page (Tautulli sessions, history, user stats)
- [x] Settings UI for all platform credentials
- [x] Celery scheduled sync tasks
- [x] Dynamic root folder lookup for Radarr/Sonarr
- [x] Saga grouping with longest-common-prefix heuristic

## 🔧 Known Issues / Tech Debt
- [ ] **Saga false positives**: `Les Aventures de...` groups unrelated movies (Tintin, Winnie, Rabbi Jacob). Needs TMDB collection-based grouping.
- [ ] **AniList ↔ TMDB dedup**: AniList items lack `tmdb_id`, so duplicates like *Your Name.* appear as both `movie` and `anime`. Needs cross-ID mapping or title-based dedup.
- [ ] **Genre filter**: Frontend sends genre names (e.g. "Action") but backend expects TMDb genre IDs. Filter is currently non-functional.
- [ ] **Hide Monitored**: `hide_monitored` query param exists but is not implemented in recommendations logic.
- [ ] **Disk usage**: Dashboard shows `0 TB`. Needs filesystem scan or API call to Plex for library size.
- [ ] **Task polling**: Frontend polls `/api/tasks` every 2s — should be relaxed to 5s+.

## 🚀 Next Features (priority order)
1. **Wishlist page** (UI exists but is empty / not wired)
2. **Queue page** — show active Sonarr/Radarr downloads with progress
3. **Genre filter fix** — map genre names to IDs, or store genre names in DB
4. **TMDB collection-based sagas** — replace heuristic with real `belongs_to_collection` data
5. **Hide monitored logic** — filter out items already in Sonarr/Radarr queue
6. **Per-user recommendations** — currently recommendations are global; tie them to Plex user watch history
7. **Notifications** — toast when batch add succeeds/fails, not just console errors
8. **Search** — global search bar in Discover for title/year lookup
9. **Dark/light theme toggle**
10. **Mobile responsiveness polish** — some tables overflow on small screens
