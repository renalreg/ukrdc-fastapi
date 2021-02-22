from fastapi import Depends, FastAPI
from fastapi_pagination import pagination_params
from starlette.responses import RedirectResponse

from ukrdc_fastapi.routers import errors, laborders, linkrecords, records, workitems

app = FastAPI(
    title="UKRDC API v2",
    description="Early test version of an updated, simpler UKRDC API",
    version="0.0.0",
    dependencies=[Depends(pagination_params)],
)


@app.get("/", include_in_schema=False)
def root():
    """Redirect to documentation"""
    return RedirectResponse(url="/docs")


app.include_router(laborders.router, prefix="/laborders", tags=["Lab Orders"])
app.include_router(records.router, prefix="/records", tags=["Patient Records"])
app.include_router(workitems.router, prefix="/workitems", tags=["Work Items"])
app.include_router(linkrecords.router, prefix="/linkrecords", tags=["Link Records"])
app.include_router(errors.router, prefix="/errors", tags=["Errors"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
