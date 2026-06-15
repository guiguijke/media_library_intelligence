import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import httpx
import redis.asyncio as redis
from aiolimiter import AsyncLimiter
from app.config import settings
from app.services.settings import get_setting

logger = logging.getLogger(__name__)

# TMDB has a soft limit of ~40 requests/second and 20 concurrent connections per IP.
# Stay safely under it to avoid 429s during large syncs.
_TMDB_RATE_LIMIT = 35


class TMDBConnector:
    def __init__(self):
        self.api_key = ""
        self.base_url = ""
        self.image_base_url = ""
        self.timeout = 30.0
        self._redis: Optional[redis.Redis] = None
        self._rate_limiter = AsyncLimiter(_TMDB_RATE_LIMIT, 1)

    async def _init(self):
        self.api_key = await get_setting("TMDB_API_KEY")
        self.base_url = (await get_setting("TMDB_BASE_URL")).rstrip("/")
        self.image_base_url = (await get_setting("TMDB_IMAGE_BASE_URL")).rstrip("/")

    async def _get_redis(self) -> Optional[redis.Redis]:
        if self._redis is None:
            try:
                self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception as exc:
                logger.warning(f"Redis unavailable: {exc}")
        return self._redis

    async def _cache_get(self, key: str) -> Optional[str]:
        r = await self._get_redis()
        if not r:
            return None
        try:
            return await r.get(key)
        except Exception:
            return None

    async def _cache_set(self, key: str, value: str, ttl: int = 3600) -> None:
        r = await self._get_redis()
        if not r:
            return
        try:
            await r.setex(key, ttl, value)
        except Exception:
            pass

    @staticmethod
    def _is_jwt(token: str) -> bool:
        """Detect TMDB read access tokens (JWT) vs legacy API keys."""
        return isinstance(token, str) and token.count(".") == 2

    async def _request(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        await self._init()
        url = f"{self.base_url}{endpoint}"
        query = params.copy() if params else {}
        headers = {}
        if self._is_jwt(self.api_key):
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            query["api_key"] = self.api_key
        cache_key = f"tmdb:{endpoint}:{json.dumps(query, sort_keys=True)}"

        cached = await self._cache_get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                pass

        last_error = None
        for attempt in range(3):
            try:
                async with self._rate_limiter:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.get(url, params=query, headers=headers)
                        response.raise_for_status()
                        data = response.json()
                        await self._cache_set(cache_key, json.dumps(data))
                        return data
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    retry_after = int(exc.response.headers.get("Retry-After", 1))
                    wait = retry_after * (2 ** attempt)
                    logger.warning(
                        f"TMDB rate limit hit ({url}), waiting {wait}s before retry {attempt + 1}/3"
                    )
                    await asyncio.sleep(wait)
                    last_error = exc
                    continue
                logger.error(f"TMDB API HTTP error ({url}): {exc.response.status_code}")
                return None
            except Exception as exc:
                logger.error(f"TMDB API error ({url}): {exc}")
                return None

        if last_error:
            logger.error(f"TMDB API rate limit exceeded after retries ({url}): {last_error}")
        return None

    def _build_poster(self, path: Optional[str]) -> Optional[str]:
        if path:
            return f"{self.image_base_url}{path}"
        return None

    async def get_top_rated_movies(self, page: int = 1) -> List[Dict[str, Any]]:
        data = await self._request("/movie/top_rated", {"page": page})
        if not data or "results" not in data:
            return []
        results = []
        for item in data["results"]:
            results.append({
                "tmdb_id": item.get("id"),
                "title": item.get("title"),
                "original_title": item.get("original_title"),
                "year": int(item["release_date"][:4]) if item.get("release_date") else None,
                "genre_ids": item.get("genre_ids", []),
                "original_language": item.get("original_language"),
                "vote_average": item.get("vote_average"),
                "vote_count": item.get("vote_count"),
                "popularity": item.get("popularity"),
                "poster_url": self._build_poster(item.get("poster_path")),
            })
        return results

    async def get_top_rated_series(self, page: int = 1) -> List[Dict[str, Any]]:
        data = await self._request("/tv/top_rated", {"page": page})
        if not data or "results" not in data:
            return []
        results = []
        for item in data["results"]:
            results.append({
                "tmdb_id": item.get("id"),
                "title": item.get("name"),
                "original_title": item.get("original_name"),
                "year": int(item["first_air_date"][:4]) if item.get("first_air_date") else None,
                "genre_ids": item.get("genre_ids", []),
                "original_language": item.get("original_language"),
                "vote_average": item.get("vote_average"),
                "vote_count": item.get("vote_count"),
                "popularity": item.get("popularity"),
                "poster_url": self._build_poster(item.get("poster_path")),
            })
        return results

    async def discover_animation(self, filters: Optional[dict] = None, page: int = 1) -> List[Dict[str, Any]]:
        params = {
            "with_genres": "16",
            "sort_by": "vote_average.desc",
            "vote_count.gte": 50,
            "page": page,
        }
        if filters:
            params.update(filters)
        data = await self._request("/discover/movie", params)
        if not data or "results" not in data:
            return []
        results = []
        for item in data["results"]:
            results.append({
                "tmdb_id": item.get("id"),
                "title": item.get("title"),
                "original_title": item.get("original_title"),
                "year": int(item["release_date"][:4]) if item.get("release_date") else None,
                "genre_ids": item.get("genre_ids", []),
                "original_language": item.get("original_language"),
                "vote_average": item.get("vote_average"),
                "vote_count": item.get("vote_count"),
                "popularity": item.get("popularity"),
                "poster_url": self._build_poster(item.get("poster_path")),
            })
        return results

    async def search_by_title_year(self, title: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {"query": title}
        if year:
            params["year"] = year
        data = await self._request("/search/multi", params)
        if not data or "results" not in data:
            return []
        results = []
        for item in data["results"]:
            if item.get("media_type") not in ("movie", "tv"):
                continue
            results.append({
                "tmdb_id": item.get("id"),
                "title": item.get("title") or item.get("name"),
                "original_title": item.get("original_title") or item.get("original_name"),
                "year": year,
                "media_type": item.get("media_type"),
                "poster_url": self._build_poster(item.get("poster_path")),
            })
        return results

    async def get_movie_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        data = await self._request(f"/movie/{tmdb_id}")
        if not data:
            return None
        return {
            "tmdb_id": data.get("id"),
            "title": data.get("title"),
            "original_title": data.get("original_title"),
            "year": int(data["release_date"][:4]) if data.get("release_date") else None,
            "genre_ids": [g["id"] for g in data.get("genres", [])],
            "vote_average": data.get("vote_average"),
            "vote_count": data.get("vote_count"),
            "popularity": data.get("popularity"),
            "poster_url": self._build_poster(data.get("poster_path")),
            "overview": data.get("overview"),
            "belongs_to_collection": data.get("belongs_to_collection"),
        }

    async def get_tv_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        data = await self._request(f"/tv/{tmdb_id}", params={"append_to_response": "external_ids"})
        if not data:
            return None
        return {
            "tmdb_id": data.get("id"),
            "title": data.get("name"),
            "original_title": data.get("original_name"),
            "year": int(data["first_air_date"][:4]) if data.get("first_air_date") else None,
            "genre_ids": [g["id"] for g in data.get("genres", [])],
            "vote_average": data.get("vote_average"),
            "vote_count": data.get("vote_count"),
            "popularity": data.get("popularity"),
            "poster_url": self._build_poster(data.get("poster_path")),
            "overview": data.get("overview"),
            "tvdb_id": data.get("external_ids", {}).get("tvdb_id"),
        }

    async def get_collection_details(self, collection_id: int) -> Optional[Dict[str, Any]]:
        data = await self._request(f"/collection/{collection_id}")
        if not data:
            return None
        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "total": len(data.get("parts", [])),
            "poster_url": self._build_poster(data.get("poster_path")),
            "backdrop_url": self._build_poster(data.get("backdrop_path")),
        }

    async def test_connection(self) -> bool:
        try:
            data = await self._request("/configuration")
            return bool(data and "images" in data)
        except Exception:
            return False
