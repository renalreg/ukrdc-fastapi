from typing import Optional

from pydantic import BaseSettings


class Configuration(BaseSettings):
    # Built-time configuration, designed to be read-only

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

    # Used to correct linking when behind a reverse proxy
    api_base: str = "/api"

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

    user_permission_key: str = "org.ukrdc.permissions"

    mirth_url: str = "http://localhost:9004"
    mirth_user: str = "webapi"
    mirth_pass: str = "****"
    mirth_verify_ssl: bool = True

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

    class Config:
        env_file = ".env"


settings = Settings()
configuration = Configuration()
