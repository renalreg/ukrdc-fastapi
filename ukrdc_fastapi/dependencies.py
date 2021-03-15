from typing import Generator

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from .config import settings
from .database import ErrorsSession, JtraceSession, Ukrdc3Session
from .mirth import MirthConnection

JTRACE_FRIENDLY_ERROR_CODES = {"e3q8": "Error connecting to JTRACE database."}
UKRDC3_FRIENDLY_ERROR_CODES = {"e3q8": "Error connecting to UKRDC3 database."}
ERRORS_FRIENDLY_ERROR_CODES = {"e3q8": "Error connecting to ERRORSDB database."}


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
            detail=UKRDC3_FRIENDLY_ERROR_CODES.get(e.code, "UKRDC3 Operational Error"),
        ) from e
    finally:
        session.close()


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
            detail=JTRACE_FRIENDLY_ERROR_CODES.get(e.code, "JTRACE Operational Error"),
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
                e.code, "ERRORSDB Operational Error"
            ),
        ) from e
    finally:
        session.close()


def get_mirth() -> MirthConnection:
    """Returns a new Mirth API connection"""
    return MirthConnection(settings.mirth_url)
