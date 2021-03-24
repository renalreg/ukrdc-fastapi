import logging
from typing import Dict, List

from fastapi import Depends, FastAPI, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi_hypermodel import HyperModel
from fastapi_pagination import pagination_params
from mirth_client import MirthAPI
from mirth_client.channels import Channel
from mirth_client.models import LoginResponse

from ukrdc_fastapi.auth import auth
from ukrdc_fastapi.config import settings
from ukrdc_fastapi.routers import api

app = FastAPI(
    title="UKRDC API v2",
    description="Early test version of an updated, simpler UKRDC API",
    version="0.0.0",
    dependencies=[Depends(pagination_params), Depends(auth.implicit_scheme)],
    openapi_url=f"{settings.api_base.rstrip('/')}/openapi.json",
    docs_url=f"{settings.api_base.rstrip('/')}/docs",
    redoc_url=f"{settings.api_base.rstrip('/')}/redoc",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": settings.swagger_client_id,
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HyperModel.init_app(app)


app.include_router(
    api.router,
    prefix=settings.api_base,
    dependencies=[Security(auth.get_user)],
)


@app.on_event("startup")
async def startup_event():
    """
    Check Mirth credentials and that all expected Mirth channels are available
    """
    mirth_api: MirthAPI
    async with MirthAPI(
        settings.mirth_url, verify_ssl=settings.mirth_verify_ssl
    ) as mirth_api:
        # Check we can log in to Mirth
        login_response: LoginResponse = await mirth_api.login(
            settings.mirth_user, settings.mirth_pass
        )
        logging.debug(login_response)
        if login_response.status != "SUCCESS":
            raise RuntimeError("Unable to authenticate with Mirth")
        # Check each channel we use
        available_channels: List[Channel] = await mirth_api.get_channels()
        available_channel_map: Dict[str, Channel] = {
            channel.id: channel for channel in available_channels
        }
        logging.debug("Available channels:")
        for channel in available_channels:
            logging.debug("%s: %s", channel.name, channel.id)
        for id_ in settings.mirth_channel_map.values():
            if id_ not in available_channel_map:
                raise RuntimeError(f"Channel {id_} not found in Mirth instance")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
