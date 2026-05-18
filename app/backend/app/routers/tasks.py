from fastapi import APIRouter
from app.services.tasks import get_recent_tasks

router = APIRouter(tags=["tasks"])


@router.get("/tasks")
async def list_tasks():
    tasks = await get_recent_tasks(limit=20)
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
