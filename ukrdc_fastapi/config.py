from pydantic import BaseSettings


class Settings(BaseSettings):
    secret_key: str = "changeme"
    mirth_url: str = "http://localhost:9004"

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

    crowd_url: str = "https://crowd.renalregistry.nhs.uk/crowd"
    crowd_name: str = "ukrdc-user-api"
    crowd_pass: str = "****"


settings = Settings()
