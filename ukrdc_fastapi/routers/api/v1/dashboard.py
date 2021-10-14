from typing import Optional

from fastapi import APIRouter, Depends, Security
from pydantic import BaseModel
from redis import Redis
from sqlalchemy.orm import Session

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_jtrace, get_redis
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.dashboard import (
    UKRDCRecordsDashSchema,
    WorkItemsDashSchema,
    get_empi_stats,
    get_workitems_stats,
)

router = APIRouter(tags=["Dashboard"])


class DashboardSchema(BaseModel):
    messages: list[str]
    warnings: list[str]
    workitems: Optional[WorkItemsDashSchema] = None
    ukrdcrecords: Optional[UKRDCRecordsDashSchema] = None


@router.get("/", response_model=DashboardSchema)
def dashboard(
    refresh: bool = False,
    jtrace: Session = Depends(get_jtrace),
    redis: Redis = Depends(get_redis),
    user: UKRDCUser = Security(auth.get_user()),
):
    """Retreive basic statistics about recent records"""
    dash = DashboardSchema(messages=settings.motd, warnings=settings.wotd)

    units = Permissions.unit_codes(user.permissions)

    # Admin statistics
    if Permissions.UNIT_WILDCARD in units:
        dash.workitems = get_workitems_stats(jtrace, redis, refresh=refresh)
        dash.ukrdcrecords = get_empi_stats(jtrace, redis, refresh=refresh)

    return dash
