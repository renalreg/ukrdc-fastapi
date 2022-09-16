import uuid

from fastapi import APIRouter, Depends, HTTPException

from ukrdc_fastapi.dependencies import get_task_tracker
from ukrdc_fastapi.exceptions import TaskNotFoundError
from ukrdc_fastapi.tasks.background import TaskTracker, TrackableTaskSchema
from ukrdc_fastapi.utils.paginate import Page, paginate_sequence

router = APIRouter(tags=["Background Tasks"])


@router.get("", response_model=Page[TrackableTaskSchema])
async def tasks(
    tracker: TaskTracker = Depends(get_task_tracker),
):
    """Return a list of all non-expired background tasks"""
    return paginate_sequence(tracker.get_all())


@router.get("/{task_id}", response_model=TrackableTaskSchema)
async def task(
    task_id: uuid.UUID,
    tracker: TaskTracker = Depends(get_task_tracker),
) -> TrackableTaskSchema:
    """Return a specific background task"""
    try:
        return tracker.get(task_id.hex)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail="fTask {task_id} not found") from e
