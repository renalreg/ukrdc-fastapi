from typing import AsyncGenerator, Generator

import redis
from fastapi import Security
from mirth_client import MirthAPI
from sqlalchemy.orm import Session

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import auth
from ukrdc_fastapi.utils.tasks import TaskTracker

from .database import (
    audit_session,
    errors_session,
    jtrace_session,
    stats_session,
    ukrdc3_session,
    users_session,
)
from .mirth import mirth_session


async def get_mirth() -> AsyncGenerator[MirthAPI, None]:
    """Connect, login to, and yeild a new MirthAPI session

    Yields:
        [MirthAPI]: MirthAPI session
    """
    async with mirth_session() as api:
        yield api


def get_ukrdc3() -> Generator[Session, None, None]:
    """Yeild a new UKRDC3 database session

    Yields:
        [Session]: UKRDC3 database session
    """
    with ukrdc3_session() as ukrdc3:
        yield ukrdc3


def get_jtrace() -> Generator[Session, None, None]:
    """Yeild a new JTRACE database session

    Yields:
        Generator[Session]: JTRACE database session
    """
    with jtrace_session() as jtrace:
        yield jtrace


def get_errorsdb() -> Generator[Session, None, None]:
    """Yeild a new errorsdb database session

    Yields:
        Generator[Session]: errorsdb database session
    """
    with errors_session() as errorsdb:
        yield errorsdb


def get_statsdb() -> Generator[Session, None, None]:
    """Yeild a new statsdb database session

    Yields:
        Generator[Session]: statsdb database session
    """
    with stats_session() as statsdb:
        yield statsdb


def get_auditdb() -> Generator[Session, None, None]:
    """Yeild a new auditdb database session

    Yields:
        Generator[Session]: auditdb database session
    """
    with audit_session() as auditdb:
        yield auditdb


def get_usersdb() -> Generator[Session, None, None]:
    """Yeild a new usersdb database session

    Yields:
        Generator[Session]: usersdb database session
    """
    with users_session() as usersdb:
        yield usersdb


def get_redis() -> redis.Redis:
    """Return a new Redis database session

    Returns:
        redis.Redis: Redis database session
    """
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=True,
    )


def get_task_tracker(
    user: auth.UKRDCUser = Security(auth.auth.get_user()),
) -> TaskTracker:
    """Creates a TaskTracker pre-populated with a User and Redis session"""
    return TaskTracker(
        redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_tasks_db,
            decode_responses=True,
        ),
        redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_locks_db,
        ),
        user,
    )


def get_root_task_tracker() -> TaskTracker:
    """Creates a TaskTracker pre-populated with a SuperUser and Redis session"""
    return TaskTracker(
        redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_tasks_db,
            decode_responses=True,
        ),
        redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_locks_db,
        ),
        auth.auth.superuser,
    )
