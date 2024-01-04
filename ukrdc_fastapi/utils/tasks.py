import datetime
import inspect
from functools import wraps
from typing import Any, Callable, Literal, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import Field
from redis import Redis

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.exceptions import TaskLockError, TaskNotFoundError
from ukrdc_fastapi.schemas.base import JSONModel

_LOCK_PREFIX = "_LOCK_"

VisibilityType = Literal["public", "private"]
StatusType = Literal["pending", "running", "finished", "failed"]


class TrackableTaskSchema(JSONModel):
    """Base schema for a trackable background task"""

    id: UUID = Field(..., description="Task UUID")
    name: str = Field(..., description="Task friendly-name")
    visibility: VisibilityType = Field(
        ...,
        description="Task visibility. Private tasks are only visible to the user who created them",
    )
    owner: str = Field(..., description="Task owner username")
    status: StatusType = Field(..., description="Task status")
    error: Optional[str] = Field(None, description="Error message, if any")

    created: datetime.datetime = Field(..., description="Task creation timestamp")
    started: Optional[datetime.datetime] = Field(
        None, description="Task start timestamp"
    )
    finished: Optional[datetime.datetime] = Field(
        None, description="Task finish timestamp"
    )

    @classmethod
    def from_redis(cls, redis_dict: dict):
        """
        We can't store NoneType in Redis, so when loading
        from Redis we need to convert empty strings to None
        """
        normalized_dict: dict[str, Optional[str]] = {}
        for key, value in redis_dict.items():
            if value == "":
                normalized_dict[key] = None
            else:
                normalized_dict[key] = value
        return cls(**normalized_dict)


class TrackableTask:
    def __init__(
        self,
        task_redis: Redis,
        lock_redis: Redis,
        user: UKRDCUser,
        func: Callable,
        name: Optional[str] = None,
        lock: Optional[str] = None,
        visibility: VisibilityType = "public",
    ):
        self.task_redis: Redis = task_redis
        self.lock_redis: Redis = lock_redis

        self.user: UKRDCUser = user

        self.id: UUID = uuid4()
        self._key: str = self.id.hex

        self.name: str = name or func.__name__
        self.lock: Optional[str] = lock
        self.visibility: VisibilityType = visibility
        self.owner: Optional[str] = self.user.email
        self.status: StatusType = "pending"
        self.error: Optional[str] = None

        self.created: datetime.datetime = datetime.datetime.now()
        self.started: Optional[datetime.datetime] = None
        self.finished: Optional[datetime.datetime] = None

        self._func: Callable = func
        self._lock_key: Optional[str] = (
            f"{_LOCK_PREFIX}{self.lock}" if self.lock else None
        )

        self._prime()
        self._sync()

    def _rdict(self):
        # Redis-friendly dictionary represenation of the task
        return {
            "id": self.id.hex or "",
            "lock": self.lock or "",
            "name": self.name or "",
            "visibility": self.visibility,
            "owner": self.owner or "",
            "status": self.status or "",
            "error": self.error or "",
            "created": self.created.isoformat(),
            "started": self.started.isoformat() if self.started else "",
            "finished": self.finished.isoformat() if self.finished else "",
        }

    def response(self) -> TrackableTaskSchema:
        """Return the task resource representation, for use in the API

        Returns:
            TrackableTaskSchema: Task resource representation
        """
        return TrackableTaskSchema.from_orm(self)

    def _sync(self):
        self.task_redis.hset(self._key, mapping=self._rdict())

    def _prime(self):
        """
        Acquire the tasks lock prior to running.
        The lock will automatically release after 60 seconds if the task is not started.
        """
        if self.lock:
            self._acquire()
            self.lock_redis.expire(self._lock_key, settings.redis_tasks_expire_lock)

    def _acquire(self):
        """
        Acquire the tasks lock. This is useful to prevent multiple instances of the
        same task from running at the same time. The lock key can be any string and
        thus depend on the task arguments.
        This means we can, for example, prevent the same export running for a single
        patient multiple times simultaneously.
        """
        # If we're working with a lockable function
        if self.lock:
            # Check if the lock is already acquired
            active_lock = self.lock_redis.get(self._lock_key)
            if active_lock:
                # If lock is already acquired, raise an error
                raise TaskLockError(f"Task {self.name} is locked by task {active_lock}")
            # Acquire the lock
            self.lock_redis.set(self._lock_key, self._key)

    def _release(self):
        if self.lock:
            # Release the lock
            self.lock_redis.delete(self._lock_key)

    @property
    def tracked(self) -> Callable:
        """
        Wrap a function with tracking functionality. This wrapper is what enables
        us to check a task's status and error state at any point in the future, by
        querying the Redis database.
        """

        @wraps(self._func)
        async def wrapper(*args: Any, **kwargs: Any) -> None:
            func_args = inspect.signature(self._func).bind(*args, **kwargs).arguments
            func_args_str = ", ".join(
                "{}={!r}".format(*item)  # pylint: disable=consider-using-f-string
                for item in func_args.items()
            )

            # Update the task status to running
            print(f"[{self.id}] Started {self.name} with arguments: {func_args_str}")
            self.status = "running"
            self.started = datetime.datetime.now()
            self._sync()

            # Remove the lock expiry now the task is running
            if self.lock:
                self.lock_redis.persist(self._lock_key)

            try:
                await self._func(*args, **kwargs)
                print(f"[{self.id}] Finished {self.name} Successfully")
                # Mark the task as finished
                self.status = "finished"
                self._sync()
                # Expire the task after the configured time
                self.task_redis.expire(self._key, settings.redis_tasks_expire)
            except Exception as e:  # pylint: disable=broad-except
                print(f"[{self.id}] Failed Permanently {self.name} with error: {e}")
                # Mark the task as errored
                self.status = "failed"
                # Set the error message
                self.error = str(e)
                # Sync to redis
                self._sync()
                # Expire the task after the configured time
                self.task_redis.expire(self._key, settings.redis_tasks_expire_error)
            finally:
                self.finished = datetime.datetime.now()
                # Sync to redis
                self._sync()
                # Release the lock
                self._release()

        return wrapper


