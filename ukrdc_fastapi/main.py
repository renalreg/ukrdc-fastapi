import logging
import re

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.routing import APIRoute
from fastapi_pagination import add_pagination

from ukrdc_fastapi.config import configuration, settings
from ukrdc_fastapi.dependencies.auth import auth
from ukrdc_fastapi.dependencies.sentry import add_sentry
from ukrdc_fastapi.exceptions import ResourceNotFoundError
from ukrdc_fastapi.routers import api
from ukrdc_fastapi.tasks import repeated, startup


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

app.openapi_version = "3.0.2"

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


# Run synchronous startup functions
logging.info("Clearing task tracker and locks...")
startup.clear_task_tracker()

# Attach async startup event handlers
logging.info("Starting repeated background tasks...")
app.router.add_event_handler("startup", repeated.update_channel_id_name_map)
app.router.add_event_handler("startup", repeated.update_facilities_list)
app.router.add_event_handler("startup", repeated.precalculate_facility_stats_dialysis)

# Run app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
