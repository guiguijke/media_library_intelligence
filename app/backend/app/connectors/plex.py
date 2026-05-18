import logging
import re
from typing import Any, Dict, List, Optional

import httpx
from app.services.settings import get_setting

logger = logging.getLogger(__name__)


def _extract_guid(guids: List[Dict], prefix: str) -> Optional[int]:
    """Extract numeric ID from Plex Guid list, e.g. tmdb://12345 -> 12345"""
    if not guids:
        return None
    for g in guids:
        gid = g.get("id", "")
        if gid.startswith(f"{prefix}://"):
            try:
                return int(gid.split("://")[1])
            except (ValueError, IndexError):
                return None
    return None


class PlexConnector:
    def __init__(self):
        self.base_url = ""
        self.token = ""
        self.headers = {}
        self.timeout = 30.0

    async def _init(self):
        self.base_url = (await get_setting("PLEX_BASE_URL")).rstrip("/")
        self.token = await get_setting("PLEX_TOKEN")
        self.headers = {
            "X-Plex-Token": self.token,
            "Accept": "application/json",
        }

    async def _request(self, method: str, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        await self._init()
        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.error(f"Plex API error ({url}): {exc}")
            return None

    async def get_library(self) -> List[Dict[str, Any]]:
        """Retrieves Movies and TV Shows sections with metadata."""
        sections = await self._request("GET", "/library/sections")
        if not sections or "MediaContainer" not in sections:
            return []

        results = []
        directories = sections["MediaContainer"].get("Directory", [])
        if isinstance(directories, dict):
            directories = [directories]

        for section in directories:
            section_type = section.get("type")
            section_key = section.get("key")
            if section_type not in ("movie", "show"):
                continue

            items = await self._request("GET", f"/library/sections/{section_key}/all", params={"includeGuids": "1"})
            if not items or "MediaContainer" not in items:
                continue

            media_items = items["MediaContainer"].get("Metadata", [])
            if isinstance(media_items, dict):
                media_items = [media_items]

            for item in media_items:
                genre_list = item.get("Genre", [])
                if isinstance(genre_list, dict):
                    genre_list = [genre_list]
                genres = [g.get("tag") for g in genre_list if g.get("tag")]

                collection_list = item.get("Collection", [])
                if isinstance(collection_list, dict):
                    collection_list = [collection_list]
                collections = [c.get("tag") for c in collection_list if c.get("tag")]

                media_info = item.get("Media", [])
                resolution = None
                if media_info and isinstance(media_info, list):
                    resolution = media_info[0].get("videoResolution")
                elif media_info and isinstance(media_info, dict):
                    resolution = media_info.get("videoResolution")

                category = "series"
                if section_type == "movie":
                    category = "movie"
                elif any("anime" in g.lower() for g in genres) or any("animation" in g.lower() for g in genres):
                    category = "anime"
                elif any("cartoon" in g.lower() for g in genres):
                    category = "cartoon"

                # Extract external GUIDs
                guid_list = item.get("Guid", [])
                if isinstance(guid_list, dict):
                    guid_list = [guid_list]

                results.append({
                    "title": item.get("title"),
                    "original_title": item.get("originalTitle") or item.get("title"),
                    "year": item.get("year"),
                    "category": category,
                    "genres": genres,
                    "resolution": resolution,
                    "collections": collections,
                    "rating_key": item.get("ratingKey"),
                    "section_key": section_key,
                    "section_type": section_type,
                    "tmdb_id": _extract_guid(guid_list, "tmdb"),
                    "tvdb_id": _extract_guid(guid_list, "tvdb"),
                    "imdb_id": _extract_guid(guid_list, "imdb"),
                })

        return results

    async def get_libraries(self) -> List[Dict[str, Any]]:
        sections = await self._request("GET", "/library/sections")
        if not sections or "MediaContainer" not in sections:
            return []
        directories = sections["MediaContainer"].get("Directory", [])
        if isinstance(directories, dict):
            directories = [directories]
        return [
            {"key": s.get("key"), "title": s.get("title"), "type": s.get("type")}
            for s in directories
        ]

    async def test_connection(self) -> bool:
        try:
            data = await self._request("GET", "/")
            return bool(data and "MediaContainer" in data)
        except Exception:
            return False
