from fastapi import APIRouter, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import PlexLibraryMapping, CategoryEnum
from app.schemas import PlexMappingCreate
from app.connectors.plex import PlexConnector

router = APIRouter(
    prefix="/plex",
    tags=["plex"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/libraries")
async def get_plex_libraries():
    connector = PlexConnector()
    libs = await connector.get_libraries()
    return libs


@router.get("/mappings")
async def get_mappings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlexLibraryMapping))
    return result.scalars().all()


@router.post("/mappings")
async def save_mappings(mappings: list[PlexMappingCreate], db: AsyncSession = Depends(get_db)):
    await db.execute(delete(PlexLibraryMapping))
    for m in mappings:
        try:
            cat = CategoryEnum(m.category)
        except ValueError:
            cat = CategoryEnum.ignore
        db.add(PlexLibraryMapping(
            library_key=m.library_key,
            library_name=m.library_name,
            category=cat,
        ))
    await db.commit()
    return {"saved": len(mappings)}
