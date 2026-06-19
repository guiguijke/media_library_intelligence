import asyncio
from datetime import datetime, timedelta
from typing import List

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    PlexLibrary,
    TautulliStats,
    TMDBCollection,
    RadarrQueue,
)
from app.schemas import DashboardStats, IncompleteCollection, TrendItem
from app.connectors.tmdb import TMDBConnector
from app.connectors.radarr import RadarrConnector

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)) -> DashboardStats:
    # Aggregate category counts in a single grouped query
    category_counts = {
        row.category: row.count
        for row in (
            await db.execute(
                select(PlexLibrary.category, func.count(PlexLibrary.id).label("count"))
                .group_by(PlexLibrary.category)
            )
        ).all()
    }
    total_movies = category_counts.get("movie", 0)
    total_series = category_counts.get("series", 0)
    total_anime = category_counts.get("anime", 0)
    total_cartoons = category_counts.get("cartoon", 0)

    # Watch Trends: real data from TautulliStats joined with PlexLibrary
    trends = []
    # Ensure explicit join from PlexLibrary to avoid cross-join issues
    trend_rows = await db.execute(
        select(PlexLibrary.category, func.sum(TautulliStats.watch_count).label("count"))
        .select_from(PlexLibrary)
        .join(TautulliStats, PlexLibrary.rating_key == TautulliStats.media_id)
        .group_by(PlexLibrary.category)
    )
    rows = trend_rows.all()
    if not rows:
        trends = []
    for row in rows:
        if row.count:
            trends.append(
                TrendItem(
                    genre=row.category.value if hasattr(row.category, "value") else str(row.category),
                    count=int(row.count),
                )
            )

    # Incomplete collections: use TMDB collection_id when available, fallback to prefix heuristic
    incomplete_collections: List[IncompleteCollection] = []
    lib_result = await db.execute(select(PlexLibrary))
    items = lib_result.scalars().all()

    # All owned TMDB ids in the library
    owned_tmdb_ids = {item.tmdb_id for item in items if item.tmdb_id}

    # Group by TMDB collection
    collection_groups = {}
    heuristic_items = []
    for item in items:
        if item.collection_id:
            collection_groups.setdefault(item.collection_id, {"name": item.collection_name or "Unknown Collection", "items": []})
            collection_groups[item.collection_id]["items"].append(item)
        else:
            heuristic_items.append(item)

    # Preload TMDB collection totals
    collection_ids = list(collection_groups.keys())
    collection_totals = {}
    if collection_ids:
        coll_result = await db.execute(
            select(TMDBCollection.id, TMDBCollection.total, TMDBCollection.name).where(
                TMDBCollection.id.in_(collection_ids)
            )
        )
        for cid, total, name in coll_result.all():
            collection_totals[cid] = (total, name)

    # Determine which TMDB collections are actually incomplete so we only fetch
    # details and Radarr state for collections that may need action.
    incomplete_collection_ids: List[int] = []
    for cid, data in collection_groups.items():
        owned = len(data["items"])
        if owned < 2:
            continue
        total, _ = collection_totals.get(cid, (None, None))
        if total is None:
            total = owned + 1
        if owned < total:
            incomplete_collection_ids.append(cid)

    # Fetch collection details for incomplete TMDB collections
    tmdb = TMDBConnector()
    collection_details_cache: dict[int, dict] = {}
    if incomplete_collection_ids:
        sem = asyncio.Semaphore(5)

        async def _load_collection(cid: int):
            async with sem:
                details = await tmdb.get_collection_details(cid)
                if details:
                    collection_details_cache[cid] = details

        await asyncio.gather(*[_load_collection(cid) for cid in incomplete_collection_ids])

    # Load current Radarr catalogue once to avoid proposing movies already monitored there
    radarr_tmdb_ids: set[int] = set()
    if incomplete_collection_ids:
        try:
            radarr = RadarrConnector()
            radarr_movies = await radarr.get_movies()
            radarr_tmdb_ids = {m.get("tmdbId") for m in radarr_movies if m.get("tmdbId")}
        except Exception:
            logger.exception("Failed to load Radarr movies for saga completion check")

    idx = 1
    for cid, data in sorted(collection_groups.items(), key=lambda x: len(x[1]["items"]), reverse=True):
        owned = len(data["items"])
        if owned < 2:
            continue
        total, known_name = collection_totals.get(cid, (None, None))
        if total is None:
            total = owned + 1
        if owned >= total:
            continue

        name = known_name or data["name"]
        missing_count = max(0, total - owned)
        actionable_count = missing_count

        if cid:
            details = collection_details_cache.get(cid)
            if details:
                parts = details.get("parts", [])
                missing_tmdb_ids = [
                    p["tmdb_id"]
                    for p in parts
                    if p.get("tmdb_id") and p["tmdb_id"] not in owned_tmdb_ids
                ]
                actionable_missing = [tid for tid in missing_tmdb_ids if tid not in radarr_tmdb_ids]
                total = len(parts) or total
                missing_count = len(missing_tmdb_ids)
                actionable_count = len(actionable_missing)

        # Hide collections whose missing items are already in Radarr, and complete ones
        if actionable_count <= 0:
            continue

        incomplete_collections.append(
            IncompleteCollection(
                id=idx,
                name=name,
                owned=owned,
                total=total,
                collection_id=cid,
                missing_count=missing_count,
                actionable_missing_count=actionable_count,
            )
        )
        idx += 1

    # Fallback heuristic for items without TMDB collection
    raw_groups = {}
    for item in heuristic_items:
        words = item.title.strip().split()[:3]
        key = " ".join(words).lower()
        if not key:
            continue
        raw_groups.setdefault(key, []).append(item.title)

    CONNECTING = {"et", "des", "de", "du", "la", "le", "les", "au", "aux", "en", "un", "une", "a", "the", "of", "in", "on", "at", "to", "for", "with", "and", "or", "but", "from", "by"}

    def _common_prefix(titles):
        if not titles:
            return ""
        word_lists = [t.strip().split() for t in titles]
        min_len = min(len(w) for w in word_lists)
        prefix = []
        for i in range(min_len):
            w0 = word_lists[0][i].lower().rstrip(":;-–—")
            if all(w[i].lower().rstrip(":;-–—") == w0 for w in word_lists):
                prefix.append(word_lists[0][i])
            else:
                break
        while prefix and (prefix[-1].lower().rstrip(":;-–—") in CONNECTING or prefix[-1].lower().rstrip(":;-–—") == ""):
            prefix.pop()
        return " ".join(prefix).rstrip(":;-–— ")

    groups = {}
    for key, titles in raw_groups.items():
        if len(titles) < 2:
            continue
        prefix = _common_prefix(titles)
        if len(prefix.split()) < 2:
            continue
        groups[prefix] = titles

    for prefix, titles in sorted(groups.items(), key=lambda x: len(x[1]), reverse=True):
        owned = len(titles)
        missing = 1
        incomplete_collections.append(
            IncompleteCollection(
                id=idx,
                name=prefix,
                owned=owned,
                total=owned + 1,
                missing_count=missing,
                actionable_missing_count=missing,
            )
        )
        idx += 1

    return DashboardStats(
        movies=total_movies or 0,
        series=total_series or 0,
        anime=total_anime or 0,
        cartoons=total_cartoons or 0,
        incomplete_collections=incomplete_collections,
        trends=trends,
    )


