import logging
from typing import Any, Dict, List, Optional

import httpx
from app.services.settings import get_setting

logger = logging.getLogger(__name__)


class SonarrConnector:
    def __init__(self):
        self.base_url = ""
        self.api_key = ""
        self.headers = {}
        self.timeout = 30.0

    async def _init(self):
        self.base_url = (await get_setting("SONARR_BASE_URL")).rstrip("/")
        self.api_key = await get_setting("SONARR_API_KEY")
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, endpoint: str, json_data: Optional[dict] = None, params: Optional[dict] = None) -> Optional[Any]:
        await self._init()
        url = f"{self.base_url}/api/v3{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, headers=self.headers, json=json_data, params=params)
                response.raise_for_status()
                if response.status_code == 204:
                    return None
                return response.json()
        except Exception as exc:
            logger.error(f"Sonarr API error ({url}): {exc}")
            return None

    async def get_series(self) -> List[Dict[str, Any]]:
        data = await self._request("GET", "/series")
        if not isinstance(data, list):
            return []
        return data

    async def _get_root_folder(self) -> str:
        folders = await self._request("GET", "/rootfolder")
        if isinstance(folders, list) and folders:
            return folders[0].get("path", "/tv")
        return "/tv"

    async def add_series(self, title: str, tmdb_id: Optional[int] = None, tvdb_id: Optional[int] = None, quality_profile: Optional[int] = None, root_folder: Optional[str] = None) -> Optional[Dict[str, Any]]:
        # Search for the series first
        search = await self._request("GET", "/series/lookup", params={"term": f"tmdb:{tmdb_id}" if tmdb_id else title})
        if not isinstance(search, list) or not search:
            search = await self._request("GET", "/series/lookup", params={"term": title})
        if not isinstance(search, list) or not search:
            logger.warning(f"Sonarr: series not found for {title}")
            return None

        candidate = search[0]
        # Sonarr expects the full lookup object with overrides
        candidate.pop("id", None)
        candidate.pop("ratings", None)
        candidate["qualityProfileId"] = quality_profile or 1
        candidate["rootFolderPath"] = root_folder or await self._get_root_folder()
        candidate["monitored"] = True
        candidate["addOptions"] = {"searchForMissingEpisodes": True}
        result = await self._request("POST", "/series", json_data=candidate)
        return result

    async def get_queue_status(self) -> List[Dict[str, Any]]:
        data = await self._request("GET", "/queue")
        if not data or "records" not in data:
            return []
        return data["records"]

    async def test_connection(self) -> bool:
        try:
            data = await self._request("GET", "/system/status")
            return bool(data and "version" in data)
        except Exception:
            return False
