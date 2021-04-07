import asyncio
import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi_hypermodel import HyperModel, UrlFor
from mirth_client import MirthAPI
from mirth_client.channels import Channel
from mirth_client.models import ChannelStatistics
from pydantic import BaseModel
from redis import Redis
from sqlalchemy.orm import Query, Session
from ukrdc_sqla.empi import Base as EMPIBase
from ukrdc_sqla.empi import MasterRecord, WorkItem

from ukrdc_fastapi.auth import Auth0User, Scopes, Security, auth
from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_jtrace, get_mirth, get_redis

router = APIRouter()


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


def _total_day_prev(query: Query, table: EMPIBase, datefield: str) -> dict[str, int]:
    total_workitems = query.count()
    day_workitems = query.filter(
        getattr(table, datefield)
        > (datetime.datetime.utcnow() - datetime.timedelta(days=1))
    ).count()
    prev_workitems = query.filter(
        getattr(table, datefield)
        > (datetime.datetime.utcnow() - datetime.timedelta(days=2)),
        getattr(table, datefield)
        <= (datetime.datetime.utcnow() - datetime.timedelta(days=1)),
    ).count()
    return {
        "total": total_workitems,
        "day": day_workitems,
        "prev": prev_workitems,
    }


@router.get("/", response_model=DashboardSchema)
def dashboard(
    refresh: bool = False,
    jtrace: Session = Depends(get_jtrace),
    redis: Redis = Depends(get_redis),
    user: Auth0User = Security(auth.get_user),
):
    """Retreive basic statistics about recent records"""
    dash = DashboardSchema(messages=settings.motd, warnings=settings.wotd)

    if Scopes.READ_WORKITEMS in user.permissions:
        # Workitem stats
        if redis.exists("dashboard:workitems") and not refresh:
            dash.workitems = WorkItemsDashSchema(**redis.hgetall("dashboard:workitems"))
        else:
            open_workitems_stats: dict[str, int] = _total_day_prev(
                jtrace.query(WorkItem).filter(WorkItem.status == 1),
                WorkItem,
                "last_updated",
            )
            dash.workitems = WorkItemsDashSchema(**open_workitems_stats)
            redis.hset("dashboard:workitems", mapping=open_workitems_stats)  # type: ignore
            # Remove cached statistics after 15 minutes. Next request will re-query
            redis.expire("dashboard:workitems", 900)

        if redis.exists("dashboard:ukrdcrecords") and not refresh:
            dash.ukrdcrecords = UKRDCRecordsDashSchema(
                **redis.hgetall("dashboard:ukrdcrecords")
            )
        else:
            ukrdc_masterrecords_stats: dict[str, int] = _total_day_prev(
                jtrace.query(MasterRecord).filter(
                    MasterRecord.nationalid_type == "UKRDC"
                ),
                MasterRecord,
                "creation_date",
            )
            dash.ukrdcrecords = UKRDCRecordsDashSchema(**ukrdc_masterrecords_stats)
            redis.hset("dashboard:ukrdcrecords", mapping=ukrdc_masterrecords_stats)  # type: ignore
            # Remove cached statistics after 15 minutes. Next request will re-query
            redis.expire("dashboard:ukrdcrecords", 900)

    return dash


@router.get("/mirth", response_model=list[ChannelDashStatisticsSchema])
async def mirth_dashboard(
    refresh: bool = False,
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_MIRTH]),
):
    """Retreive basic statistics about Mirth channels"""

    dash = []
    coros = []

    for channel_id in settings.mirth_channel_map.values():
        if redis.exists(f"dashboard:mirth:{channel_id}") and not refresh:
            dash.append(redis.hgetall(f"dashboard:mirth:{channel_id}"))
        else:
            coros.append(Channel(mirth, channel_id).get_statistics())

    # Await array of request coroutines
    results: list[ChannelStatistics] = await asyncio.gather(*coros)

    for result in results:
        result_dict = {
            "updated": datetime.datetime.now().timestamp(),
            "name": settings.inverse_mirth_channel_map.get(str(result.channel_id)),
            "serverId": str(result.server_id),
            "channelId": str(result.channel_id),
            "received": result.received,
            "sent": result.sent,
            "error": result.error,
            "filtered": result.filtered,
            "queued": result.queued,
        }
        dash.append(result_dict)
        redis.hset(f"dashboard:mirth:{result.channel_id}", mapping=result_dict)  # type: ignore
        # Remove cached statistics after 15 minutes. Next request will re-query
        redis.expire(f"dashboard:mirth:{result.channel_id}", 900)

    # Insert channel names and return
    return [ChannelDashStatisticsSchema(**item) for item in dash]
