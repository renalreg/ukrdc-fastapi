from fastapi import Depends, FastAPI, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi_hypermodel import HyperModel
from fastapi_pagination import pagination_params
from starlette.responses import RedirectResponse

from ukrdc_fastapi.auth import auth
from ukrdc_fastapi.routers import (
    dashboard,
    empi,
    errors,
    laborders,
    patientrecords,
    resultitems,
)

app = FastAPI(
    title="UKRDC API v2",
    description="Early test version of an updated, simpler UKRDC API",
    version="0.0.0",
    dependencies=[Depends(pagination_params), Depends(auth.implicit_scheme)],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HyperModel.init_app(app)


@app.get("/", include_in_schema=False)
def root():
    """Redirect to documentation"""
    return RedirectResponse(url="/docs")


app.include_router(dashboard.router, prefix="/dash")
app.include_router(empi.router, prefix="/empi")
app.include_router(
    patientrecords.router, prefix="/patientrecords", tags=["Patient Records"]
)
app.include_router(laborders.router, prefix="/laborders", tags=["Lab Orders"])
app.include_router(errors.router, prefix="/errors", tags=["Errors"])
app.include_router(resultitems.router, prefix="/resultitems", tags=["Result Items"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
