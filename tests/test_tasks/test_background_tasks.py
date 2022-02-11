import asyncio
from typing import Optional

import pytest
import pytest_asyncio
from fastapi import BackgroundTasks, Depends
from httpx import AsyncClient
from pydantic import BaseModel

from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.dependencies import get_task_tracker
from ukrdc_fastapi.tasks.background import TaskTracker, TrackableTaskSchema

"""
NOTE: 
When running in a test environment, background tasks don't run in the same
way as they do in production. Here, when a task is started it will full complete
before the view function return value is actually sent back to the client. 

In practice, this means that the tasks will never be in a running state here, however
we can still test core functionality by assuming that the FastAPI background task
functionality is passing tests upstream.
"""


class TaskSubmitModel(BaseModel):
    time_to_wait: float
    bad: bool = False
    private: bool = False
    force_owner: Optional[str] = None


@pytest.mark.anyio
async def task_good(time_to_wait: int):
    await asyncio.sleep(time_to_wait)


@pytest.mark.anyio
async def task_bad(time_to_wait: int):
    await asyncio.sleep(time_to_wait)
    raise RuntimeError("bad task finished")


@pytest.fixture(scope="function")
def app_with_tasks(app):
    @app.post("/start_task/", status_code=202, response_model=TrackableTaskSchema)
    async def send_task(
        params: TaskSubmitModel,
        background_tasks: BackgroundTasks,
        tracker: TaskTracker = Depends(get_task_tracker),
    ):
        if params.bad:
            task_func = task_bad
        else:
            task_func = task_good

        task = tracker.http_create(
            task_func,
            lock=f"task-{params.time_to_wait}-{'bad' if params.bad else 'good'}",
            visibility="private" if params.private else "public",
        )

        if params.force_owner:
            task.owner = params.force_owner
            task._sync()

        background_tasks.add_task(task.tracked, params.time_to_wait)

        return task.response()

    return app


@pytest_asyncio.fixture(scope="function")
async def client_with_tasks(app_with_tasks):
    async with AsyncClient(app=app_with_tasks, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_submit_task(client_with_tasks):
    response = await client_with_tasks.post("/start_task/", json={"time_to_wait": 0.1})
    assert response.status_code == 202
    assert response.json().get("status") == "pending"
    assert response.json().get("owner") == "TEST@UKRDC_FASTAPI"
    assert response.json().get("visibility") == "public"


@pytest.mark.asyncio
async def test_get_task(client_with_tasks):
    response = await client_with_tasks.post("/start_task/", json={"time_to_wait": 0.1})
    assert response.status_code == 202
    task_id = response.json().get("id")

    task_status = await client_with_tasks.get(
        f"{configuration.base_url}/v1/tasks/{task_id}/"
    )
    assert task_status.status_code == 200
    assert task_status.json().get("status") == "finished"


@pytest.mark.asyncio
async def test_get_task_error(client_with_tasks):
    response = await client_with_tasks.post(
        "/start_task/", json={"time_to_wait": 0.1, "bad": True}
    )
    assert response.status_code == 202
    task_id = response.json().get("id")

    task_status = await client_with_tasks.get(
        f"{configuration.base_url}/v1/tasks/{task_id}/"
    )
    assert task_status.status_code == 200
    assert task_status.json().get("status") == "failed"
    assert task_status.json().get("error") == "bad task finished"


@pytest.mark.asyncio
async def test_get_task_missing(client_with_tasks):
    task_status = await client_with_tasks.get(
        f"{configuration.base_url}/v1/tasks/00000000-0000-0000-0000-000000000000/"
    )
    assert task_status.status_code == 404


@pytest.mark.asyncio
async def test_get_tasks_list(client_with_tasks):
    # Start some tasks
    await asyncio.gather(
        client_with_tasks.post("/start_task/", json={"time_to_wait": 0.1}),
        client_with_tasks.post("/start_task/", json={"time_to_wait": 0.0}),
        client_with_tasks.post("/start_task/", json={"time_to_wait": 0.1, "bad": True}),
    )

    tasks_list = await client_with_tasks.get(f"{configuration.base_url}/v1/tasks/")
    assert tasks_list.status_code == 200
    assert len(tasks_list.json()) == 3


@pytest.mark.asyncio
async def test_get_tasks_private(client_with_tasks):
    # Start some tasks
    await asyncio.gather(
        client_with_tasks.post(
            "/start_task/",
            json={
                "time_to_wait": 0.1,
                "private": True,
                "force_owner": "TEST2@UKRDC_FASTAPI",  # Override task owner to check list visibility
            },
        ),
        client_with_tasks.post("/start_task/", json={"time_to_wait": 0.0}),
        client_with_tasks.post("/start_task/", json={"time_to_wait": 0.1, "bad": True}),
    )

    tasks_list = await client_with_tasks.get(f"{configuration.base_url}/v1/tasks/")
    assert tasks_list.status_code == 200
    # Assert the private task started by another user is excluded
    assert len(tasks_list.json()) == 2


@pytest.mark.asyncio
async def test_submit_task_lock_error(client_with_tasks):
    results = await asyncio.gather(
        client_with_tasks.post("/start_task/", json={"time_to_wait": 1}),
        client_with_tasks.post("/start_task/", json={"time_to_wait": 1}),
        client_with_tasks.post("/start_task/", json={"time_to_wait": 1}),
    )
    codes = [r.status_code for r in results]
    codes.sort()
    # Assert that only one of the identical tasks was started
    assert codes == [202, 409, 409]
