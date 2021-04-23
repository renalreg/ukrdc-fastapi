from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
        )
    ),
)

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
        )
    ),
)

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
        )
    ),
)
