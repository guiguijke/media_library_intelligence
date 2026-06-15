import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import RadarrQueue, SonarrQueue, Wishlist
from app.schemas import BatchRadarrRequest, BatchSonarrRequest, BatchWishlistRequest, WishlistOut
from app.connectors import ConnectorException
from app.connectors.radarr import RadarrConnector
from app.connectors.sonarr import SonarrConnector

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/batch",
    tags=["batch"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/radarr")
async def batch_add_radarr(
    payload: BatchRadarrRequest,
    db: AsyncSession = Depends(get_db),
):
    connector = RadarrConnector()
    added = []
    failed = []

    for tmdb_id in payload.ids:
        existing = await db.scalar(
            select(RadarrQueue).where(RadarrQueue.external_id == str(tmdb_id))
        )
        if existing:
            continue

        try:
            result = await connector.add_movie(
                title=f"tmdb:{tmdb_id}",
                tmdb_id=tmdb_id,
                quality_profile=payload.quality_profile,
            )
            if result:
                queue_item = RadarrQueue(
                    external_id=str(tmdb_id),
                    title=result.get("title", str(tmdb_id)),
                    status="added",
                )
                db.add(queue_item)
                added.append(tmdb_id)
            else:
                failed.append(tmdb_id)
        except ConnectorException as exc:
            logger.error(f"Radarr batch add error for {tmdb_id}: {exc}")
            failed.append(tmdb_id)

    await db.commit()
    return {"added": added, "failed": failed}


@router.post("/sonarr")
async def batch_add_sonarr(
    payload: BatchSonarrRequest,
    db: AsyncSession = Depends(get_db),
):
    connector = SonarrConnector()
    added = []
    failed = []

    for raw_id in payload.ids:
        ext_id = str(raw_id)
        title = f"tvdb:{raw_id}"

        existing = await db.scalar(
            select(SonarrQueue).where(SonarrQueue.external_id == ext_id)
        )
        if existing:
            continue

        try:
            # Try tvdb_id first, then fallback to tmdb_id
            result = await connector.add_series(
                title=title,
                tmdb_id=None,
                tvdb_id=raw_id,
                quality_profile=payload.quality_profile,
            )
            if not result:
                result = await connector.add_series(
                    title=f"tmdb:{raw_id}",
                    tmdb_id=raw_id,
                    tvdb_id=None,
                    quality_profile=payload.quality_profile,
                )
            if result:
                queue_item = SonarrQueue(
                    external_id=ext_id,
                    title=result.get("title", title),
                    status="added",
                )
                db.add(queue_item)
                added.append(ext_id)
            else:
                failed.append(ext_id)
        except ConnectorException as exc:
            logger.error(f"Sonarr batch add error for {ext_id}: {exc}")
            failed.append(ext_id)

    await db.commit()
    return {"added": added, "failed": failed}


@router.post("/wishlist")
async def batch_add_wishlist(
    payload: BatchWishlistRequest,
    db: AsyncSession = Depends(get_db),
):
    added = []
    for item in payload.items:
        existing = await db.scalar(
            select(Wishlist).where(
                Wishlist.external_id == item.external_id,
                Wishlist.category == item.category,
            )
        )
        if existing:
            continue
        wl = Wishlist(
            external_id=item.external_id,
            category=item.category,
            title=item.title,
            poster_url=item.poster_url,
            tmdb_id=item.tmdb_id,
            tvdb_id=item.tvdb_id,
            anilist_id=item.anilist_id,
            notes=item.notes,
        )
        db.add(wl)
        added.append(item.external_id)

    await db.commit()
    return {"added": added}
