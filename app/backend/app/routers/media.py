import hashlib
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import ExternalClassics, CategoryEnum
from app.schemas import MediaDetailOut
from app.connectors.tmdb import TMDBConnector

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/media",
    tags=["media"],
    dependencies=[Depends(get_current_user)],
)


def _parse_media_id(media_id: str) -> tuple[str, Optional[int]]:
    """Parse a stable media id like 'tmdb-123' or 'anilist-456'."""
    if media_id.startswith("tmdb-"):
        return "tmdb", int(media_id.split("-", 1)[1])
    if media_id.startswith("anilist-"):
        return "anilist", int(media_id.split("-", 1)[1])
    return "title", None


def _build_stable_id(item: ExternalClassics) -> str:
    if item.tmdb_id:
        return f"tmdb-{item.tmdb_id}"
    if item.anilist_id:
        return f"anilist-{item.anilist_id}"
    stable_hash = hashlib.md5(f"{item.title}:{item.year}".encode()).hexdigest()
    return f"title-{stable_hash}"


@router.get("/{media_id}", response_model=MediaDetailOut)
async def get_media_detail(
    media_id: str,
    db: AsyncSession = Depends(get_db),
) -> MediaDetailOut:
    kind, external_id = _parse_media_id(media_id)

    item: Optional[ExternalClassics] = None
    if kind == "tmdb" and external_id:
        result = await db.execute(
            select(ExternalClassics).where(ExternalClassics.tmdb_id == external_id)
        )
        item = result.scalar_one_or_none()
    elif kind == "anilist" and external_id:
        result = await db.execute(
            select(ExternalClassics).where(ExternalClassics.anilist_id == external_id)
        )
        item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Media not found")

    detail = MediaDetailOut(
        id=_build_stable_id(item),
        title=item.title,
        original_title=item.original_title,
        year=item.year,
        category=item.category.value,
        tmdb_id=item.tmdb_id,
        tvdb_id=item.tvdb_id,
        anilist_id=item.anilist_id,
        poster_url=item.poster_url,
        vote_average=item.score_external,
        popularity=item.popularity,
    )

    if item.tmdb_id:
        tmdb = TMDBConnector()
        try:
            if item.category in (CategoryEnum.series, CategoryEnum.anime, CategoryEnum.cartoon):
                data = await tmdb.get_tv_details(item.tmdb_id)
                if data:
                    detail.overview = data.get("overview")
                    detail.backdrop_url = data.get("backdrop_url") or data.get("backdrop_path")
                    detail.vote_count = data.get("vote_count")
                    detail.number_of_seasons = data.get("number_of_seasons")
                    detail.number_of_episodes = data.get("number_of_episodes")
            else:
                data = await tmdb.get_movie_details(item.tmdb_id)
                if data:
                    detail.overview = data.get("overview")
                    detail.backdrop_url = data.get("backdrop_url") or data.get("backdrop_path")
                    detail.vote_count = data.get("vote_count")
                    detail.runtime = data.get("runtime")

            # Enrich with appended data
            extra = await tmdb._request(
                f"/{'tv' if item.category in (CategoryEnum.series, CategoryEnum.anime, CategoryEnum.cartoon) else 'movie'}/{item.tmdb_id}",
                params={"append_to_response": "credits,watch/providers,similar,videos,images"},
            )
            if extra:
                detail.genres = [g.get("name") for g in extra.get("genres", [])]
                credits = extra.get("credits", {})
                detail.cast = [
                    {
                        "id": c.get("id"),
                        "name": c.get("name"),
                        "character": c.get("character"),
                        "profile_path": tmdb._build_poster(c.get("profile_path")),
                    }
                    for c in credits.get("cast", [])[:10]
                ]
                detail.crew = [
                    {
                        "id": c.get("id"),
                        "name": c.get("name"),
                        "job": c.get("job"),
                        "department": c.get("department"),
                    }
                    for c in credits.get("crew", [])[:10]
                ]
                videos = extra.get("videos", {}).get("results", [])
                detail.videos = [
                    {
                        "key": v.get("key"),
                        "name": v.get("name"),
                        "site": v.get("site"),
                        "type": v.get("type"),
                    }
                    for v in videos
                ]
                similar = extra.get("similar", {}).get("results", [])
                detail.similar = [
                    {
                        "id": s.get("id"),
                        "title": s.get("title") or s.get("name"),
                        "year": (
                            int(s["release_date"][:4])
                            if s.get("release_date")
                            else int(s["first_air_date"][:4])
                            if s.get("first_air_date")
                            else None
                        ),
                        "poster_url": tmdb._build_poster(s.get("poster_path")),
                    }
                    for s in similar[:10]
                ]
                providers = extra.get("watch/providers", {}).get("results", {})
                country_providers = providers.get("US") or providers.get("FR") or next(iter(providers.values()), {})
                detail.watch_providers = [p.get("provider_name") for p in country_providers.get("flatrate", [])]
                images = extra.get("images", {}).get("backdrops", [])
                detail.images = [tmdb._build_poster(img.get("file_path")) for img in images[:10] if img.get("file_path")]
        except Exception as exc:
            logger.warning(f"Failed to enrich media {media_id}: {exc}")

    return detail
