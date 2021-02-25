from fastapi import Depends, FastAPI
from fastapi_hypermodel import HyperModel
from fastapi_pagination import pagination_params
from starlette.responses import RedirectResponse

from ukrdc_fastapi.routers import (
    errors,
    laborders,
    linkrecords,
    records,
    resultitems,
    search,
    workitems,
)

app = FastAPI(
    title="UKRDC API v2",
    description="Early test version of an updated, simpler UKRDC API",
    version="0.0.0",
    dependencies=[Depends(pagination_params)],
)

HyperModel.init_app(app)


@app.get("/", include_in_schema=False)
def root():
    """Redirect to documentation"""
    return RedirectResponse(url="/docs")


app.include_router(laborders.router, prefix="/laborders", tags=["Lab Orders"])
app.include_router(records.router, prefix="/records", tags=["Patient Records"])
app.include_router(workitems.router, prefix="/workitems", tags=["Work Items"])
app.include_router(linkrecords.router, prefix="/linkrecords", tags=["Link Records"])
app.include_router(errors.router, prefix="/errors", tags=["Errors"])
app.include_router(resultitems.router, prefix="/resultitems", tags=["Result Items"])
app.include_router(search.router, prefix="/search", tags=["Search"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
