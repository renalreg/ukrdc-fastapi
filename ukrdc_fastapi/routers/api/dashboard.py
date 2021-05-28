import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from fastapi_hypermodel import HyperModel, UrlFor
from mirth_client.models import ChannelStatistics
from pydantic import BaseModel
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord, WorkItem

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_jtrace, get_redis
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.utils.statistics import TotalDayPrev, total_day_prev

router = APIRouter(tags=["Summary Dashboard"])


class ChannelDashStatisticsSchema(ChannelStatistics):
    name: Optional[str]
    updated: Optional[datetime.datetime]


class _DayPrevTotalSchema(HyperModel):
    total: int
    day: int
    prev: int


class WorkItemsDashSchema(_DayPrevTotalSchema):
    href = UrlFor("workitems_list")


class UKRDCRecordsDashSchema(_DayPrevTotalSchema):
    href = UrlFor("master_records")


class DashboardSchema(BaseModel):
    messages: list[str]
    warnings: list[str]
    workitems: Optional[WorkItemsDashSchema] = None
    ukrdcrecords: Optional[UKRDCRecordsDashSchema] = None


def _get_workitems_stats(jtrace: Session, redis: Redis, refresh: bool = False):
    if redis.exists("dashboard:workitems") and not refresh:
        return WorkItemsDashSchema(**redis.hgetall("dashboard:workitems"))
    else:
        open_workitems_stats: TotalDayPrev = total_day_prev(
            jtrace.query(WorkItem).filter(WorkItem.status == 1),
            WorkItem,
            "last_updated",
        ).dict()
        workitems = WorkItemsDashSchema(**open_workitems_stats)
        redis.hset("dashboard:workitems", mapping=open_workitems_stats)  # type: ignore
        # Remove cached statistics after 15 minutes. Next request will re-query
        redis.expire("dashboard:workitems", 900)
        return workitems


def _get_empi_stats(jtrace: Session, redis: Redis, refresh: bool = False):
    if redis.exists("dashboard:ukrdcrecords") and not refresh:
        return UKRDCRecordsDashSchema(**redis.hgetall("dashboard:ukrdcrecords"))
    else:
        ukrdc_masterrecords_stats: TotalDayPrev = total_day_prev(
            jtrace.query(MasterRecord).filter(MasterRecord.nationalid_type == "UKRDC"),
            MasterRecord,
            "creation_date",
        ).dict()
        ukrdcrecords = UKRDCRecordsDashSchema(**ukrdc_masterrecords_stats)
        redis.hset("dashboard:ukrdcrecords", mapping=ukrdc_masterrecords_stats)  # type: ignore
        # Remove cached statistics after 15 minutes. Next request will re-query
        redis.expire("dashboard:ukrdcrecords", 900)
        return ukrdcrecords


@router.get("/", response_model=DashboardSchema)
def dashboard(
    refresh: bool = False,
    jtrace: Session = Depends(get_jtrace),
    redis: Redis = Depends(get_redis),
    user: UKRDCUser = Security(auth.get_user),
):
    """Retreive basic statistics about recent records"""
    dash = DashboardSchema(messages=settings.motd, warnings=settings.wotd)

    units = Permissions.unit_codes(user.permissions)

    # Admin statistics
    if Permissions.UNIT_WILDCARD in units:
        dash.workitems = _get_workitems_stats(jtrace, redis, refresh=refresh)
        dash.ukrdcrecords = _get_empi_stats(jtrace, redis, refresh=refresh)

    return dash
