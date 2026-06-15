from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import SonarrQueue, RadarrQueue, Wishlist
from app.schemas import QueueItemOut, WishlistOut
from app.connectors.sonarr import SonarrConnector
from app.connectors.radarr import RadarrConnector
from app.connectors import ConnectorException

router = APIRouter(
    prefix="/queue",
    tags=["queue"],
    dependencies=[Depends(get_current_user)],
)


def _extract_poster(images: List[dict]) -> Optional[str]:
    for img in images or []:
        if img.get("coverType") == "poster" or img.get("coverType") == "Poster":
            url = img.get("remoteUrl") or img.get("url")
            if url:
                return url
    return None


def _compute_progress(size: Optional[int], sizeleft: Optional[int]) -> float:
    if not size or size <= 0:
        return 0.0
    left = sizeleft or 0
    done = size - left
    return round((done / size) * 100, 1)


def _map_sonarr_status(record: dict) -> str:
    state = record.get("trackedDownloadState", "").lower()
    status = record.get("status", "").lower()
    if state == "downloading" or status == "downloading":
        return "downloading"
    if state == "importpending" or state == "importing":
        return "importing"
    if state == "failed":
        return "failed"
    if state == "completed" or status == "completed":
        return "completed"
    if status == "queued":
        return "queued"
    return status or "unknown"


def _map_radarr_status(record: dict) -> str:
    state = record.get("trackedDownloadState", "").lower()
    status = record.get("status", "").lower()
    if state == "downloading" or status == "downloading":
        return "downloading"
    if state == "importpending" or state == "importing":
        return "importing"
    if state == "failed":
        return "failed"
    if state == "completed" or status == "completed":
        return "completed"
    if status == "queued":
        return "queued"
    return status or "unknown"


def _extract_sonarr_external_id(series: dict) -> Optional[str]:
    tvdb_id = series.get("tvdbId")
    if tvdb_id is not None:
        return str(tvdb_id)
    tmdb_id = series.get("tmdbId")
    if tmdb_id is not None:
        return str(tmdb_id)
    return None


def _sonarr_record_to_out(record: dict) -> QueueItemOut:
    series = record.get("series") or {}
    episode = record.get("episode") or {}
    size = record.get("size")
    sizeleft = record.get("sizeleft")
    progress = _compute_progress(size, sizeleft)

    title = series.get("title", "Unknown")
    episode_title = episode.get("title")
    season = record.get("seasonNumber")
    ep_num = record.get("episodeNumber")
    if season is not None and ep_num is not None:
        title = f"{title} S{season:02d}E{ep_num:02d}"
        if episode_title:
            title = f"{title} - {episode_title}"
    elif episode_title:
        title = f"{title} - {episode_title}"

    return QueueItemOut(
        id=_extract_sonarr_external_id(series) or str(record.get("id", "")),
        title=title,
        year=series.get("year"),
        poster_url=_extract_poster(series.get("images")),
        status=_map_sonarr_status(record),
        progress=progress,
        size=size,
        sizeleft=sizeleft,
        timeleft=record.get("timeleft"),
        quality=record.get("quality", {}).get("quality", {}).get("name"),
        protocol=record.get("protocol"),
        added_at=None,
    )


def _extract_radarr_external_id(movie: dict) -> Optional[str]:
    tmdb_id = movie.get("tmdbId")
    if tmdb_id is not None:
        return str(tmdb_id)
    return None


def _radarr_record_to_out(record: dict) -> QueueItemOut:
    movie = record.get("movie") or {}
    size = record.get("size")
    sizeleft = record.get("sizeleft")
    progress = _compute_progress(size, sizeleft)

    return QueueItemOut(
        id=_extract_radarr_external_id(movie) or str(record.get("id", "")),
        title=movie.get("title", "Unknown"),
        year=movie.get("year"),
        poster_url=_extract_poster(movie.get("images")),
        status=_map_radarr_status(record),
        progress=progress,
        size=size,
        sizeleft=sizeleft,
        timeleft=record.get("timeleft"),
        quality=record.get("quality", {}).get("quality", {}).get("name"),
        protocol=record.get("protocol"),
        added_at=None,
    )


@router.get("/sonarr", response_model=List[QueueItemOut])
async def list_sonarr_queue(db: AsyncSession = Depends(get_db)):
    connector = SonarrConnector()
    live_records = await connector.get_queue_status()
    live_items: dict[str, QueueItemOut] = {}
    for r in live_records:
        item = _sonarr_record_to_out(r)
        if item.id:
            live_items[item.id] = item

    # Merge with DB "added" items that aren't in the live queue yet
    result = await db.execute(select(SonarrQueue).order_by(SonarrQueue.added_at.desc()))
    db_items = result.scalars().all()

    merged = {**live_items}
    for db_item in db_items:
        key = db_item.external_id
        if key in merged:
            merged[key].added_at = db_item.added_at
        else:
            merged[key] = QueueItemOut(
                id=key,
                title=db_item.title,
                year=None,
                poster_url=None,
                status=db_item.status or "added",
                progress=0.0,
                added_at=db_item.added_at,
            )

    return list(merged.values())


