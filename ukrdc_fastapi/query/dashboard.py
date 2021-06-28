from fastapi_hypermodel import HyperModel, UrlFor
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord, WorkItem

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.utils.statistics import TotalDayPrev, total_day_prev


class _DayPrevTotalSchema(HyperModel):
    total: int
    day: int
    prev: int


class WorkItemsDashSchema(_DayPrevTotalSchema):
    href = UrlFor("workitems_list")


class UKRDCRecordsDashSchema(_DayPrevTotalSchema):
    href = UrlFor("master_records")


def get_workitems_stats(jtrace: Session, redis: Redis, refresh: bool = False):
    if redis.exists("dashboard:workitems") and not refresh:
        return WorkItemsDashSchema(**redis.hgetall("dashboard:workitems"))

    open_workitems_stats: TotalDayPrev = total_day_prev(
        jtrace.query(WorkItem).filter(WorkItem.status == 1),
        WorkItem,
        "last_updated",
    )
    workitems = WorkItemsDashSchema(**open_workitems_stats.dict())
    redis.hset("dashboard:workitems", mapping=open_workitems_stats.dict())  # type: ignore
    redis.expire("dashboard:workitems", settings.cache_dashboard_seconds)
    return workitems


def get_empi_stats(jtrace: Session, redis: Redis, refresh: bool = False):
    if redis.exists("dashboard:ukrdcrecords") and not refresh:
        return UKRDCRecordsDashSchema(**redis.hgetall("dashboard:ukrdcrecords"))

    ukrdc_masterrecords_stats: TotalDayPrev = total_day_prev(
        jtrace.query(MasterRecord).filter(MasterRecord.nationalid_type == "UKRDC"),
        MasterRecord,
        "creation_date",
    )
    ukrdcrecords = UKRDCRecordsDashSchema(**ukrdc_masterrecords_stats.dict())
    redis.hset("dashboard:ukrdcrecords", mapping=ukrdc_masterrecords_stats.dict())  # type: ignore
    redis.expire("dashboard:ukrdcrecords", settings.cache_dashboard_seconds)
    return ukrdcrecords
