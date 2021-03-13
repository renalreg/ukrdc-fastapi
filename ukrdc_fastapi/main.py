from fastapi import Depends, FastAPI, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi_hypermodel import HyperModel
from fastapi_pagination import pagination_params

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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
