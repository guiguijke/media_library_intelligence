import asyncio
import logging
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import select, delete

from app.database import AsyncSessionLocal
from app.models import (
    PlexLibrary,
    PlexLibraryMapping,
    TautulliStats,
    ExternalClassics,
    CategoryEnum,
    TMDBCollection,
)
from app.services.tasks import create_task_status, update_task_status
from app.connectors.plex import PlexConnector
from app.connectors.tautulli import TautulliConnector
from app.connectors.tmdb import TMDBConnector
from app.connectors.anilist import AniListConnector

logger = logging.getLogger(__name__)

EXCLUDED_GENRE_IDS = {27}
EXCLUDED_KEYWORDS = {"adult", "erotica", "pornographic", "hentai", "ecchi"}

# AniList genres are free-text strings. Map the common ones to TMDB genre IDs
# so that anime recommendations can be filtered by the same genre pills as movies/series.
ANILIST_GENRE_TO_TMDB = {
    "Action": 28,
    "Adventure": 12,
    "Comedy": 35,
    "Drama": 18,
    "Fantasy": 14,
    "Horror": 27,
    "Mahou Shoujo": 16,
    "Mecha": 878,
    "Music": 10402,
    "Mystery": 9648,
    "Psychological": 53,
    "Romance": 10749,
    "Sci-Fi": 878,
    "Slice of Life": 18,
    "Sports": 18,
    "Supernatural": 14,
    "Thriller": 53,
}


def _map_anilist_genres(anilist_genres):
    """Convert a list of AniList genre strings to TMDB genre IDs."""
    if not anilist_genres:
        return []
    mapped = {ANILIST_GENRE_TO_TMDB.get(g) for g in anilist_genres if g in ANILIST_GENRE_TO_TMDB}
    return sorted(mapped)


