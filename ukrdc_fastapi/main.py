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

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_redis
from ukrdc_fastapi.dependencies.auth import auth
from ukrdc_fastapi.dependencies.database import Ukrdc3Session
from ukrdc_fastapi.dependencies.sentry import add_sentry
from ukrdc_fastapi.routers import api
from ukrdc_fastapi.tasks import cache_all_facilities, cache_dash_stats

# Create app


app = FastAPI(
    title="UKRDC API v2",
    description="Early test version of an updated, simpler UKRDC API",
    version="0.0.0",
    dependencies=[Depends(auth.oidc_scheme)],
    openapi_url=f"{settings.api_base.rstrip('/')}/openapi.json",
    docs_url=f"{settings.api_base.rstrip('/')}/docs",
    redoc_url=f"{settings.api_base.rstrip('/')}/redoc",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": settings.swagger_client_id,
        "additionalQueryStringParams": {"nonce": "132456"},
        "scopes": ["openid", "profile", "email", "offline_access"],
    },
)


# Add routes

app.include_router(
    api.router,
    prefix=settings.api_base,
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

app.router.add_event_handler("startup", cache_dash_stats)
app.router.add_event_handler("startup", cache_all_facilities)


class StartupError(RuntimeError):
    pass


@app.on_event("startup")
async def check_connections():
    """
    Check Mirth, database, and Redis connections
    """
    logging.info("Checking connection to Mirth API...")
    mirth_api: MirthAPI
    async with MirthAPI(
        settings.mirth_url, verify_ssl=settings.mirth_verify_ssl, timeout=None
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

    logging.info("Checking connection to UKRDC database...")
    try:
        Ukrdc3Session().connection()
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

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
