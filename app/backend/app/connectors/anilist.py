import logging
from typing import Any, Dict, List, Optional

import httpx
from app.services.settings import get_setting

logger = logging.getLogger(__name__)


class AniListConnector:
    def __init__(self):
        self.base_url = ""
        self.timeout = 30.0

    async def _init(self):
        self.base_url = await get_setting("ANILIST_BASE_URL")

    async def _graphql(self, query: str, variables: Optional[dict] = None) -> Optional[dict]:
        await self._init()
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.base_url, json=payload)
                response.raise_for_status()
                data = response.json()
                if "errors" in data:
                    logger.warning(f"AniList GraphQL errors: {data['errors']}")
                    return None
                return data.get("data")
        except Exception as exc:
            logger.error(f"AniList API error: {exc}")
            return None

    async def get_top_anime(self, page: int = 1, per_page: int = 50) -> List[Dict[str, Any]]:
        query = """
        query ($page: Int, $perPage: Int) {
          Page(page: $page, perPage: $perPage) {
            media(type: ANIME, sort: SCORE_DESC) {
              id
              title {
                romaji
                english
                native
              }
              startDate {
                year
              }
              genres
              averageScore
              popularity
              coverImage {
                large
              }
              format
              isAdult
            }
          }
        }
        """
        data = await self._graphql(query, {"page": page, "perPage": per_page})
        if not data or "Page" not in data:
            return []

        results = []
        for item in data["Page"]["media"]:
            if item.get("isAdult"):
                continue
            genres = item.get("genres", [])
            if "Hentai" in genres or "Ecchi" in genres:
                continue

            title = item["title"].get("english") or item["title"].get("romaji") or item["title"].get("native")
            results.append({
                "anilist_id": item.get("id"),
                "title": title,
                "original_title": item["title"].get("romaji") or title,
                "year": item.get("startDate", {}).get("year"),
                "genre_ids": genres,
                "score_external": item.get("averageScore"),
                "popularity": item.get("popularity"),
                "poster_url": item.get("coverImage", {}).get("large"),
                "format": item.get("format"),
            })
        return results

    async def search_anime(self, title: str) -> List[Dict[str, Any]]:
        query = """
        query ($search: String) {
          Page(page: 1, perPage: 10) {
            media(type: ANIME, search: $search, sort: POPULARITY_DESC) {
              id
              title {
                romaji
                english
                native
              }
              startDate {
                year
              }
              genres
              averageScore
              popularity
              coverImage {
                large
              }
              format
              isAdult
            }
          }
        }
        """
        data = await self._graphql(query, {"search": title})
        if not data or "Page" not in data:
            return []

        results = []
        for item in data["Page"]["media"]:
            if item.get("isAdult"):
                continue
            genres = item.get("genres", [])
            if "Hentai" in genres or "Ecchi" in genres:
                continue

            t = item["title"].get("english") or item["title"].get("romaji") or item["title"].get("native")
            results.append({
                "anilist_id": item.get("id"),
                "title": t,
                "original_title": item["title"].get("romaji") or t,
                "year": item.get("startDate", {}).get("year"),
                "genre_ids": genres,
                "score_external": item.get("averageScore"),
                "popularity": item.get("popularity"),
                "poster_url": item.get("coverImage", {}).get("large"),
                "format": item.get("format"),
            })
        return results
