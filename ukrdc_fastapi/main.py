import logging
import re

import redis
import sqlalchemy
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.routing import APIRoute
from fastapi_pagination import add_pagination
from httpx import ConnectError
from mirth_client import MirthAPI
from mirth_client.models import LoginResponse

from ukrdc_fastapi.config import configuration, settings
from ukrdc_fastapi.dependencies import get_redis
from ukrdc_fastapi.dependencies.auth import auth
from ukrdc_fastapi.dependencies.database import ukrdc3_session
from ukrdc_fastapi.dependencies.mirth import mirth_session
from ukrdc_fastapi.dependencies.sentry import add_sentry
from ukrdc_fastapi.exceptions import ResourceNotFoundError
from ukrdc_fastapi.routers import api
from ukrdc_fastapi.tasks import repeated, shutdown


# Create app
def _custom_generate_unique_id(route: APIRoute):
    """
    Custom unique route ID function.
    We use this to simplify the function names of our generated client libraries
    """
    operation_id = route.name
    operation_id = re.sub("[^0-9a-zA-Z_]", "_", operation_id)
    operation_id = list(route.methods)[0].lower() + "_" + operation_id
    return operation_id


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
    generate_unique_id_function=_custom_generate_unique_id,
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
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_sentry(app)
add_pagination(app)

# Add custom exception handlers


@app.exception_handler(ResourceNotFoundError)
async def http_exception_handler(_, exc):
    """Handle missing resources with a 404 response"""
    return PlainTextResponse(str(exc), status_code=404)


# Attach event handlers

# Async startup functions and event handlers
app.router.add_event_handler("startup", repeated.update_channel_id_name_map)
app.router.add_event_handler("startup", repeated.update_facilities_list)
app.router.add_event_handler("startup", repeated.precalculate_facility_stats_dialysis)

# Async shutdown functions and event handler
app.router.add_event_handler("shutdown", shutdown.clear_task_tracker)


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
