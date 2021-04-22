import logging

import sentry_sdk
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_hypermodel import HyperModel
from fastapi_pagination import add_pagination
from httpx import ConnectError
from mirth_client import MirthAPI
from mirth_client.models import LoginResponse
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from ukrdc_fastapi.auth import Scopes, auth
from ukrdc_fastapi.config import settings
from ukrdc_fastapi.routers import api

if settings.sentry_dsn:
    logging.warning("Sentry reporting is enabled")
    sentry_sdk.init(  # pylint: disable=abstract-class-instantiated
        dsn=settings.sentry_dsn,
        integrations=[RedisIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=1.0,
    )
else:
    logging.warning("No Sentry DSN found. Sentry reporting disabled.")

app = FastAPI(
    title="UKRDC API v2",
    description="Early test version of an updated, simpler UKRDC API",
    version="0.0.0",
    dependencies=[Depends(auth.implicit_scheme)],
    openapi_url=f"{settings.api_base.rstrip('/')}/openapi.json",
    docs_url=f"{settings.api_base.rstrip('/')}/docs",
    redoc_url=f"{settings.api_base.rstrip('/')}/redoc",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": settings.swagger_client_id,
        "scopes": Scopes.all(as_string=True),
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.sentry_dsn:
    app.add_middleware(SentryAsgiMiddleware)


HyperModel.init_app(app)


app.include_router(
    api.router,
    prefix=settings.api_base,
)


class StartupError(RuntimeError):
    pass


@app.on_event("startup")
async def check_connections():
    """
    Check Mirth credentials and that all expected Mirth channels are available
    """
    logging.info("Checking connection to Mirth API...")
    mirth_api: MirthAPI
    async with MirthAPI(
        settings.mirth_url, verify_ssl=settings.mirth_verify_ssl
    ) as mirth_api:
        try:
            # Check we can log in to Mirth
            login_response: LoginResponse = await mirth_api.login(
                settings.mirth_user, settings.mirth_pass
            )
            logging.debug(login_response)
            if login_response.status != "SUCCESS":
                raise RuntimeError("Unable to authenticate with Mirth")
        except ConnectError as e:
            raise StartupError(
                "Unable to connect to Mirth API. Ensure connection is properly configured."
            ) from e


# Add pagination parameters automatically to API views that need it
add_pagination(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
