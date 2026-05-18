import logging
import re
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import PlexLibrary, TautulliStats, ExternalClassics, CategoryEnum
from app.schemas import RecommendationItem, RecommendationFilter, RecommendationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

EXCLUDED_GENRE_IDS = {27}  # Horror
EXCLUDED_KEYWORDS = {"adult", "erotica", "pornographic", "hentai", "ecchi"}


def _normalize_title(title: str) -> str:
    """Normalize title for fuzzy comparison: lower-case, remove non-alphanumeric."""
    if not title:
        return ""
    return re.sub(r"[^a-z0-9]", "", title.lower())


def _root_title(title: str) -> str:
    """Return the root part of a title (before :, -, –, —)."""
    if not title:
        return ""
    t = title.lower()
    for sep in [":", " -", " –", " —", "(", "["]:
        if sep in t:
            t = t.split(sep)[0]
    return t.strip()


async def _get_user_top_genres(db: AsyncSession) -> Dict[int, float]:
    """Computes the most-watched genres weighted by completion percentage."""
    result = await db.execute(
        select(PlexLibrary.genre_ids, TautulliStats.percent_complete, TautulliStats.watch_count)
        .join(TautulliStats, PlexLibrary.rating_key == TautulliStats.media_id, isouter=True)
    )
    genre_scores = {}
    for row in result.all():
        genres, pct, count = row
        if not genres:
            continue
        weight = (count or 0) * (pct or 0) / 100.0
        for g in genres:
            if g in EXCLUDED_GENRE_IDS:
                continue
            genre_scores[g] = genre_scores.get(g, 0.0) + weight
    return genre_scores


async def _get_plex_collections(db: AsyncSession) -> Dict[str, List[int]]:
    """Retrieves collections and the items they contain."""
    result = await db.execute(select(PlexLibrary.title, PlexLibrary.id))
    collections = {}
    for title, mid in result.all():
        if not title:
            continue
        key = _normalize_title(title.split(":")[0].split("-")[0])
        if key not in collections:
            collections[key] = []
        collections[key].append(mid)
    return collections


def _compute_relevance_score(
    item: ExternalClassics,
    user_genres: Dict[int, float],
    plex_titles: set,
    collections: Dict[str, List[int]],
) -> float:
    # 1. Watch history fit (40%)
    item_genres = set(getattr(item, 'genre_ids', None) or [])
    if EXCLUDED_GENRE_IDS & item_genres:
        return 0.0

    genre_score = 0.0
    total_user_weight = sum(user_genres.values()) or 1.0
    for g in item_genres:
        genre_score += user_genres.get(g, 0.0)
    history_score = (genre_score / total_user_weight) * 100

    # 2. Recognized classic status (30%)
    classic_score = 30.0 if item.is_recommended else 0.0

    # 3. Saga completion (20%)
    saga_score = 0.0
    item_title = (item.title or "").split(":")[0].split("-")[0].strip().lower()
    if item_title in collections and len(collections[item_title]) > 0:
        saga_score = 20.0

    # 4. General popularity (10%)
    pop = item.popularity or 0
    pop_score = min(10.0, pop / 100.0)

    total = history_score * 0.40 + classic_score * 0.30 + saga_score * 0.20 + pop_score * 0.10
    return round(total, 2)


@router.post("", response_model=RecommendationResponse)
async def get_recommendations_post(
    filters: RecommendationFilter,
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    return await _get_recommendations_logic(filters, db)


@router.get("", response_model=RecommendationResponse)
async def get_recommendations_get(
    category: str = "all",
    genre: str = None,
    year_min: int = None,
    year_max: int = None,
    rating_min: float = None,
    hide_in_plex: bool = False,
    hide_monitored: bool = False,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    categories = None if category in ("all", None) else category.split(",")
    genres = [int(g) for g in genre.split(",")] if genre else None
    filters = RecommendationFilter(
        categories=categories,
        genres=genres,
        min_year=year_min,
        max_year=year_max,
        limit=limit,
    )
    return await _get_recommendations_logic(filters, db)


async def _get_recommendations_logic(
    filters: RecommendationFilter,
    db: AsyncSession,
) -> RecommendationResponse:
    user_genres = await _get_user_top_genres(db)
    collections = await _get_plex_collections(db)

    plex_result = await db.execute(select(PlexLibrary.title, PlexLibrary.tmdb_id, PlexLibrary.tvdb_id, PlexLibrary.anilist_id))
    plex_titles = set()
    plex_root_titles = set()
    plex_tmdb_ids = set()
    plex_tvdb_ids = set()
    plex_anilist_ids = set()
    for title, tmdb_id, tvdb_id, anilist_id in plex_result.all():
        if title:
            plex_titles.add(_normalize_title(title))
            plex_root_titles.add(_root_title(title))
        if tmdb_id:
            plex_tmdb_ids.add(tmdb_id)
        if tvdb_id:
            plex_tvdb_ids.add(tvdb_id)
        if anilist_id:
            plex_anilist_ids.add(anilist_id)

    query = select(ExternalClassics)
    if filters.categories:
        query = query.where(ExternalClassics.category.in_(filters.categories))
    if filters.min_year:
        query = query.where(ExternalClassics.year >= filters.min_year)
    if filters.max_year:
        query = query.where(ExternalClassics.year <= filters.max_year)

    result = await db.execute(query)
    candidates = result.scalars().all()

    recommendations = []
    for item in candidates:
        if item.tmdb_id and item.tmdb_id in plex_tmdb_ids:
            continue
        if item.tvdb_id and item.tvdb_id in plex_tvdb_ids:
            continue
        if item.anilist_id and item.anilist_id in plex_anilist_ids:
            continue
        if item.title and _normalize_title(item.title) in plex_titles:
            continue
        if item.title and _root_title(item.title) in plex_root_titles:
            continue

        item_genres = set(getattr(item, 'genre_ids', None) or [])
        if EXCLUDED_GENRE_IDS & item_genres:
            continue
        if filters.genres and not item_genres.intersection(set(filters.genres)):
            continue

        if any(k in (item.title or "").lower() for k in EXCLUDED_KEYWORDS):
            continue
        if any(k in (item.original_title or "").lower() for k in EXCLUDED_KEYWORDS):
            continue

        score = _compute_relevance_score(item, user_genres, plex_titles, collections)
        if score <= 0:
            continue

        reasons = []
        if score >= 35:
            reasons.append("Watch history")
        if item.is_recommended:
            reasons.append("Recognized classic")
        if score >= 15 and any(_normalize_title(item.title or "").startswith(c) for c in collections):
            reasons.append("Completes a saga")

        item_id = f"tmdb-{item.tmdb_id}" if item.tmdb_id else (f"anilist-{item.anilist_id}" if item.anilist_id else f"title-{hash(item.title)}")
        recommendations.append(
            RecommendationItem(
                id=item_id,
                title=item.title,
                original_title=item.original_title,
                year=item.year,
                category=item.category.value,
                tmdb_id=item.tmdb_id,
                anilist_id=item.anilist_id,
                poster_url=item.poster_url,
                score=score,
                reason=", ".join(reasons) if reasons else "Popular",
                score_reason=", ".join(reasons) if reasons else "Popular",
                vote_average=item.score_external,
                vote_count=None,
                genres=None,
            )
        )

    recommendations.sort(key=lambda x: x.score, reverse=True)
    return {"items": recommendations[: filters.limit], "total": len(recommendations)}
