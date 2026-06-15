import logging
from typing import Any, Dict, List, Optional

import httpx
from app.connectors import ConnectorException
from app.services.settings import get_setting

logger = logging.getLogger(__name__)


class RadarrConnector:
    def __init__(self):
        self.base_url = ""
        self.api_key = ""
        self.headers = {}
        self.timeout = 30.0

    async def _init(self):
        self.base_url = (await get_setting("RADARR_BASE_URL")).rstrip("/")
        self.api_key = await get_setting("RADARR_API_KEY")
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
        except httpx.HTTPStatusError as exc:
            logger.error(f"Radarr API HTTP error ({url}): {exc.response.status_code} - {exc.response.text}")
            raise ConnectorException(f"Radarr API error: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error(f"Radarr API request error ({url}): {exc}")
            raise ConnectorException(f"Radarr API request failed: {exc}") from exc

    async def get_movies(self) -> List[Dict[str, Any]]:
        data = await self._request("GET", "/movie")
        if not isinstance(data, list):
            return []
        return data

    async def _get_root_folder(self) -> str:
        folders = await self._request("GET", "/rootfolder")
        if isinstance(folders, list) and folders:
            return folders[0].get("path", "/movies")
        return "/movies"

    async def _get_first_quality_profile(self) -> int:
        profiles = await self._request("GET", "/qualityprofile")
        if isinstance(profiles, list) and profiles:
            return profiles[0].get("id", 1)
        return 1

    async def add_movie(self, title: str, tmdb_id: int, quality_profile: Optional[int] = None, root_folder: Optional[str] = None) -> Optional[Dict[str, Any]]:
        search = await self._request("GET", "/movie/lookup", params={"term": f"tmdb:{tmdb_id}"})
        if not isinstance(search, list) or not search:
            search = await self._request("GET", "/movie/lookup", params={"term": title})
        if not isinstance(search, list) or not search:
            logger.warning(f"Radarr: movie not found for {title} (tmdb:{tmdb_id})")
            return None

        candidate = search[0]
        # Radarr expects the full lookup object with overrides
        candidate.pop("id", None)
        candidate.pop("ratings", None)
        candidate["qualityProfileId"] = quality_profile or await self._get_first_quality_profile()
        candidate["rootFolderPath"] = root_folder or await self._get_root_folder()
        candidate["monitored"] = True
        candidate["addOptions"] = {"searchForMovie": True}
        result = await self._request("POST", "/movie", json_data=candidate)
        if not result or not result.get("id"):
            logger.warning(f"Radarr: failed to add movie {title}, response: {result}")
            return None
        return result

    async def get_queue_status(self) -> List[Dict[str, Any]]:
        await self._init()
        if not self.base_url:
            return []
        all_records: List[Dict[str, Any]] = []
        page = 1
        page_size = 1000
        while True:
            data = await self._request(
                "GET", "/queue", params={"page": page, "pageSize": page_size, "includeMovie": "true"}
            )
            if not data or "records" not in data:
                break
            records = data["records"]
            if not records:
                break
            all_records.extend(records)
            if len(records) < page_size:
                break
            page += 1
        return all_records

    async def test_connection(self) -> bool:
        try:
            data = await self._request("GET", "/system/status")
            return bool(data and "version" in data)
        except Exception:
            return False