@router.get("/radarr", response_model=List[QueueItemOut])
async def list_radarr_queue(db: AsyncSession = Depends(get_db)):
    connector = RadarrConnector()
    live_records = await connector.get_queue_status()
    live_items: dict[str, QueueItemOut] = {}
    for r in live_records:
        item = _radarr_record_to_out(r)
        if item.id:
            live_items[item.id] = item

    # Merge with DB "added" items that aren't in the live queue yet
    result = await db.execute(select(RadarrQueue).order_by(RadarrQueue.added_at.desc()))
    db_items = result.scalars().all()

    merged = {**live_items}
    for db_item in db_items:
        key = db_item.external_id
        if key in merged:
            merged[key].added_at = db_item.added_at
        else:
            merged[key] = QueueItemOut(
                id=key,
                title=db_item.title,
                year=None,
                poster_url=None,
                status=db_item.status or "added",
                progress=0.0,
                added_at=db_item.added_at,
            )

    return list(merged.values())


@router.get("/wishlist", response_model=List[WishlistOut])
async def list_wishlist(db: AsyncSession = Depends(get_db)):
    from app.models import Wishlist
    result = await db.execute(select(Wishlist).order_by(Wishlist.added_at.desc()))
    return result.scalars().all()


@router.delete("/wishlist/{wishlist_id}")
async def delete_wishlist_item(wishlist_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(Wishlist, wishlist_id)
    if not item:
        return {"error": "Not found"}
    await db.delete(item)
    await db.commit()
    return {"deleted": True}


@router.post("/wishlist/{wishlist_id}/radarr")
async def send_wishlist_to_radarr(
    wishlist_id: int,
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(Wishlist, wishlist_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")

    tmdb_id = item.tmdb_id
    if tmdb_id is None:
        raise HTTPException(status_code=400, detail="No TMDB ID available for this item")

    existing = await db.scalar(
        select(RadarrQueue).where(RadarrQueue.external_id == str(tmdb_id))
    )
    if existing:
        await db.delete(item)
        await db.commit()
        return {"added": False, "reason": "already_in_queue", "deleted": True}

    connector = RadarrConnector()
    try:
        result = await connector.add_movie(
            title=f"tmdb:{tmdb_id}",
            tmdb_id=tmdb_id,
        )
        if not result:
            raise HTTPException(status_code=502, detail="Radarr rejected the movie")

        queue_item = RadarrQueue(
            external_id=str(tmdb_id),
            title=result.get("title", item.title),
            status="added",
        )
        db.add(queue_item)
        await db.delete(item)
        await db.commit()
        return {"added": True, "deleted": True, "title": queue_item.title}
    except ConnectorException as exc:
        raise HTTPException(status_code=502, detail=f"Radarr error: {exc}")


@router.post("/wishlist/{wishlist_id}/sonarr")
async def send_wishlist_to_sonarr(
    wishlist_id: int,
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(Wishlist, wishlist_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")

    tvdb_id = item.tvdb_id
    tmdb_id = item.tmdb_id
    if tvdb_id is None and tmdb_id is None:
        raise HTTPException(status_code=400, detail="No TVDB/TMDB ID available for this item")

    ext_id = str(tvdb_id if tvdb_id is not None else tmdb_id)
    existing = await db.scalar(
        select(SonarrQueue).where(SonarrQueue.external_id == ext_id)
    )
    if existing:
        await db.delete(item)
        await db.commit()
        return {"added": False, "reason": "already_in_queue", "deleted": True}

    connector = SonarrConnector()
    try:
        result = None
        if tvdb_id is not None:
            result = await connector.add_series(
                title=f"tvdb:{tvdb_id}",
                tmdb_id=None,
                tvdb_id=tvdb_id,
            )
        if not result and tmdb_id is not None:
            result = await connector.add_series(
                title=f"tmdb:{tmdb_id}",
                tmdb_id=tmdb_id,
                tvdb_id=None,
            )
        if not result:
            raise HTTPException(status_code=502, detail="Sonarr rejected the series")

        queue_item = SonarrQueue(
            external_id=ext_id,
            title=result.get("title", item.title),
            status="added",
        )
        db.add(queue_item)
        await db.delete(item)
        await db.commit()
        return {"added": True, "deleted": True, "title": queue_item.title}
    except ConnectorException as exc:
        raise HTTPException(status_code=502, detail=f"Sonarr error: {exc}")
