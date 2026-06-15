import hashlib
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import ExternalClassics, PlexLibrary, CategoryEnum
from app.schemas import SearchResponse, SearchResultItem

router = APIRouter(
    prefix="/search",
    tags=["search"],
    dependencies=[Depends(get_current_user)],
)


def _build_stable_id(item: ExternalClassics) -> str:
    if item.tmdb_id:
        return f"tmdb-{item.tmdb_id}"
    if item.anilist_id:
        return f"anilist-{item.anilist_id}"
    stable_hash = hashlib.md5(f"{item.title}:{item.year}".encode()).hexdigest()
    return f"title-{stable_hash}"


@router.get("", response_model=SearchResponse)
async def search(
    q: str,
    category: Optional[str] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Search discoverable content by title or original title."""
    query = select(ExternalClassics)

    if q:
        pattern = f"%{q}%"
        query = query.where(
            or_(
                ExternalClassics.title.ilike(pattern),
                ExternalClassics.original_title.ilike(pattern),
            )
        )

    if category and category != "all":
        categories = category.split(",")
        query = query.where(ExternalClassics.category.in_(categories))

    if year_min:
        query = query.where(ExternalClassics.year >= year_min)
    if year_max:
        query = query.where(ExternalClassics.year <= year_max)

    # Get total count
    count_query = select(func.count(ExternalClassics.id))
    if query.whereclause is not None:
        count_query = count_query.where(query.whereclause)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginated results
    query = query.order_by(ExternalClassics.popularity.desc().nullslast(), ExternalClassics.title)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    # Build owned set from PlexLibrary
    plex_result = await db.execute(
        select(PlexLibrary.tmdb_id, PlexLibrary.anilist_id)
    )
    plex_rows = plex_result.all()
    owned_tmdb = {row.tmdb_id for row in plex_rows if row.tmdb_id}
    owned_anilist = {row.anilist_id for row in plex_rows if row.anilist_id}

    search_items = []
    for item in items:
        item_id = _build_stable_id(item)
        is_owned = bool(
            (item.tmdb_id and item.tmdb_id in owned_tmdb)
            or (item.anilist_id and item.anilist_id in owned_anilist)
        )
        search_items.append(
            SearchResultItem(
                id=item_id,
                title=item.title,
                original_title=item.original_title,
                year=item.year,
                category=item.category.value,
                tmdb_id=item.tmdb_id,
                anilist_id=item.anilist_id,
                poster_url=item.poster_url,
                vote_average=item.score_external,
                vote_count=None,
                is_owned=is_owned,
            )
        )

    return SearchResponse(
        items=search_items,
        total=total,
        limit=limit,
        offset=offset,
    )
