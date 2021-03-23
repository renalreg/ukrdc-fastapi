from typing import AsyncGenerator, Generator

import redis
from fastapi import HTTPException
from mirth_client import MirthAPI
from mirth_client.exceptions import MirthLoginError
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from .config import settings
from .database import ErrorsSession, JtraceSession, Ukrdc3Session

JTRACE_FRIENDLY_ERROR_CODES = {"e3q8": "Error connecting to JTRACE database."}
UKRDC3_FRIENDLY_ERROR_CODES = {"e3q8": "Error connecting to UKRDC3 database."}
ERRORS_FRIENDLY_ERROR_CODES = {"e3q8": "Error connecting to ERRORSDB database."}


async def get_mirth() -> AsyncGenerator[MirthAPI, None]:
    """Connect, login to, and yeild a new MirthAPI session

    Yields:
        [MirthAPI]: MirthAPI session
    """
    async with MirthAPI(
        settings.mirth_url, verify_ssl=settings.mirth_verify_ssl
    ) as api:
        try:
            await api.login(settings.mirth_user, settings.mirth_pass)
        except MirthLoginError as e:
            raise HTTPException(
                500,
                detail="Unable to authenticate with Mirth instance",
            ) from e
        else:
            yield api


def get_ukrdc3() -> Generator[Session, None, None]:
    """Yeild a new UKRDC3 database session

    Yields:
        [Session]: UKRDC3 database session
    """
    session = Ukrdc3Session()
    try:
        yield session
    except OperationalError as e:
        raise HTTPException(
            500,
            detail=UKRDC3_FRIENDLY_ERROR_CODES.get(
                e.code or "unknown", "UKRDC3 Operational Error"
            ),
        ) from e
    finally:
        session.close()


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


def get_jtrace() -> Generator[Session, None, None]:
    """Yeild a new JTRACE database session

    Yields:
        Generator[Session]: JTRACE database session
    """
    session = JtraceSession()
    try:
        yield session
    except OperationalError as e:
        raise HTTPException(
            500,
            detail=JTRACE_FRIENDLY_ERROR_CODES.get(
                e.code or "unknown", "JTRACE Operational Error"
            ),
        ) from e
    finally:
        session.close()


def get_errorsdb() -> Generator[Session, None, None]:
    """Yeild a new errorsdb database session

    Yields:
        Generator[Session]: errorsdb database session
    """
    session = ErrorsSession()
    try:
        yield session
    except OperationalError as e:
        raise HTTPException(
            500,
            detail=ERRORS_FRIENDLY_ERROR_CODES.get(
                e.code or "unknown", "ERRORSDB Operational Error"
            ),
        ) from e
    finally:
        session.close()


# def get_mirth() -> MirthConnection:
#    """Returns a new Mirth API connection"""
#    return MirthConnection(settings.mirth_url)
