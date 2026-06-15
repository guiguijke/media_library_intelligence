from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ConfigDict, create_model

from app.auth import get_current_admin, get_current_user
from app.services.settings import SETTING_KEYS, get_all_settings, update_settings

router = APIRouter(tags=["settings"])

# Build a strict Pydantic schema that only accepts keys defined in SETTING_KEYS.
_settings_fields = {
    key: (str | None, None)
    for key in SETTING_KEYS.keys()
}
SettingsUpdatePayload = create_model(
    "SettingsUpdatePayload",
    __config__=ConfigDict(extra="forbid"),
    **_settings_fields,
)


@router.get("/settings")
async def list_settings(user: dict = Depends(get_current_user)):
    return await get_all_settings(mask_secrets=True)


@router.put("/settings")
async def save_settings(
    payload: SettingsUpdatePayload,
    admin: dict = Depends(get_current_admin),
):
    try:
        await update_settings(payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    return {"status": "saved"}
