import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Security
from fastapi_auth0 import Auth0User
from fastapi_hypermodel import HyperModel, UrlFor
from pydantic import BaseModel
from redis import Redis
from sqlalchemy.orm import Query, Session
from ukrdc_sqla.empi import Base as EMPIBase
from ukrdc_sqla.empi import MasterRecord, WorkItem

from ukrdc_fastapi.auth import auth
from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_jtrace, get_redis

router = APIRouter()


class UserSchema(BaseModel):
    permissions: Optional[List[str]]
    email: Optional[str]


class _DayPrevTotalSchema(HyperModel):
    total: int
    day: int
    prev: int


class WorkItemsDashSchema(_DayPrevTotalSchema):
    href = UrlFor("workitems_list")


class UKRDCRecordsDashSchema(_DayPrevTotalSchema):
    href = UrlFor("master_records")


class DashboardSchema(BaseModel):
    message: Optional[str]
    user: UserSchema
    workitems: WorkItemsDashSchema
    ukrdcrecords: UKRDCRecordsDashSchema


def _total_day_prev(query: Query, table: EMPIBase, datefield: str) -> Dict[str, int]:
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
    user: Auth0User = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    redis: Redis = Depends(get_redis),
):
    """Retreive basic statistics about recent records"""
    dash = {
        "message": settings.motd,
        "user": {"email": user.email, "permissions": user.permissions},
        "workitems": None,
        "ukrdcrecords": None,
    }
    # Workitem stats
    if redis.exists("dashboard:workitems"):
        dash["workitems"] = redis.hgetall("dashboard:workitems")
    else:
        open_workitems_stats: Dict[str, int] = _total_day_prev(
            jtrace.query(WorkItem).filter(WorkItem.status == 1),
            WorkItem,
            "last_updated",
        )
        dash["workitems"] = open_workitems_stats
        redis.hmset("dashboard:workitems", open_workitems_stats)  # type: ignore
        # Remove cached statistics after 15 minutes. Next request will re-query
        redis.expire("dashboard:workitems", 900)

    if redis.exists("dashboard:ukrdcrecords"):
        dash["ukrdcrecords"] = redis.hgetall("dashboard:ukrdcrecords")
    else:
        ukrdc_masterrecords_stats: Dict[str, int] = _total_day_prev(
            jtrace.query(MasterRecord).filter(MasterRecord.nationalid_type == "UKRDC"),
            MasterRecord,
            "creation_date",
        )
        dash["ukrdcrecords"] = ukrdc_masterrecords_stats
        redis.hmset("dashboard:ukrdcrecords", ukrdc_masterrecords_stats)  # type: ignore
        # Remove cached statistics after 15 minutes. Next request will re-query
        redis.expire("dashboard:ukrdcrecords", 900)

    return dash
