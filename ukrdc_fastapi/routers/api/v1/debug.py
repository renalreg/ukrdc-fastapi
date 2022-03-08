import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends

from ukrdc_fastapi.dependencies import get_task_tracker
from ukrdc_fastapi.schemas.base import JSONModel
from ukrdc_fastapi.tasks.background import TaskTracker, TrackableTaskSchema

router = APIRouter(tags=["Debug"])


class DebugCreateTaskInput(JSONModel):
    time: int


async def wait_for(time: int):
    await asyncio.sleep(time)
    return {"time": time}


@router.post("/create_task/", status_code=202, response_model=TrackableTaskSchema)
def debug_create_task(
    args: DebugCreateTaskInput,
    background_tasks: BackgroundTasks,
    tracker: TaskTracker = Depends(get_task_tracker),
):
    task = tracker.http_create(wait_for, visibility="private")
    background_tasks.add_task(task.tracked, args.time)
    return task.response()
