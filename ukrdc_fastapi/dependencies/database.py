import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.utils import build_db_uri

Ukrdc3Session = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=create_engine(
        build_db_uri(
            settings.ukrdc_driver,
            settings.ukrdc_host,
            settings.ukrdc_port,
            settings.ukrdc_user,
            settings.ukrdc_pass,
            settings.ukrdc_name,
        ),
        connect_args={"application_name": settings.application_name},
    ),
)


@contextmanager
def ukrdc3_session() -> Generator[Session, None, None]:
    """Yeild a new UKRDC3 database session

    Yields:
        [Session]: UKRDC3 database session
    """
    session = Ukrdc3Session()
    try:
        yield session
    finally:
        session.close()


JtraceSession = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=create_engine(
        build_db_uri(
            settings.jtrace_driver,
            settings.jtrace_host,
            settings.jtrace_port,
            settings.jtrace_user,
            settings.jtrace_pass,
            settings.jtrace_name,
        ),
        connect_args={"application_name": settings.application_name},
    ),
)


@contextmanager
def jtrace_session() -> Generator[Session, None, None]:
    """Yeild a new JTRACE database session

    Yields:
        [Session]: JTRACE database session
    """
    session = JtraceSession()
    try:
        yield session
    finally:
        session.close()


ErrorsSession = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=create_engine(
        build_db_uri(
            settings.errors_driver,
            settings.errors_host,
            settings.errors_port,
            settings.errors_user,
            settings.errors_pass,
            settings.errors_name,
        ),
        connect_args={"application_name": settings.application_name},
    ),
)


@contextmanager
def errors_session() -> Generator[Session, None, None]:
    """Yeild a new ERRORSDB database session

    Yields:
        [Session]: ERRORSDB database session
    """
    session = ErrorsSession()
    try:
        yield session
    finally:
        session.close()


StatsSession = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=create_engine(
        build_db_uri(
            settings.stats_driver,
            settings.stats_host,
            settings.stats_port,
            settings.stats_user,
            settings.stats_pass,
            settings.stats_name,
        ),
        connect_args={"application_name": settings.application_name},
    ),
)


@contextmanager
def stats_session() -> Generator[Session, None, None]:
    """Yeild a new STATSDB database session

    Yields:
        [Session]: STATSDB database session
    """
    session = StatsSession()
    try:
        yield session
    finally:
        session.close()


AuditSession = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=create_engine(
        build_db_uri(
            settings.audit_driver,
            settings.audit_host,
            settings.audit_port,
            settings.audit_user,
            settings.audit_pass,
            settings.audit_name,
        ),
        connect_args={"application_name": settings.application_name},
    ),
)


@contextmanager
def audit_session() -> Generator[Session, None, None]:
    """Yeild a new AUDITDB database session

    Yields:
        [Session]: AUDITDB database session
    """
    session = AuditSession()
    try:
        yield session
    finally:
        session.close()


UsersSession = sessionmaker(
    bind=create_engine(
        build_db_uri(
            "sqlite", name=os.path.join(settings.sqlite_data_dir, settings.usersdb_name)
        ),
        connect_args={"check_same_thread": False},
    )
)


@contextmanager
def users_session() -> Generator[Session, None, None]:
    """Yeild a new Users database session

    Yields:
        [Session]: Users database session
    """
    session = UsersSession()
    try:
        yield session
    finally:
        session.close()
