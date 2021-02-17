from fastapi import FastAPI

from ukrdc_fastapi.routers import laborders, records, workitems

app = FastAPI()


app.include_router(laborders.router, prefix="/laborders")
app.include_router(records.router, prefix="/records")
app.include_router(workitems.router, prefix="/workitems")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
