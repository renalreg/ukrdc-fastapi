import logging

import sentry_sdk
from fastapi import FastAPI
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from ukrdc_fastapi.config import configuration


def add_sentry(app: FastAPI):
    """Configure and initialise the Sentry API, if a DSN is available

    Args:
        app (FastAPI): App to attach Sentry to
    """
    if configuration.sentry_dsn:
        logging.warning("Sentry reporting is enabled")
        sentry_sdk.init(  # pylint: disable=abstract-class-instantiated
            dsn=configuration.sentry_dsn,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(transaction_style="endpoint"),
                RedisIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=1.0,
            environment=configuration.deployment_env,
            release=configuration.github_sha,
            profiles_sample_rate=1.0,
        )
        app.add_middleware(SentryAsgiMiddleware)
    else:
        logging.warning("No Sentry DSN found. Sentry reporting disabled.")
