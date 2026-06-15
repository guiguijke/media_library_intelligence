import base64
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import select

from app.config import settings as env_settings
from app.database import AsyncSessionLocal
from app.models import AppSetting

logger = logging.getLogger(__name__)

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

# Fixed salt used to derive a Fernet key from SECRET_KEY.
# The security of the encrypted settings therefore relies entirely on the strength of SECRET_KEY.
_FERNET_SALT = b"media-library-intelligence-v1"


def _get_fernet() -> Optional[Fernet]:
    """Return a Fernet instance derived from SECRET_KEY, or None if no key is configured."""
    if not env_settings.SECRET_KEY:
        return None
    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=_FERNET_SALT,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(env_settings.SECRET_KEY.encode("utf-8")))
        return Fernet(key)
    except Exception as exc:
        logger.warning(f"Unable to initialize Fernet encryption: {exc}")
        return None


def _is_fernet_token(value: str) -> bool:
    """Fast heuristic: Fernet tokens produced by this library start with ``gAAAAA``."""
    return value.startswith("gAAAAA")


def _encrypt(value: str) -> str:
    """Encrypt ``value`` with Fernet if a SECRET_KEY is available."""
    f = _get_fernet()
    if not f or not value:
        return value
    try:
        return f.encrypt(value.encode("utf-8")).decode("utf-8")
    except Exception as exc:
        logger.warning(f"Encryption failed: {exc}")
        return value


def _decrypt(value: str) -> str:
    """Decrypt ``value`` with Fernet if it looks like a Fernet token."""
    f = _get_fernet()
    if not f or not value:
        return value
    if not _is_fernet_token(value):
        return value
    try:
        return f.decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return value
    except Exception as exc:
        logger.warning(f"Decryption failed: {exc}")
        return value


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
    """Get a setting value from DB, fallback to env. Secrets are decrypted before return."""
    async with AsyncSessionLocal() as db:
        row = await db.scalar(select(AppSetting).where(AppSetting.key == key))
        if row and row.value is not None:
            value = row.value
            if row.is_secret:
                value = _decrypt(value)
            if value:
                return value
            # If the stored value is empty, use the registered default when available
            default = SETTING_KEYS.get(key, {}).get("default", "")
            if default:
                return default
    # fallback to env
    return getattr(env_settings, key, "")


async def get_all_settings(mask_secrets: bool = True):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AppSetting).order_by(AppSetting.key))
        rows = result.scalars().all()
        items = []
        for row in rows:
            val = row.value or ""
            if row.is_secret:
                if mask_secrets:
                    val = "****"
                else:
                    val = _decrypt(val)
            items.append({
                "key": row.key,
                "value": val,
                "is_secret": row.is_secret,
                "description": row.description,
            })
        return items


async def update_settings(updates: dict):
    """Persist settings updates. Unknown keys are rejected; secrets are encrypted at rest."""
    if not isinstance(updates, dict):
        raise ValueError("Settings payload must be a JSON object")

    unknown_keys = [k for k in updates if k not in SETTING_KEYS]
    if unknown_keys:
        raise ValueError(f"Unknown settings keys: {', '.join(unknown_keys)}")

    async with AsyncSessionLocal() as db:
        for key, val in updates.items():
            row = await db.scalar(select(AppSetting).where(AppSetting.key == key))
            if not row:
                continue

            # Do not overwrite a secret with the masked placeholder sent by the UI
            if row.is_secret and val == "****":
                continue

            str_val = str(val) if val is not None else ""
            if row.is_secret and str_val:
                str_val = _encrypt(str_val)
            row.value = str_val

        await db.commit()
