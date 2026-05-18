from fastapi import APIRouter
from app.connectors.tautulli import TautulliConnector

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/now")
async def now_playing():
    connector = TautulliConnector()
    sessions = await connector.get_activity()
    return {"sessions": sessions}


@router.get("/history")
async def watch_history(length: int = 100):
    connector = TautulliConnector()
    history = await connector.get_history(length=length)
    return {"history": history}


@router.get("/users")
async def list_users():
    connector = TautulliConnector()
    users = await connector.get_users()
    return {"users": users}


@router.get("/users/stats")
async def users_stats():
    connector = TautulliConnector()
    users = await connector.get_users()
    results = []
    for u in users:
        stats = await connector.get_user_watch_time_stats(u["user_id"])
        if not stats:
            continue
        # Tautulli returns periods (1d, 7d, 30d, 0=all); pick all-time (query_days==0) or sum
        total_time = 0
        total_plays = 0
        for s in stats:
            total_time += s.get("total_time", 0)
            total_plays += s.get("total_plays", 0)
        results.append({
            "user_id": u["user_id"],
            "username": u["username"],
            "total_time": total_time,
            "total_plays": total_plays,
            "total_time_minutes": total_time // 60,
        })
    return {"users": results}


@router.get("/top")
async def top_watched(length: int = 50):
    connector = TautulliConnector()
    history = await connector.get_history(length=length)
    # Aggregate by rating_key
    agg = {}
    for h in history:
        key = h["rating_key"]
        if key not in agg:
            agg[key] = {
                "rating_key": key,
                "title": h["title"],
                "grandparent_title": h.get("grandparent_title"),
                "media_type": h["media_type"],
                "total_plays": 0,
                "total_duration": 0,
                "thumb": h.get("thumb"),
            }
        agg[key]["total_plays"] += 1
        agg[key]["total_duration"] += h.get("duration", 0)
    sorted_top = sorted(agg.values(), key=lambda x: x["total_plays"], reverse=True)
    items = []
    for item in sorted_top[:20]:
        items.append({
            **item,
            "play_count": item["total_plays"],
            "total_duration_minutes": item["total_duration"] // 60,
        })
    return {"items": items}
