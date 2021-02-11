from fastapi import FastAPI

from ukrdc_fastapi.routers import viewer

app = FastAPI()


@app.get("/")
def read_root():
    return {"msg": "Hello World"}


app.include_router(viewer.router, prefix="/viewer")
