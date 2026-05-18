from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    PlexLibrary,
    SonarrQueue,
    RadarrQueue,
    Wishlist,
    TautulliStats,
)
from app.schemas import DashboardStats, IncompleteCollection, TrendItem

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)) -> DashboardStats:
    total_movies = await db.scalar(
        select(func.count(PlexLibrary.id)).where(PlexLibrary.category == "movie")
    )
    total_series = await db.scalar(
        select(func.count(PlexLibrary.id)).where(PlexLibrary.category == "series")
    )
    total_anime = await db.scalar(
        select(func.count(PlexLibrary.id)).where(PlexLibrary.category == "anime")
    )
    total_cartoons = await db.scalar(
        select(func.count(PlexLibrary.id)).where(PlexLibrary.category == "cartoon")
    )

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

    # Incomplete collections heuristic: group by common prefix
    incomplete_collections: List[IncompleteCollection] = []
    lib_result = await db.execute(select(PlexLibrary))
    items = lib_result.scalars().all()

    # Step 1: build raw groups by first 3 words
    raw_groups = {}
    for item in items:
        words = item.title.strip().split()[:3]
        key = " ".join(words).lower()
        if not key:
            continue
        raw_groups.setdefault(key, []).append(item.title)

    # Step 2: compute longest common prefix and filter out weak groups
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
        # Strip trailing connecting words and punctuation
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

    idx = 1
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

    # Disk usage: not computed yet
    disk_usage = 0.0  # TODO: compute actual disk usage

    return DashboardStats(
        movies=total_movies or 0,
        series=total_series or 0,
        anime=total_anime or 0,
        cartoons=total_cartoons or 0,
        disk_usage=disk_usage,
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
