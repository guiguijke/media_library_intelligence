from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SonarrQueue, RadarrQueue, Wishlist
from app.schemas import SonarrQueueOut, RadarrQueueOut, WishlistOut

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("/sonarr", response_model=List[SonarrQueueOut])
async def list_sonarr_queue(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SonarrQueue).order_by(SonarrQueue.added_at.desc()))
    return result.scalars().all()


@router.get("/radarr", response_model=List[RadarrQueueOut])
async def list_radarr_queue(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RadarrQueue).order_by(RadarrQueue.added_at.desc()))
    return result.scalars().all()


@router.get("/wishlist", response_model=List[WishlistOut])
async def list_wishlist(db: AsyncSession = Depends(get_db)):
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
