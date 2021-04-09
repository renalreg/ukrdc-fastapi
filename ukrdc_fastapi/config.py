from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    # Used to correct linking when behind a reverse proxy
    api_base: str = "/api"

    # Messages to display on user dashboards
    motd: list[str] = []
    # Warnings to display on user dashboards
    wotd: list[str] = []

    secret_key: str = "****"

    swagger_client_id: str = ""

    sentry_dsn: Optional[str] = None

    mirth_url: str = "http://localhost:9004"
    mirth_user: str = "webapi"
    mirth_pass: str = "****"
    mirth_verify_ssl: bool = True

    # Commonly used mirth channels, so we can quickly access by name
    mirth_channel_map: dict[str, str] = {
        "WorkItemUpdate": "ddc63fed-6684-4436-835c-85116a14da97",
        "Unlink": "3c8b493e-bf6b-405c-86c7-a29882a70cf9",
        "Merge Patient": "bcb9afca-e53a-427f-8415-741a296faf46",
        "PV Feed Inbound": "3cdefad2-bf10-49ee-81c9-8ac6fd2fed67",
        "PV Big Feed Inbound": "cb9ad04d-0d36-4afd-83c2-66799cb5a264",
        "PV RDA Inbound": "b19eb4ec-910f-42e6-8b77-af87610aedef",
        "Generic RDA Inbound": "734cb3a0-2b4a-4746-ac2a-f353b5b9f491",
        "PV Outbound": "57f40021-e05e-4308-98ef-8509c2f9d766",
        "RADAR Outbound": "72179b3a-e051-460e-9400-269fb0fe42ed",
    }

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    ukrdc_host: str = "localhost"
    ukrdc_port: int = 5432
    ukrdc_user: str = "ukrdc"
    ukrdc_pass: str = "****"
    ukrdc_name: str = "UKRDC3"
    ukrdc_driver: str = "postgresql+psycopg2"

    jtrace_host: str = "localhost"
    jtrace_port: int = 5432
    jtrace_user: str = "ukrdc"
    jtrace_pass: str = "****"
    jtrace_name: str = "JTRACE"
    jtrace_driver: str = "postgresql+psycopg2"

    errors_host: str = "localhost"
    errors_port: int = 5432
    errors_user: str = "ukrdc"
    errors_pass: str = "****"
    errors_name: str = "errorsdb"
    errors_driver: str = "postgresql+psycopg2"

    allowed_origins: list[str] = []

    @property
    def inverse_mirth_channel_map(self):
        """Returns a dictionary of Mirth channel name values for ID keys"""
        return {value: key for key, value in settings.mirth_channel_map.items()}

    class Config:
        env_file = ".env"


settings = Settings()
