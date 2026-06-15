import logging
from typing import Any, Dict, List, Optional

import httpx
from app.services.settings import get_setting

logger = logging.getLogger(__name__)


class TautulliConnector:
    def __init__(self):
        self.base_url = ""
        self.api_key = ""
        self.timeout = 30.0

    async def _init(self):
        self.base_url = (await get_setting("TAUTULLI_BASE_URL")).rstrip("/")
        self.api_key = await get_setting("TAUTULLI_API_KEY")

    async def _request(self, cmd: str, params: Optional[dict] = None) -> Optional[dict]:
        await self._init()
        url = f"{self.base_url}/api/v2"
        payload = {
            "apikey": self.api_key,
            "cmd": cmd,
        }
        if params:
            payload.update(params)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=payload)
                response.raise_for_status()
                data = response.json()
                result = data.get("response", {}).get("result")
                if result == "success" or result is True:
                    return data["response"]["data"]
                logger.warning(f"Tautulli error ({cmd}): result={result}, full_response={data}")
                return None
        except Exception as exc:
            logger.error(f"Tautulli API error ({cmd}): {exc}")
            return None

    async def get_watch_stats(self) -> List[Dict[str, Any]]:
        """Retrieves stats per user and media."""
        history = await self._request("get_history", {"length": 10000})
        if not history or "data" not in history:
            return []

        records = history["data"]
        if not isinstance(records, list):
            return []

        stats = {}
        for row in records:
            user_id = str(row.get("user_id", "unknown"))
            rating_key = str(row.get("rating_key", "unknown"))
            key = (user_id, rating_key)

            if key not in stats:
                stats[key] = {
                    "user_id": user_id,
                    "media_id": rating_key,
                    "watch_count": 0,
                    "percent_complete": 0.0,
                    "last_watched": row.get("date"),
                }

            stats[key]["watch_count"] += 1
            percent = row.get("percent_complete", 0) or 0
            if percent > stats[key]["percent_complete"]:
                stats[key]["percent_complete"] = percent

        return list(stats.values())

    async def get_activity(self) -> List[Dict]:
        data = await self._request("get_activity")
        logger.info(f"Tautulli get_activity raw response: {data}")
        if not data:
            return []
        sessions = data.get("sessions") or data.get("session")
        if not sessions:
            logger.info("Tautulli get_activity: no sessions found in response")
            return []
        if not isinstance(sessions, list):
            sessions = [sessions]
        results = []
        for s in sessions:
            results.append({
                "session_key": s.get("session_key"),
                "user": s.get("user", "Unknown"),
                "user_id": str(s.get("user_id", "")),
                "title": s.get("title", "Unknown"),
                "grandparent_title": s.get("grandparent_title"),
                "media_type": s.get("media_type"),
                "state": s.get("state", "playing"),
                "progress_percent": s.get("progress_percent", 0),
                "duration": s.get("duration", 0),
                "location": s.get("location", ""),
                "player": s.get("player", ""),
                "platform": s.get("platform", ""),
                "thumb": s.get("thumb"),
                "rating_key": str(s.get("rating_key", "")),
            })
        logger.info(f"Tautulli get_activity: returned {len(results)} sessions")
        return results

    async def get_history(self, length: int = 100) -> List[Dict]:
        data = await self._request("get_history", {"length": length})
        logger.info(f"Tautulli get_history raw response type: {type(data)}")
        if not data:
            return []
        records = data.get("data") if isinstance(data, dict) else data
        if not records:
            return []
        if not isinstance(records, list):
            records = [records]
        results = []
        for row in records:
            results.append({
                "user": row.get("user", "Unknown"),
                "user_id": str(row.get("user_id", "")),
                "title": row.get("title", "Unknown"),
                "grandparent_title": row.get("grandparent_title"),
                "media_type": row.get("media_type"),
                "started": row.get("started"),
                "stopped": row.get("stopped"),
                "duration": row.get("duration", 0),
                "percent_complete": row.get("percent_complete", 0),
                "rating_key": str(row.get("rating_key", "")),
                "thumb": row.get("thumb"),
            })
        logger.info(f"Tautulli get_history: returned {len(results)} records")
        return results

    async def get_users(self) -> List[Dict]:
        data = await self._request("get_users")
        logger.info(f"Tautulli get_users raw response type: {type(data)}")
        if not data:
            return []
        users = data if isinstance(data, list) else [data] if data else []
        results = []
        for u in users:
            results.append({
                "user_id": str(u.get("user_id", "")),
                "username": u.get("username", "Unknown"),
                "email": u.get("email"),
                "thumb": u.get("thumb"),
                "is_active": u.get("is_active", True),
            })
        logger.info(f"Tautulli get_users: returned {len(results)} users")
        return results

    async def get_user_watch_time_stats(self, user_id: str = None) -> List[Dict]:
        params = {}
        if user_id:
            params["user_id"] = user_id
        data = await self._request("get_user_watch_time_stats", params)
        logger.info(f"Tautulli get_user_watch_time_stats raw response type: {type(data)}")
        if not data:
            return []
        stats = data if isinstance(data, list) else [data] if data else []
        results = []
        for s in stats:
            results.append({
                "user_id": str(user_id) if user_id else str(s.get("user_id", "")),
                "username": s.get("username", "Unknown"),
                "query_days": s.get("query_days", 0),
                "total_time": s.get("total_time", 0),
                "total_plays": s.get("total_plays", 0),
            })
        logger.info(f"Tautulli get_user_watch_time_stats: returned {len(results)} stats")
        return results

    async def test_connection(self) -> bool:
        try:
            data = await self._request("get_servers_info")
            return data is not None
        except Exception:
            return False
