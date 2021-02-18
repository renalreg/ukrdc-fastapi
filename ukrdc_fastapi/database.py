from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .utils import build_db_uri

print(settings.jtrace_pass)

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
