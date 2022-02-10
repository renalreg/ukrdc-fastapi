import asyncio
import inspect
import typing
import uuid
from functools import wraps

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Security
from pydantic import BaseModel
from redis import Redis

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth

router = APIRouter()


@router.get("/")
def testing_hello():
    return "Hello world"


async def task_good(n: int):
    print("starting good task")
    await asyncio.sleep(n)
    print("good task finished")


async def task_bad(n: int):
    print("starting bad task")
    await asyncio.sleep(n)
    raise RuntimeError("bad task finished")


class TaskSubmitModel(BaseModel):
    n: int
    bad: bool = False


VisibilityType = typing.Literal["public", "private"]
StatusType = typing.Literal["pending", "running", "finished", "failed"]


class TaskInfo(BaseModel):
    id: str
    lock: str
    name: str
    visibility: VisibilityType
    owner: str
    status: StatusType
    error: typing.Optional[str]

    def redis_dict(self):
        data = self.dict()
        converted_data = {}
        for k, v in data.items():
            converted_data[k] = v if v is not None else ""
        return converted_data


class TaskLockError(Exception):
    pass


class TrackableTask:
    def __init__(
        self,
        redis: Redis,
        user: UKRDCUser,
        func: typing.Callable,
        name: typing.Optional[str] = None,
        lock: typing.Optional[str] = None,
        visibility: VisibilityType = "public",
    ):
        self.redis = redis
        self.user = user

        self.id = uuid.uuid4().hex
        self.name = name or func.__name__
        self.lock = lock
        self.visibility = visibility
        self.owner = self.user.email
        self.status = "pending"
        self.error = None

        self._func = func
        self._lock_key = f"_LOCK_{self.lock}" if self.lock else None

        self.prime()

        self.redis.hmset(self.id, self.dict())

    def dict(self):
        return {
            "id": self.id or "",
            "lock": self.lock or "",
            "name": self.name or "",
            "visibility": self.visibility,
            "owner": self.owner or "",
            "status": self.status or "",
            "error": self.error or "",
        }

    def prime(self):
        """
        Acquire the tasks lock prior to running.
        The lock will automatically release after 60 seconds if the task is not started.
        """
        self.acquire()
        self.redis.expire(self._lock_key, settings.redis_tasks_expire_lock)

    def acquire(self):
        # If we're working with a lockable function
        if self.lock:
            # Check if the lock is already acquired
            active_lock = self.redis.get(self._lock_key)
            if active_lock:
                # If lock is already acquired, raise an error
                raise TaskLockError(f"Task {self.name} is locked by task {active_lock}")
            # Acquire the lock
            self.redis.set(self._lock_key, self.id)

    def release(self):
        if self.lock:
            # Release the lock
            self.redis.delete(self._lock_key)

    @property
    def tracked(self) -> typing.Callable:
        @wraps(self._func)
        async def wrapper(*args: typing.Any, **kwargs: typing.Any) -> None:
            func_args = inspect.signature(self._func).bind(*args, **kwargs).arguments
            func_args_str = ", ".join(
                "{}={!r}".format(*item) for item in func_args.items()
            )

            # Update the task status to running
            print(f"[{self.id}] Started {self.name} with arguments: {func_args_str}")
            self.redis.hset(self.id, "status", "running")

            # Remove the lock expiry now the task is running
            if self.lock:
                self.redis.persist(self._lock_key)

            try:
                await self._func(*args, **kwargs)
                print(f"[{self.id}] Finished {self.name} Successfully")
                # Mark the task as finished
                self.redis.hset(self.id, "status", "finished")
                # Expire the task after the configured time
                self.redis.expire(self.id, settings.redis_tasks_expire)
            except Exception as e:  # 4
                print(f"[{self.id}] Failed Permanently {self.name} with error: {e}")
                # Mark the task as errored
                self.redis.hset(self.id, "status", "error")
                # Set the error message
                self.redis.hset(self.id, "error", str(e))
                # Expire the task after the configured time
                self.redis.expire(self.id, settings.redis_tasks_expire_error)
            finally:
                # Release the lock
                self.release()

        return wrapper


class TaskTracker:
    def __init__(self, redis: Redis, user: UKRDCUser):
        self.redis = redis
        self.user = user

    def get_all():
        pass

    def create(
        self,
        func: typing.Callable,
        name: typing.Optional[str] = None,
        lock: typing.Optional[str] = None,
        visibility: VisibilityType = "public",
    ) -> TrackableTask:
        return TrackableTask(
            redis=self.redis,
            user=self.user,
            func=func,
            name=name,
            lock=lock,
            visibility=visibility,
        )


def get_task_tracker(user: UKRDCUser = Security(auth.get_user())) -> TaskTracker:
    """Creates a TaskTracker pre-populated with a User and Redis session"""
    return TaskTracker(
        Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_tasks_db,
            decode_responses=True,
        ),
        user,
    )


@router.post("/tasks/", status_code=202)
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
            task_func, lock=f"task-{params.n}-{'bad' if params.bad else 'good'}"
        )
    except TaskLockError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        ) from e

    background_tasks.add_task(task.tracked, params.n)

    return {"message": "A task has been started"}
