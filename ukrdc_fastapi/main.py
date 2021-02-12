from fastapi import FastAPI

from ukrdc_fastapi.routers import viewer

app = FastAPI()


app.include_router(viewer.router, prefix="/viewer")
