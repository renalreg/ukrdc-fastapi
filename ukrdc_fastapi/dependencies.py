from typing import Generator

from sqlalchemy.orm import Session

from .database import JtraceSession, Ukrdc3Session


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
