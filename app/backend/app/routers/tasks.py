from fastapi import APIRouter, Depends, Query

from app.auth import get_current_user
from app.services.tasks import get_recent_tasks

router = APIRouter(
    tags=["tasks"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/tasks")
async def list_tasks(limit: int = Query(20, ge=1), hours: int = Query(24, ge=1)):
    tasks = await get_recent_tasks(limit=limit, hours=hours)
    return [
        {
            "task_id": t.task_id,
            "task_name": t.task_name,
            "status": t.status,
            "progress": t.progress,
            "message": t.message,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
        for t in tasks
    ]
