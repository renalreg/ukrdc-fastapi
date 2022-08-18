from fastapi import APIRouter
from pydantic import BaseModel

from ukrdc_fastapi.config import settings

router = APIRouter(tags=["Dashboard"])


class DashboardSchema(BaseModel):
    messages: list[str]
    warnings: list[str]


@router.get("", response_model=DashboardSchema)
def dashboard():
    """Retreive basic statistics about recent records"""
    dash = DashboardSchema(messages=settings.motd, warnings=settings.wotd)
    return dash
