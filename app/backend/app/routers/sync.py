from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.celery_app import celery_app
from app.schemas import SyncTriggerResponse

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/plex", response_model=SyncTriggerResponse)
async def sync_plex():
    task = celery_app.send_task("app.tasks.sync.sync_plex_library")
    return SyncTriggerResponse(
        task_id=task.id,
        status="started",
        message="Plex library sync triggered",
    )


@router.post("/tautulli", response_model=SyncTriggerResponse)
async def sync_tautulli():
    task = celery_app.send_task("app.tasks.sync.sync_tautulli_stats")
    return SyncTriggerResponse(
        task_id=task.id,
        status="started",
        message="Tautulli stats sync triggered",
    )


@router.post("/external", response_model=SyncTriggerResponse)
async def sync_external():
    task = celery_app.send_task("app.tasks.sync.refresh_external_classics")
    return SyncTriggerResponse(
        task_id=task.id,
        status="started",
        message="External classics refresh triggered",
    )


@router.post("/all", response_model=SyncTriggerResponse)
async def sync_all():
    # Sequential chaining via signature
    from celery import chain
    workflow = chain(
        celery_app.signature("app.tasks.sync.sync_plex_library"),
        celery_app.signature("app.tasks.sync.sync_tautulli_stats"),
        celery_app.signature("app.tasks.sync.refresh_external_classics"),
    )
    task = workflow.apply_async()
    return SyncTriggerResponse(
        task_id=task.id,
        status="started",
        message="Full sync workflow triggered",
    )


@router.post("/trigger", response_model=SyncTriggerResponse)
async def sync_trigger():
    """Alias to trigger a full sync from the frontend."""
    from celery import chain
    workflow = chain(
        celery_app.signature("app.tasks.sync.sync_plex_library"),
        celery_app.signature("app.tasks.sync.sync_tautulli_stats"),
        celery_app.signature("app.tasks.sync.refresh_external_classics"),
    )
    task = workflow.apply_async()
    return SyncTriggerResponse(
        task_id=task.id,
        status="started",
        message="Full sync workflow triggered",
    )
