from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import AppSetting
from app.config import settings as env_settings

# Map of setting keys with defaults and whether they are secret
SETTING_KEYS = {
    "PLEX_BASE_URL": {"default": "", "secret": False, "desc": "Plex server URL"},
    "PLEX_TOKEN": {"default": "", "secret": True, "desc": "Plex token"},
    "TAUTULLI_BASE_URL": {"default": "", "secret": False, "desc": "Tautulli URL"},
    "TAUTULLI_API_KEY": {"default": "", "secret": True, "desc": "Tautulli API key"},
    "TMDB_API_KEY": {"default": "", "secret": True, "desc": "TMDB API key"},
    "TMDB_BASE_URL": {"default": "https://api.themoviedb.org/3", "secret": False, "desc": "TMDB API base URL"},
    "TMDB_IMAGE_BASE_URL": {"default": "https://image.tmdb.org/t/p/w500", "secret": False, "desc": "TMDB image base URL"},
    "ANILIST_BASE_URL": {"default": "https://graphql.anilist.co", "secret": False, "desc": "AniList API URL"},
    "SONARR_BASE_URL": {"default": "", "secret": False, "desc": "Sonarr URL"},
    "SONARR_API_KEY": {"default": "", "secret": True, "desc": "Sonarr API key"},
    "RADARR_BASE_URL": {"default": "", "secret": False, "desc": "Radarr URL"},
    "RADARR_API_KEY": {"default": "", "secret": True, "desc": "Radarr API key"},
}


async def init_default_settings():
    """Ensure all setting keys exist in DB with defaults."""
    async with AsyncSessionLocal() as db:
        for key, meta in SETTING_KEYS.items():
            existing = await db.scalar(select(AppSetting).where(AppSetting.key == key))
            if not existing:
                db.add(AppSetting(
                    key=key,
                    value=meta["default"],
                    is_secret=meta["secret"],
                    description=meta["desc"],
                ))
        await db.commit()


async def get_setting(key: str) -> str:
    """Get a setting value from DB, fallback to env."""
    async with AsyncSessionLocal() as db:
        row = await db.scalar(select(AppSetting).where(AppSetting.key == key))
        if row and row.value is not None:
            return row.value
    # fallback to env
    return getattr(env_settings, key, "")


async def get_all_settings(mask_secrets: bool = True):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AppSetting).order_by(AppSetting.key))
        rows = result.scalars().all()
        items = []
        for row in rows:
            val = row.value or ""
            if row.is_secret and mask_secrets and val:
                val = "****"
            items.append({
                "key": row.key,
                "value": val,
                "is_secret": row.is_secret,
                "description": row.description,
            })
        return items


async def update_settings(updates: dict):
    async with AsyncSessionLocal() as db:
        for key, val in updates.items():
            row = await db.scalar(select(AppSetting).where(AppSetting.key == key))
            if row:
                # Only update if value is not the masked placeholder
                if row.is_secret and val == "****":
                    continue
                row.value = val
        await db.commit()
