from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.auth import get_current_user, get_current_admin
from app.celery_app import celery_app
from app.services.tasks import get_recent_tasks, update_task_status

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


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, admin=Depends(get_current_admin)):
    tasks = await get_recent_tasks(limit=100, hours=24)
    task = next((t for t in tasks if t.task_id == task_id), None)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.status not in ("pending", "running"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is already {task.status}",
        )

    celery_app.control.revoke(task_id, terminate=True, wait=False)
    await update_task_status(task_id, status="cancelled", message="Cancelled by user")
    return {"task_id": task_id, "status": "cancelled"}
