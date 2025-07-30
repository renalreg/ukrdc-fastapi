from typing import Optional

from pydantic import BaseSettings

from . import __version__ as package_ver


class Configuration(BaseSettings):
    # Built-time configuration, designed to be read-only

    # Used to correct linking when behind a reverse proxy
    base_url: str = "/api"

    # Deployment environment, used for error logging etc
    deployment_env: str = "development"

    # Sentry
    sentry_dsn: Optional[str] = None

    # Build
    github_sha: Optional[str] = None
    github_ref: Optional[str] = None

    # Package info
    version: str = package_ver or "0.0.0-dev"


class Settings(BaseSettings):
    # Application name used in database connections
    application_name: str = "ukrdc_fastapi"

    # Optional debug mode
    debug: bool = False

    # Messages to display on user dashboards
    motd: list[str] = []
    # Warnings to display on user dashboards
    wotd: list[str] = []

    # Redis cache expiries

    cache_mirth_channel_seconds: int = 86400
    cache_mirth_groups_seconds: int = 86400
    cache_mirth_statistics_seconds: int = 3600

    cache_facilities_list_seconds: int = 3600
    cache_facilities_stats_demographics_seconds: int = 28800
    cache_facilities_stats_dialysis_seconds: int = 28800

    # Minimum number of records required to pre-cache facility dialysis stats
    cache_facilities_stats_dialysis_min: int = 1

    # Authentication settings

    swagger_client_id: str = ""
    app_client_id: str = ""
    oauth_issuer: str = "https://sso.ukkidney.org/oauth2/ausn7fa9zfh1DC2La5d6"
    oauth_audience: str = "api://ukrdc"

    # Mirth settings

    mirth_url: str = "http://localhost:9004"
    mirth_user: str = "webapi"
    mirth_pass: str = "****"
    mirth_verify_ssl: bool = True

    # Redis settings

    redis_host: str = "localhost"
    redis_port: int = 6379

    # Database for Redis caching
    redis_db: int = 0

    # Database for Redis task tracking
    redis_tasks_db: int = 1
    redis_locks_db: int = 2

    redis_tasks_expire: int = 86400
    redis_tasks_expire_error: int = 259200
    redis_tasks_expire_lock: int = 60

    # SQLite databases
    sqlite_data_dir: str = "./data"
    usersdb_name: str = "users.sqlite"

    # Database connections

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

    stats_host: str = "localhost"
    stats_port: int = 5432
    stats_user: str = "ukrdc"
    stats_pass: str = "****"
    stats_name: str = "statsdb"
    stats_driver: str = "postgresql+psycopg2"

    audit_host: str = "localhost"
    audit_port: int = 5432
    audit_user: str = "ukrdc"
    audit_pass: str = "****"
    audit_name: str = "auditdb"
    audit_driver: str = "postgresql+psycopg2"

    # CORS settings

    allow_origins: list[str] = [
        "http://host.docker.internal:3000",
        "http://localhost:3000",
        "http://ukrdc-nuxt-3:3000",
    ]

    class Config:
        env_file = ".env"


settings = Settings()
configuration = Configuration()
