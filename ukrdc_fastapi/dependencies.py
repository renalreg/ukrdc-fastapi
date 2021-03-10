from typing import Generator

from sqlalchemy.orm import Session

from .config import settings
from .database import ErrorsSession, JtraceSession, Ukrdc3Session
from .mirth import MirthConnection


def get_ukrdc3() -> Generator[Session, None, None]:
    """Yeild a new UKRDC3 database session

    Yields:
        [Session]: UKRDC3 database session
    """
    session = Ukrdc3Session()
    try:
        yield session
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
    finally:
        session.close()


def get_mirth() -> MirthConnection:
    """Returns a new Mirth API connection"""
    return MirthConnection(settings.mirth_url)
