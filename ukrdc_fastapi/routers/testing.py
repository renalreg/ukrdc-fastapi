import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from ukrdc_fastapi.dependencies import get_task_tracker
from ukrdc_fastapi.exceptions import TaskLockError
from ukrdc_fastapi.tasks.background import TaskTracker, TrackableTaskSchema

router = APIRouter()


@router.get("/")
def testing_hello():
    return "Hello world"


async def task_good(time_to_wait: int):
    print("starting good task")
    await asyncio.sleep(time_to_wait)
    print("good task finished")


async def task_bad(time_to_wait: int):
    print("starting bad task")
    await asyncio.sleep(time_to_wait)
    raise RuntimeError("bad task finished")


class TaskSubmitModel(BaseModel):
    time_to_wait: int
    bad: bool = False


@router.post("/start_task/", status_code=202, response_model=TrackableTaskSchema)
async def send_task(
    params: TaskSubmitModel,
    background_tasks: BackgroundTasks,
    tracker: TaskTracker = Depends(get_task_tracker),
):
    if params.bad:
        task_func = task_bad
    else:
        task_func = task_good

    try:
        task = tracker.create(
            task_func,
            lock=f"task-{params.time_to_wait}-{'bad' if params.bad else 'good'}",
        )
    except TaskLockError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        ) from e

    background_tasks.add_task(task.tracked, params.time_to_wait)

    return task.response()
