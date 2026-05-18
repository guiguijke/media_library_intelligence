from fastapi import APIRouter

from app.services.settings import get_all_settings, update_settings

router = APIRouter(tags=["settings"])


@router.get("/settings")
async def list_settings():
    return await get_all_settings(mask_secrets=True)


@router.get("/settings/raw")
async def list_settings_raw():
    return await get_all_settings(mask_secrets=False)


@router.put("/settings")
async def save_settings(payload: dict):
    await update_settings(payload)
    return {"status": "saved"}
