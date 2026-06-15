from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    PlexLibrary,
    TautulliStats,
    TMDBCollection,
)
from app.schemas import DashboardStats, IncompleteCollection, TrendItem

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

    idx = 1
    for cid, data in sorted(collection_groups.items(), key=lambda x: len(x[1]["items"]), reverse=True):
        owned = len(data["items"])
        if owned < 2:
            continue
        total, known_name = collection_totals.get(cid, (None, None))
        if total is None:
            total = owned + 1
        name = known_name or data["name"]
        incomplete_collections.append(
            IncompleteCollection(
                id=idx,
                name=name,
                owned=owned,
                total=total,
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
        incomplete_collections.append(
            IncompleteCollection(
                id=idx,
                name=prefix,
                owned=len(titles),
                total=len(titles) + 1,
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
