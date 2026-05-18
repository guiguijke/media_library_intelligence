import asyncio
import logging
from datetime import datetime

from celery import shared_task
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import settings
from app.models import (
    PlexLibrary,
    PlexLibraryMapping,
    TautulliStats,
    ExternalClassics,
    CategoryEnum,
)
from app.services.tasks import create_task_status, update_task_status
from app.connectors.plex import PlexConnector
from app.connectors.tautulli import TautulliConnector
from app.connectors.tmdb import TMDBConnector
from app.connectors.anilist import AniListConnector

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

EXCLUDED_GENRE_IDS = {27}
EXCLUDED_KEYWORDS = {"adult", "erotica", "pornographic", "hentai", "ecchi"}


@shared_task(bind=True, max_retries=3)
def sync_plex_library(self):
    logger.info("Starting Plex library sync")
    self.update_state(state="PROGRESS", meta={"progress": 0, "message": "Fetching Plex libraries..."})

    async def _run():
        await create_task_status(self.request.id, self.name)
        connector = PlexConnector()
        items = await connector.get_library()
        count = len(items)
        self.update_state(state="PROGRESS", meta={"progress": 50, "message": f"Saving {count} items..."})
        await update_task_status(self.request.id, status="running", progress=50, message=f"Saving {count} items...")

        async with AsyncSessionLocal() as db:
            mappings = (await db.execute(select(PlexLibraryMapping))).scalars().all()
            mapping_dict = {m.library_key: m.category for m in mappings}

            # Truncate and refill approach for simplicity
            await db.execute(delete(PlexLibrary))
            for item in items:
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
                    poster_url=None,
                    rating_key=item.get("rating_key"),
                    added_date=datetime.utcnow(),
                )
                db.add(pl)
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
        await create_task_status(self.request.id, self.name)
        connector = TautulliConnector()
        stats = await connector.get_watch_stats()
        count = len(stats)
        self.update_state(state="PROGRESS", meta={"progress": 50, "message": f"Saving {count} stats..."})
        await update_task_status(self.request.id, status="running", progress=50, message=f"Saving {count} stats...")

        async with AsyncSessionLocal() as db:
            await db.execute(delete(TautulliStats))
            for s in stats:
                last_watched_raw = s.get("last_watched")
                last_watched = datetime.fromtimestamp(last_watched_raw) if last_watched_raw else None
                ts = TautulliStats(
                    user_id=s["user_id"],
                    media_id=s["media_id"],
                    watch_count=s["watch_count"],
                    percent_complete=s["percent_complete"],
                    last_watched=last_watched,
                )
                db.add(ts)
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
        await create_task_status(self.request.id, self.name)
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
                        "anilist_id": None,
                        "source_api": "tmdb",
                        "source_list": "top_rated_movies",
                        "score_external": m.get("vote_average"),
                        "popularity": m.get("popularity"),
                        "poster_url": m.get("poster_url"),
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
                        "anilist_id": None,
                        "source_api": "tmdb",
                        "source_list": "top_rated_series",
                        "score_external": s.get("vote_average"),
                        "popularity": s.get("popularity"),
                        "poster_url": s.get("poster_url"),
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
                cat = "cartoon"
                if a.get("original_language") == "ja":
                    cat = "anime"
                all_items.append({
                    "title": a["title"],
                    "original_title": a.get("original_title"),
                    "year": a.get("year"),
                    "category": cat,
                    "tmdb_id": a.get("tmdb_id"),
                    "anilist_id": None,
                    "source_api": "tmdb",
                    "source_list": "discover_animation",
                    "score_external": a.get("vote_average"),
                    "popularity": a.get("popularity"),
                    "poster_url": a.get("poster_url"),
                    "is_recommended": True,
                })
            self.update_state(state="PROGRESS", meta={"progress": 75, "message": "Fetched animations"})
            await update_task_status(self.request.id, status="running", progress=75, message="Fetched animations")
        except Exception as exc:
            logger.error(f"TMDB animation discover error: {exc}")

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
                        "anilist_id": a.get("anilist_id"),
                        "source_api": "anilist",
                        "source_list": "top_anime",
                        "score_external": a.get("score_external"),
                        "popularity": a.get("popularity"),
                        "poster_url": a.get("poster_url"),
                        "is_recommended": True,
                    })
                progress = 75 + int((page / 5) * 25)
                self.update_state(state="PROGRESS", meta={"progress": progress, "message": f"Fetched AniList page {page}"})
                await update_task_status(self.request.id, status="running", progress=progress, message=f"Fetched AniList page {page}")
            except Exception as exc:
                logger.error(f"AniList page {page} error: {exc}")

        # Deduplicate by tmdb_id: keep the entry with the best score_external
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

        async with AsyncSessionLocal() as db:
            # Upsert logic: delete old entries from these sources and insert new ones
            for source in ("tmdb", "anilist"):
                await db.execute(
                    delete(ExternalClassics).where(ExternalClassics.source_api == source)
                )
            for item in all_items:
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
                    anilist_id=item.get("anilist_id"),
                    source_api=item["source_api"],
                    source_list=item.get("source_list"),
                    score_external=item.get("score_external"),
                    popularity=item.get("popularity"),
                    poster_url=item.get("poster_url"),
                    last_synced=datetime.utcnow(),
                    is_recommended=item.get("is_recommended", False),
                )
                db.add(ec)
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
