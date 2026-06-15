from datetime import datetime, timedelta, timezone
from sqlalchemy import select, desc
from app.database import AsyncSessionLocal
from app.models import TaskStatus


async def create_task_status(task_id: str, task_name: str, status: str = "running", progress: int = 0, message: str = "Starting..."):
    async with AsyncSessionLocal() as db:
        ts = TaskStatus(
            task_id=task_id,
            task_name=task_name,
            status=status,
            progress=progress,
            message=message,
        )
        db.add(ts)
        await db.commit()


async def update_task_status(task_id: str, status: str = None, progress: int = None, message: str = None, result: dict = None):
    async with AsyncSessionLocal() as db:
        row = await db.scalar(select(TaskStatus).where(TaskStatus.task_id == task_id))
        if row:
            if status:
                row.status = status
            if progress is not None:
                row.progress = progress
            if message:
                row.message = message
            if result:
                row.result = result
            await db.commit()


async def get_recent_tasks(limit: int = 20, hours: int = 24):
    async with AsyncSessionLocal() as db:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await db.execute(
            select(TaskStatus)
            .where(TaskStatus.created_at >= since)
            .order_by(desc(TaskStatus.created_at))
            .limit(limit)
        )
        return result.scalars().all()