class TaskTracker:
    def __init__(self, task_redis: Redis, lock_redis: Redis, user: UKRDCUser):
        self.task_redis = task_redis
        self.lock_redis = lock_redis
        self.user = user

    def get_all(self) -> list[TrackableTaskSchema]:
        """Get a list of all trackable task resource representations

        Returns:
            list[TrackableTaskSchema]: List of tasks
        """
        tasks: list[TrackableTaskSchema] = []
        for key in self.task_redis.scan_iter():
            # Convert Redis map to TrackableTaskSchema
            task = TrackableTaskSchema.from_redis(self.task_redis.hgetall(key))
            # Only show public tasks or those owned by the current user
            if task.visibility == "public" or task.owner == self.user.email:
                tasks.append(task)

        # Sort by created date
        tasks.sort(key=lambda x: x.created, reverse=True)
        return tasks

    def get(self, key: str) -> TrackableTaskSchema:
        """
        Get a task resource representation by its key

        Args:
            key (str): Task key (UUID hex)

        Raises:
            TaskNotFoundError: Task is expired or does not exist

        Returns:
            TrackableTaskSchema: Task resource representation
        """
        if not self.task_redis.exists(key):
            raise TaskNotFoundError(f"Task {key} does not exist")
        return TrackableTaskSchema.from_redis(self.task_redis.hgetall(key))

    def create(
        self,
        func: Callable,
        name: Optional[str] = None,
        lock: Optional[str] = None,
        visibility: VisibilityType = "public",
    ) -> TrackableTask:
        """Create, track, and start a new background task

        Args:
            func (Callable): Function to wrap and run in the background
            name (Optional[str], optional): Friendly task name. Defaults to None.
            lock (Optional[str], optional): Lock key to prevent multiple instances. Defaults to None.
            visibility (VisibilityType, optional): Task status visibility. Defaults to "public".

        Returns:
            TrackableTask: Task tracker object
        """
        return TrackableTask(
            task_redis=self.task_redis,
            lock_redis=self.lock_redis,
            user=self.user,
            func=func,
            name=name,
            lock=lock,
            visibility=visibility,
        )

    def http_create(
        self,
        func: Callable,
        name: Optional[str] = None,
        lock: Optional[str] = None,
        visibility: VisibilityType = "public",
    ) -> TrackableTask:
        """
        Create, track, and start a new background task, returning HTTP exceptions
        if the task cannot be launched. Mostly used if you need to create a
        background task from within a router function.

        Args:
            func (Callable): Function to wrap and run in the background
            name (Optional[str], optional): Friendly task name. Defaults to None.
            lock (Optional[str], optional): Lock key to prevent multiple instances. Defaults to None.
            visibility (VisibilityType, optional): Task status visibility. Defaults to "public".

        Returns:
            TrackableTask: Task tracker object
        """
        try:
            return self.create(func, name=name, lock=lock, visibility=visibility)
        except TaskLockError as e:
            raise HTTPException(
                status_code=409,
                detail=str(e),
            ) from e
