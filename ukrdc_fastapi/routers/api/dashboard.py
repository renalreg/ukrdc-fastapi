import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Security
from fastapi_auth0 import Auth0User
from fastapi_hypermodel import HyperModel, UrlFor
from pydantic import BaseModel
from sqlalchemy.orm import Query, Session
from ukrdc_sqla.empi import Base as EMPIBase
from ukrdc_sqla.empi import MasterRecord, WorkItem

from ukrdc_fastapi.auth import auth
from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_jtrace

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


def _total_day_prev(query: Query, table: EMPIBase, datefield: str):
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
):
    """Retreive basic statistics about recent records"""
    # Workitem stats
    open_workitems: Query = jtrace.query(WorkItem).filter(WorkItem.status == 1)
    ukrdc_masterrecords: Query = jtrace.query(MasterRecord).filter(
        MasterRecord.nationalid_type == "UKRDC"
    )

    return {
        "message": settings.motd,
        "workitems": _total_day_prev(open_workitems, WorkItem, "last_updated"),
        "ukrdcrecords": _total_day_prev(
            ukrdc_masterrecords, MasterRecord, "creation_date"
        ),
        "user": {"email": user.email, "permissions": user.permissions},
    }