@router.get("/collections/{collection_id}/missing")
async def get_collection_missing(collection_id: int, db: AsyncSession = Depends(get_db)):
    """Return movies from a TMDB collection that are not in the local Plex library."""
    connector = TMDBConnector()
    coll = await connector.get_collection_details(collection_id)
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")

    owned_tmdb_ids = set()
    result = await db.execute(select(PlexLibrary.tmdb_id).where(PlexLibrary.tmdb_id.isnot(None)))
    for (tid,) in result.all():
        owned_tmdb_ids.add(tid)

    missing = [p for p in coll.get("parts", []) if p.get("tmdb_id") and p["tmdb_id"] not in owned_tmdb_ids]
    return {
        "collection_id": collection_id,
        "name": coll.get("name"),
        "missing": missing,
    }


@router.post("/collections/{collection_id}/add-to-radarr")
async def add_collection_missing_to_radarr(collection_id: int, db: AsyncSession = Depends(get_db)):
    """Add all missing movies from a TMDB collection to Radarr."""
    connector = TMDBConnector()
    coll = await connector.get_collection_details(collection_id)
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")

    owned_tmdb_ids = set()
    result = await db.execute(select(PlexLibrary.tmdb_id).where(PlexLibrary.tmdb_id.isnot(None)))
    for (tid,) in result.all():
        owned_tmdb_ids.add(tid)

    missing = [p for p in coll.get("parts", []) if p.get("tmdb_id") and p["tmdb_id"] not in owned_tmdb_ids]
    if not missing:
        return {"added": [], "failed": [], "message": "No missing movies"}

    radarr = RadarrConnector()
    added = []
    failed = []
    for movie in missing:
        tmdb_id = movie["tmdb_id"]
        existing = await db.scalar(
            select(RadarrQueue).where(RadarrQueue.external_id == str(tmdb_id))
        )
        if existing:
            continue
        try:
            res = await radarr.add_movie(title=f"tmdb:{tmdb_id}", tmdb_id=tmdb_id)
            if res:
                db.add(
                    RadarrQueue(
                        external_id=str(tmdb_id),
                        title=res.get("title", movie.get("title", str(tmdb_id))),
                        status="added",
                    )
                )
                added.append(tmdb_id)
            else:
                failed.append(tmdb_id)
        except Exception as exc:
            logger.error(f"Radarr add error for {tmdb_id}: {exc}")
            failed.append(tmdb_id)

    await db.commit()
    return {"added": added, "failed": failed}


@router.get("/recent")
async def get_recent_additions(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PlexLibrary)
        .order_by(PlexLibrary.added_date.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/top-watched")
async def get_top_watched(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TautulliStats)
        .order_by(TautulliStats.watch_count.desc())
        .limit(limit)
    )
    return result.scalars().all()
