from typing import AsyncGenerator, Generator

import redis
from mirth_client import MirthAPI
from sqlalchemy.orm import Session

from ukrdc_fastapi.config import settings

from .database import errors_session, jtrace_session, stats_session, ukrdc3_session
from .mirth import mirth_session

JTRACE_FRIENDLY_ERROR_CODES = {"e3q8": "Error connecting to JTRACE database."}
UKRDC3_FRIENDLY_ERROR_CODES = {"e3q8": "Error connecting to UKRDC3 database."}
ERRORS_FRIENDLY_ERROR_CODES = {"e3q8": "Error connecting to ERRORSDB database."}


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


def get_statssdb() -> Generator[Session, None, None]:
    """Yeild a new statsdb database session

    Yields:
        Generator[Session]: statsdb database session
    """
    with stats_session() as statsdb:
        yield statsdb


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
