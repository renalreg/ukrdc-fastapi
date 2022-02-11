import uuid

from fastapi import APIRouter, Depends, HTTPException

from ukrdc_fastapi.dependencies import get_task_tracker
from ukrdc_fastapi.exceptions import TaskNotFoundError
from ukrdc_fastapi.tasks.background import TaskTracker, TrackableTaskSchema

router = APIRouter(tags=["Background Tasks"])


@router.get("/", response_model=list[TrackableTaskSchema])
async def get_tasks(
    tracker: TaskTracker = Depends(get_task_tracker),
) -> list[TrackableTaskSchema]:
    """Return a list of all non-expired background tasks

    Args:
        tracker (TaskTracker, optional): Task tracker dependency. Defaults to Depends(get_task_tracker).

    Returns:
        list[TrackableTaskSchema]: List of tasks
    """
    return tracker.get_all()


@router.get("/{task_id}", response_model=TrackableTaskSchema)
async def get_task(
    task_id: uuid.UUID,
    tracker: TaskTracker = Depends(get_task_tracker),
) -> TrackableTaskSchema:
    """
    Return a specific background task

    Args:
        task_id (uuid.UUID): Task ID
        tracker (TaskTracker, optional): Task tracker dependency. Defaults to Depends(get_task_tracker).

    Returns:
        TrackableTaskSchema: Task resource
    """
    try:
        return tracker.get(task_id.hex)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail="fTask {task_id} not found") from e
