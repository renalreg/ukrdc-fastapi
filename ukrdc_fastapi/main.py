from fastapi import FastAPI
from starlette.responses import RedirectResponse

from ukrdc_fastapi.routers import laborders, records, workitems

app = FastAPI(
    title="UKRDC API v2",
    description="Early test version of an updated, simpler UKRDC API",
    version="0.0.0",
)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


app.include_router(laborders.router, prefix="/laborders", tags=["Lab Orders"])
app.include_router(records.router, prefix="/records", tags=["Patient Records"])
app.include_router(workitems.router, prefix="/workitems", tags=["Work Items"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