@shared_task(bind=True, max_retries=3)
def sync_plex_library(self):
    logger.info("Starting Plex library sync")
    self.update_state(state="PROGRESS", meta={"progress": 0, "message": "Fetching Plex libraries..."})

    async def _run():
        await create_task_status(self.request.id, self.name, status="running", progress=0, message="Fetching Plex libraries...")
        connector = PlexConnector()
        items = await connector.get_library()
        self.update_state(state="PROGRESS", meta={"progress": 5, "message": f"Fetched {len(items)} items from Plex"})
        await update_task_status(self.request.id, status="running", progress=5, message=f"Fetched {len(items)} items from Plex")

        async with AsyncSessionLocal() as db:
            mappings = (await db.execute(select(PlexLibraryMapping))).scalars().all()
            mapping_dict = {m.library_key: m.category for m in mappings}

        # Skip sections mapped to "ignore" before doing any enrichment
        items = [
            item for item in items
            if mapping_dict.get(item.get("section_key")) != "ignore"
        ]
        count = len(items)
        self.update_state(state="PROGRESS", meta={"progress": 6, "message": f"{count} items after filtering ignored sections"})
        await update_task_status(self.request.id, status="running", progress=6, message=f"{count} items after filtering ignored sections")

        # Load existing movie enrichment cache to avoid re-calling TMDB for unchanged items
        async with AsyncSessionLocal() as db:
            existing_movies = (
                await db.execute(select(PlexLibrary).where(PlexLibrary.tmdb_id.isnot(None)))
            ).scalars().all()
            existing_movie_cache = {
                m.tmdb_id: {
                    "collection_id": m.collection_id,
                    "collection_name": m.collection_name,
                }
                for m in existing_movies
            }

        # Enrich movies with TMDB collection info
        tmdb = TMDBConnector()
        sem = asyncio.Semaphore(10)
        movie_items = [item for item in items if item.get("category") == "movie" and item.get("tmdb_id")]
        total_movies = len(movie_items)
        collection_cache: dict[int, dict] = {}

        async def _enrich(item):
            async with sem:
                tmdb_id = item.get("tmdb_id")
                cached = existing_movie_cache.get(tmdb_id)
                if cached and cached.get("collection_id"):
                    item["collection_id"] = cached["collection_id"]
                    item["collection_name"] = cached["collection_name"]
                    return item

                details = await tmdb.get_movie_details(tmdb_id)
            if details:
                collection = details.get("belongs_to_collection")
                if collection:
                    collection_id = collection.get("id")
                    item["collection_id"] = collection_id
                    item["collection_name"] = collection.get("name")
                    if collection_id and collection_id not in collection_cache:
                        coll_details = await tmdb.get_collection_details(collection_id)
                        if coll_details:
                            collection_cache[collection_id] = coll_details
            return item

        if total_movies > 0:
            completed = 0
            lock = asyncio.Lock()

            async def _enrich_with_progress(item):
                nonlocal completed
                await _enrich(item)
                async with lock:
                    completed += 1
                    if completed % max(1, total_movies // 10) == 0 or completed == total_movies:
                        progress = 5 + int((completed / total_movies) * 55)
                        msg = f"Enriching TMDB collections... ({completed}/{total_movies})"
                        self.update_state(state="PROGRESS", meta={"progress": progress, "message": msg})
                        await update_task_status(self.request.id, status="running", progress=progress, message=msg)

            await asyncio.gather(*[_enrich_with_progress(item) for item in movie_items])

        self.update_state(state="PROGRESS", meta={"progress": 60, "message": f"Saving {count} items..."})
        await update_task_status(self.request.id, status="running", progress=60, message=f"Saving {count} items...")

        async with AsyncSessionLocal() as db:
            mappings = (await db.execute(select(PlexLibraryMapping))).scalars().all()
            mapping_dict = {m.library_key: m.category for m in mappings}

            for i, item in enumerate(items):
                section_key = item.get("section_key")
                section_type = item.get("section_type")
                mapped = mapping_dict.get(section_key)
                if mapped:
                    category = mapped.value
                else:
                    category = "movie" if section_type == "movie" else "series"
                try:
                    cat_enum = CategoryEnum(category)
                except ValueError:
                    cat_enum = CategoryEnum.series

                rating_key = item.get("rating_key")
                existing = None
                if rating_key:
                    existing = await db.scalar(
                        select(PlexLibrary).where(PlexLibrary.rating_key == rating_key)
                    )

                if existing:
                    existing.title = item["title"]
                    existing.original_title = item.get("original_title")
                    existing.year = item.get("year")
                    existing.category = cat_enum
                    existing.genre_ids = item.get("genres")
                    existing.collections = item.get("collections")
                    existing.tmdb_id = item.get("tmdb_id")
                    existing.tvdb_id = item.get("tvdb_id")
                    existing.anilist_id = None
                    existing.imdb_id = item.get("imdb_id")
                    existing.collection_id = item.get("collection_id")
                    existing.collection_name = item.get("collection_name")
                    existing.poster_url = None
                    # added_date is intentionally preserved
                else:
                    pl = PlexLibrary(
                        title=item["title"],
                        original_title=item.get("original_title"),
                        year=item.get("year"),
                        category=cat_enum,
                        genre_ids=item.get("genres"),
                        collections=item.get("collections"),
                        tmdb_id=item.get("tmdb_id"),
                        tvdb_id=item.get("tvdb_id"),
                        anilist_id=None,
                        imdb_id=item.get("imdb_id"),
                        collection_id=item.get("collection_id"),
                        collection_name=item.get("collection_name"),
                        poster_url=None,
                        rating_key=rating_key,
                        added_date=datetime.now(timezone.utc),
                    )
                    db.add(pl)

                if i % max(1, count // 10) == 0:
                    progress = 60 + int((i / count) * 35)
                    self.update_state(state="PROGRESS", meta={"progress": progress, "message": f"Saving item {i}/{count}..."})
                    await update_task_status(self.request.id, status="running", progress=progress, message=f"Saving item {i}/{count}...")

            # Upsert discovered TMDB collections
            for coll_id, coll_data in collection_cache.items():
                existing = await db.get(TMDBCollection, coll_id)
                if existing:
                    existing.name = coll_data["name"]
                    existing.total = coll_data["total"]
                    existing.poster_url = coll_data["poster_url"]
                    existing.backdrop_url = coll_data["backdrop_url"]
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    db.add(
                        TMDBCollection(
                            id=coll_id,
                            name=coll_data["name"],
                            total=coll_data["total"],
                            poster_url=coll_data["poster_url"],
                            backdrop_url=coll_data["backdrop_url"],
                            updated_at=datetime.now(timezone.utc),
                        )
                    )

            await db.commit()

        await update_task_status(self.request.id, status="success", progress=100, result={"synced": count})
        return {"synced": count}

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_run())
    except Exception as exc:
        logger.exception("Plex library sync failed")
        try:
            loop.run_until_complete(update_task_status(self.request.id, status="failure", message=str(exc)))
        except Exception:
            pass
        raise
    logger.info(f"Plex library sync completed: {result['synced']} items")
    return result


@shared_task(bind=True, max_retries=3)
def sync_tautulli_stats(self, previous_result=None):
    logger.info("Starting Tautulli stats sync")
    self.update_state(state="PROGRESS", meta={"progress": 0, "message": "Fetching Tautulli stats..."})

    async def _run():
        await create_task_status(self.request.id, self.name, status="running", progress=0, message="Fetching Tautulli stats...")
        connector = TautulliConnector()
        stats = await connector.get_watch_stats()
        count = len(stats)
        self.update_state(state="PROGRESS", meta={"progress": 10, "message": f"Fetched {count} stats from Tautulli"})
        await update_task_status(self.request.id, status="running", progress=10, message=f"Fetched {count} stats from Tautulli")

        async with AsyncSessionLocal() as db:
            for i, s in enumerate(stats):
                user_id = s["user_id"]
                media_id = s["media_id"]
                last_watched_raw = s.get("last_watched")
                last_watched = datetime.fromtimestamp(last_watched_raw, tz=timezone.utc) if last_watched_raw else None

                existing = await db.scalar(
                    select(TautulliStats).where(
                        TautulliStats.user_id == user_id,
                        TautulliStats.media_id == media_id,
                    )
                )

                if existing:
                    existing.watch_count = s["watch_count"]
                    existing.percent_complete = s["percent_complete"]
                    existing.last_watched = last_watched
                else:
                    ts = TautulliStats(
                        user_id=user_id,
                        media_id=media_id,
                        watch_count=s["watch_count"],
                        percent_complete=s["percent_complete"],
                        last_watched=last_watched,
                    )
                    db.add(ts)

                if i % max(1, count // 10) == 0:
                    progress = 10 + int((i / count) * 85)
                    self.update_state(state="PROGRESS", meta={"progress": progress, "message": f"Saving stat {i}/{count}..."})
                    await update_task_status(self.request.id, status="running", progress=progress, message=f"Saving stat {i}/{count}...")
            await db.commit()

        await update_task_status(self.request.id, status="success", progress=100, result={"synced": count})
        return {"synced": count}

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_run())
    except Exception as exc:
        logger.exception("Tautulli stats sync failed")
        try:
            loop.run_until_complete(update_task_status(self.request.id, status="failure", message=str(exc)))
        except Exception:
            pass
        raise
    logger.info(f"Tautulli stats sync completed: {result['synced']} records")
    return result


@shared_task(bind=True, max_retries=3)
def refresh_external_classics(self, previous_result=None):
    logger.info("Starting external classics refresh")
    self.update_state(state="PROGRESS", meta={"progress": 0, "message": "Fetching external classics..."})

    async def _run():
        await create_task_status(self.request.id, self.name, status="running", progress=0, message="Fetching external classics...")
        tmdb = TMDBConnector()
        anilist = AniListConnector()

        all_items = []

        # Movies pages 1-20
        for page in range(1, 21):
            try:
                movies = await tmdb.get_top_rated_movies(page=page)
                for m in movies:
                    if any(g in EXCLUDED_GENRE_IDS for g in (m.get("genre_ids") or [])):
                        continue
                    all_items.append({
                        "title": m["title"],
                        "original_title": m.get("original_title"),
                        "year": m.get("year"),
                        "category": "movie",
                        "tmdb_id": m.get("tmdb_id"),
                        "tvdb_id": None,
                        "anilist_id": None,
                        "source_api": "tmdb",
                        "source_list": "top_rated_movies",
                        "score_external": m.get("vote_average"),
                        "popularity": m.get("popularity"),
                        "poster_url": m.get("poster_url"),
                        "genre_ids": m.get("genre_ids", []),
                        "is_recommended": True,
                    })
                progress = int((page / 20) * 40)
                self.update_state(state="PROGRESS", meta={"progress": progress, "message": f"Fetched movies page {page}"})
                await update_task_status(self.request.id, status="running", progress=progress, message=f"Fetched movies page {page}")
            except Exception as exc:
                logger.error(f"TMDB movies page {page} error: {exc}")

        # Series pages 1-10
        for page in range(1, 11):
            try:
                series = await tmdb.get_top_rated_series(page=page)
                for s in series:
                    if any(g in EXCLUDED_GENRE_IDS for g in (s.get("genre_ids") or [])):
                        continue
                    all_items.append({
                        "title": s["title"],
                        "original_title": s.get("original_title"),
                        "year": s.get("year"),
                        "category": "series",
                        "tmdb_id": s.get("tmdb_id"),
                        "tvdb_id": None,
                        "anilist_id": None,
                        "source_api": "tmdb",
                        "source_list": "top_rated_series",
                        "score_external": s.get("vote_average"),
                        "popularity": s.get("popularity"),
                        "poster_url": s.get("poster_url"),
                        "genre_ids": s.get("genre_ids", []),
                        "is_recommended": True,
                    })
                progress = 40 + int((page / 10) * 30)
                self.update_state(state="PROGRESS", meta={"progress": progress, "message": f"Fetched series page {page}"})
                await update_task_status(self.request.id, status="running", progress=progress, message=f"Fetched series page {page}")
            except Exception as exc:
                logger.error(f"TMDB series page {page} error: {exc}")

        # Animation discover
        try:
            animations = await tmdb.discover_animation()
            for a in animations:
                if any(g in EXCLUDED_GENRE_IDS for g in (a.get("genre_ids") or [])):
                    continue
                cat = "anime" if a.get("original_language") == "ja" else "cartoon"
                all_items.append({
                    "title": a["title"],
                    "original_title": a.get("original_title"),
                    "year": a.get("year"),
                    "category": cat,
                    "tmdb_id": a.get("tmdb_id"),
                    "tvdb_id": None,
                    "anilist_id": None,
                    "source_api": "tmdb",
                    "source_list": "discover_animation",
                    "score_external": a.get("vote_average"),
                    "popularity": a.get("popularity"),
                    "poster_url": a.get("poster_url"),
                    "genre_ids": a.get("genre_ids", []),
                    "is_recommended": True,
                })
            self.update_state(state="PROGRESS", meta={"progress": 75, "message": "Fetched animations"})
            await update_task_status(self.request.id, status="running", progress=75, message="Fetched animations")
        except Exception as exc:
            logger.error(f"TMDB animation discover error: {exc}")

        # Enrich series with TVDb IDs when available
        series_items = [item for item in all_items if item["category"] == "series" and item.get("tmdb_id")]
        if series_items:
            sem = asyncio.Semaphore(10)
            completed = 0
            lock = asyncio.Lock()
            total_series = len(series_items)

            async def _enrich_tvdb(item):
                nonlocal completed
                async with sem:
                    details = await tmdb.get_tv_details(item["tmdb_id"])
                if details:
                    item["tvdb_id"] = details.get("tvdb_id") or item.get("tvdb_id")
                async with lock:
                    completed += 1
                    if completed % max(1, total_series // 5) == 0 or completed == total_series:
                        msg = f"Enriching TVDb IDs... ({completed}/{total_series})"
                        self.update_state(state="PROGRESS", meta={"progress": 76, "message": msg})
                        await update_task_status(self.request.id, status="running", progress=76, message=msg)

            await asyncio.gather(*[_enrich_tvdb(item) for item in series_items])

        # AniList top anime
        for page in range(1, 6):
            try:
                anime_list = await anilist.get_top_anime(page=page, per_page=50)
                for a in anime_list:
                    all_items.append({
                        "title": a["title"],
                        "original_title": a.get("original_title"),
                        "year": a.get("year"),
                        "category": "anime",
                        "tmdb_id": None,
                        "tvdb_id": None,
                        "anilist_id": a.get("anilist_id"),
                        "source_api": "anilist",
                        "source_list": "top_anime",
                        "score_external": a.get("score_external"),
                        "popularity": a.get("popularity"),
                        "poster_url": a.get("poster_url"),
                        "genre_ids": _map_anilist_genres(a.get("genre_ids")),
                        "is_recommended": True,
                    })
                progress = 75 + int((page / 5) * 25)
                self.update_state(state="PROGRESS", meta={"progress": progress, "message": f"Fetched AniList page {page}"})
                await update_task_status(self.request.id, status="running", progress=progress, message=f"Fetched AniList page {page}")
            except Exception as exc:
                logger.error(f"AniList page {page} error: {exc}")

        # Deduplicate by tmdb_id: keep the entry with the best score_external
        self.update_state(state="PROGRESS", meta={"progress": 77, "message": "Deduplicating by TMDB ID..."})
        await update_task_status(self.request.id, status="running", progress=77, message="Deduplicating by TMDB ID...")

        seen_tmdb = {}
        deduped_items = []
        for item in all_items:
            tid = item.get("tmdb_id")
            if tid:
                if tid in seen_tmdb:
                    existing = seen_tmdb[tid]
                    if (item.get("score_external") or 0) > (existing.get("score_external") or 0):
                        seen_tmdb[tid] = item
                else:
                    seen_tmdb[tid] = item
            else:
                deduped_items.append(item)
        deduped_items.extend(seen_tmdb.values())
        all_items = deduped_items

        # Second pass: deduplicate by normalized title (AniList vs TMDB without tmdb_id)
        self.update_state(state="PROGRESS", meta={"progress": 78, "message": "Deduplicating by title..."})
        await update_task_status(self.request.id, status="running", progress=78, message="Deduplicating by title...")

        def _norm(title):
            if not title:
                return ""
            return "".join(c for c in title.lower() if c.isalnum())

        seen_title = {}
        final_items = []
        for item in all_items:
            key = _norm(item.get("title"))
            if not key:
                final_items.append(item)
                continue
            if key in seen_title:
                existing = seen_title[key]
                if (item.get("score_external") or 0) > (existing.get("score_external") or 0):
                    seen_title[key] = item
            else:
                seen_title[key] = item
        final_items.extend(seen_title.values())
        all_items = final_items

        self.update_state(state="PROGRESS", meta={"progress": 80, "message": f"Saving {len(all_items)} items to database..."})
        await update_task_status(self.request.id, status="running", progress=80, message=f"Saving {len(all_items)} items to database...")

        async with AsyncSessionLocal() as db:
            # Atomic transaction: delete old entries from handled sources, then insert new ones
            for source in ("tmdb", "anilist"):
                await db.execute(
                    delete(ExternalClassics).where(ExternalClassics.source_api == source)
                )
            total = len(all_items)
            for i, item in enumerate(all_items):
                try:
                    cat_enum = CategoryEnum(item["category"])
                except ValueError:
                    cat_enum = CategoryEnum.movie
                ec = ExternalClassics(
                    title=item["title"],
                    original_title=item.get("original_title"),
                    year=item.get("year"),
                    category=cat_enum,
                    tmdb_id=item.get("tmdb_id"),
                    tvdb_id=item.get("tvdb_id"),
                    anilist_id=item.get("anilist_id"),
                    source_api=item["source_api"],
                    source_list=item.get("source_list"),
                    score_external=item.get("score_external"),
                    popularity=item.get("popularity"),
                    poster_url=item.get("poster_url"),
                    genre_ids=item.get("genre_ids"),
                    last_synced=datetime.now(timezone.utc),
                    is_recommended=item.get("is_recommended", False),
                )
                db.add(ec)
                if i % max(1, total // 10) == 0:
                    progress = 80 + int((i / total) * 18)
                    self.update_state(state="PROGRESS", meta={"progress": progress, "message": f"Saving item {i}/{total}..."})
                    await update_task_status(self.request.id, status="running", progress=progress, message=f"Saving item {i}/{total}...")
            await db.commit()

        await update_task_status(self.request.id, status="success", progress=100, result={"synced": len(all_items)})
        return len(all_items)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        count = loop.run_until_complete(_run())
    except Exception as exc:
        logger.exception("External classics refresh failed")
        try:
            loop.run_until_complete(update_task_status(self.request.id, status="failure", message=str(exc)))
        except Exception:
            pass
        raise
    logger.info(f"External classics refresh completed: {count} items")
    return {"synced": count}
