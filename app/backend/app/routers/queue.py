from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SonarrQueue, RadarrQueue
from app.schemas import QueueItemOut, WishlistOut
from app.connectors.sonarr import SonarrConnector
from app.connectors.radarr import RadarrConnector

router = APIRouter(prefix="/queue", tags=["queue"])


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
        title = f"{title} S{season:02d}E{ep_num}"
        if episode_title:
            title = f"{title} - {episode_title}"
    elif episode_title:
        title = f"{title} - {episode_title}"

    return QueueItemOut(
        id=str(record.get("id", "")),
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


def _radarr_record_to_out(record: dict) -> QueueItemOut:
    movie = record.get("movie") or {}
    size = record.get("size")
    sizeleft = record.get("sizeleft")
    progress = _compute_progress(size, sizeleft)

    return QueueItemOut(
        id=str(record.get("id", "")),
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
    live_items = {str(r.get("id")): _sonarr_record_to_out(r) for r in live_records if r.get("id")}

    # Merge with DB "added" items that aren't in the live queue yet
    result = await db.execute(select(SonarrQueue).order_by(SonarrQueue.added_at.desc()))
    db_items = result.scalars().all()

    for db_item in db_items:
        key = db_item.external_id
        if key not in live_items:
            live_items[key] = QueueItemOut(
                id=key,
                title=db_item.title,
                year=None,
                poster_url=None,
                status=db_item.status or "added",
                progress=0.0,
                added_at=db_item.added_at,
            )

    return list(live_items.values())


@router.get("/radarr", response_model=List[QueueItemOut])
async def list_radarr_queue(db: AsyncSession = Depends(get_db)):
    connector = RadarrConnector()
    live_records = await connector.get_queue_status()
    live_items = {str(r.get("id")): _radarr_record_to_out(r) for r in live_records if r.get("id")}

    # Merge with DB "added" items that aren't in the live queue yet
    result = await db.execute(select(RadarrQueue).order_by(RadarrQueue.added_at.desc()))
    db_items = result.scalars().all()

    for db_item in db_items:
        key = db_item.external_id
        if key not in live_items:
            live_items[key] = QueueItemOut(
                id=key,
                title=db_item.title,
                year=None,
                poster_url=None,
                status=db_item.status or "added",
                progress=0.0,
                added_at=db_item.added_at,
            )

    return list(live_items.values())


@router.get("/wishlist", response_model=List[WishlistOut])
async def list_wishlist(db: AsyncSession = Depends(get_db)):
    from app.models import Wishlist
    result = await db.execute(select(Wishlist).order_by(Wishlist.added_at.desc()))
    return result.scalars().all()


@router.delete("/wishlist/{wishlist_id}")
async def delete_wishlist_item(wishlist_id: int, db: AsyncSession = Depends(get_db)):
    from app.models import Wishlist
    item = await db.get(Wishlist, wishlist_id)
    if not item:
        return {"error": "Not found"}
    await db.delete(item)
    await db.commit()
    return {"deleted": True}
