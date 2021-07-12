import datetime
import enum
from typing import Optional, Type

from fastapi import APIRouter, Depends, Query, Security
from pydantic import BaseModel, Field
from sqlalchemy import inspect
from sqlalchemy.orm import Query as ORMQuery
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import WorkItem

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.workitems import get_workitems
from ukrdc_fastapi.schemas.empi import WorkItemShortSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

from . import workitem_id

router = APIRouter(tags=["Work Items"])
router.include_router(workitem_id.router)


class UnlinkWorkItemRequestSchema(BaseModel):
    master_record: str = Field(..., title="Master record ID")
    person_id: str = Field(..., title="Person ID")
    comment: Optional[str]


class OrderBy(str, enum.Enum):
    asc = "asc"
    desc = "desc"


# def sort_parameters(sort_by: Optional[str] = None, order_by: Optional[OrderBy] = None):
#    return {"sort_by": sort_by, "order_by": order_by}


def ModelEnum(sqla_model: Type):
    mapper = inspect(sqla_model)
    columns = [column.key for column in mapper.attrs]
    return enum.Enum(f"{sqla_model.__name__}Enum", {col: col for col in columns})


def make_sort_dependency(sqla_model: Type):
    SortEnum = ModelEnum(sqla_model)

    def sort_parameters(
        sort_by: Optional[SortEnum] = None, order_by: Optional[OrderBy] = None
    ):
        return {"sort_by": sort_by, "order_by": order_by}

    return sort_parameters


def sort_query(
    query: ORMQuery,
    sqla_model: Type,
    sort_by: Optional[str] = None,
    order_by: Optional[OrderBy] = None,
):
    if not sort_by:
        return query
    order_col = getattr(sqla_model, sort_by)
    print(order_col)
    return query


@router.get(
    "/",
    response_model=Page[WorkItemShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_WORKITEMS))],
)
def workitems_list(
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: Optional[list[int]] = Query([1]),
    facility: Optional[str] = None,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    sort: dict = Depends(make_sort_dependency(WorkItem)),
):
    """Retreive a list of open work items from the EMPI"""
    print(sort)
    query = get_workitems(
        jtrace, user, statuses=status, facility=facility, since=since, until=until
    )
    sorted = sort_query(query, WorkItem, sort["sort_by"], sort["order_by"])
    return paginate(query)
