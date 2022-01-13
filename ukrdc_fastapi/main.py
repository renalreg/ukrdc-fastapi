import logging

import redis
import sqlalchemy
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_hypermodel import HyperModel
from fastapi_pagination import add_pagination
from httpx import ConnectError
from mirth_client import MirthAPI
from mirth_client.models import LoginResponse

from ukrdc_fastapi import tasks
from ukrdc_fastapi.config import configuration, settings
from ukrdc_fastapi.dependencies import get_redis
from ukrdc_fastapi.dependencies.auth import auth
from ukrdc_fastapi.dependencies.database import ukrdc3_session
from ukrdc_fastapi.dependencies.mirth import mirth_session
from ukrdc_fastapi.dependencies.sentry import add_sentry
from ukrdc_fastapi.routers import api

# Create app


app = FastAPI(
    title="UKRDC API",
    description="Early test version of an updated, simpler UKRDC API",
    version=configuration.version,
    openapi_url=f"{configuration.base_url}/openapi.json",
    docs_url=f"{configuration.base_url}/docs",
    redoc_url=f"{configuration.base_url}/redoc",
    swagger_ui_oauth2_redirect_url=f"{configuration.base_url}/docs/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": settings.swagger_client_id,
        "scopes": ["openid", "profile", "email", "offline_access"],
    },
)

# Add routes

app.include_router(
    api.router,
    prefix=configuration.base_url,
    dependencies=[Depends(auth.okta_jwt_scheme)],
)

# Add middlewares

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_sentry(app)
add_pagination(app)
HyperModel.init_app(app)

# Attach event handlers

if not settings.skip_cache:
    app.router.add_event_handler("startup", tasks.cache_mirth_channel_info)
    app.router.add_event_handler("startup", tasks.cache_mirth_channel_groups)
    app.router.add_event_handler("startup", tasks.cache_mirth_channel_statistics)
else:
    logging.warning("Skipping cache startup tasks")


class StartupError(RuntimeError):
    pass


# @app.on_event("startup")
async def check_connections():
    """
    Check Mirth, database, and Redis connections
    """
    logging.info("Checking connection to Mirth API...")
    mirth_api: MirthAPI
    async with mirth_session() as mirth_api:
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
                f"Unable to connect to Mirth API at {settings.mirth_url}. Ensure connection is properly configured."
            ) from e

    logging.info("Checking connection to UKRDC database...")
    with ukrdc3_session() as ukrdc3:
        try:
            ukrdc3.connection()
        except sqlalchemy.exc.OperationalError as e:
            raise StartupError(
                "Unable to connect to UKRDC database. Ensure connection is properly configured."
            ) from e

    logging.info("Checking connection to Redis database...")
    try:
        get_redis().ping()
    except redis.exceptions.ConnectionError as e:
        raise StartupError(
            "Unable to connect to Redis instance. Ensure redis-server is running locally."
        ) from e


# Run app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
