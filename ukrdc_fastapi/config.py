from typing import Optional

from pydantic import BaseSettings


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

    @property
    def version(self) -> str:
        """Generate a short version string for documentation

        Returns:
            str: Version, in the form ref/sha
        """
        prefix: str = self.github_ref.split("/")[-1] if self.github_ref else "dev"
        postfix: str = self.github_sha[0:7] if self.github_sha else "dev"
        return f"{prefix}/{postfix}"


class Settings(BaseSettings):
    # Application name used in database connections
    application_name: str = "ukrdc_fastapi"

    # Optional debug mode
    debug: bool = False

    # Optionally skip data caching on startup
    skip_cache: bool = False

    # Messages to display on user dashboards
    motd: list[str] = []
    # Warnings to display on user dashboards
    wotd: list[str] = []

    # Redis cache expiry
    cache_channel_seconds: int = 86400
    cache_groups_seconds: int = 86400
    cache_statistics_seconds: int = 3600
    cache_dashboard_seconds: int = 900

    swagger_client_id: str = ""
    app_client_id: str = ""
    oauth_issuer: str = "https://renalregistry.okta.com/oauth2/ausn7fa9zfh1DC2La5d6"
    oauth_audience: str = "api://ukrdc"

    mirth_url: str = "http://localhost:9004"
    mirth_user: str = "webapi"
    mirth_pass: str = "****"
    mirth_verify_ssl: bool = True

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

    allow_origins: list[str] = []

    class Config:
        env_file = ".env"


settings = Settings()
configuration = Configuration()
