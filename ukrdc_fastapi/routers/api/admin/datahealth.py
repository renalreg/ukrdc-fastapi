import datetime

from fastapi import APIRouter, Depends, Security
from pydantic import Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.stats import LastRunTimes

from ukrdc_fastapi.dependencies import get_jtrace, get_statsdb
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.query.stats import MultipleUKRDCIDGroup, get_multiple_ukrdcids
from ukrdc_fastapi.query.workitems import select_workitems
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.empi import MasterRecordSchema
from ukrdc_fastapi.utils.paginate import Page, paginate_sequence
from ukrdc_fastapi.utils.sort import ObjectSorter, OrderBy, make_object_sorter

router = APIRouter(tags=["Admin/Data Health"])

DATA_HEALTH_PERMISSIONS = [
    Permissions.READ_RECORDS,
    Permissions.READ_WORKITEMS,
    Permissions.UNIT_ALL,
]


class WorkItemGroup(OrmModel):
    master_record: MasterRecordSchema
    work_item_count: int


class LastRunTime(OrmModel):
    """Information about the last time a data health check was run"""

    last_run_time: datetime.datetime = Field(
        ..., description="Timestamp of last time the results were recalculated"
    )


@router.get(
    "/multiple_ukrdcids",
    response_model=Page[MultipleUKRDCIDGroup],
    dependencies=[Security(auth.permission(DATA_HEALTH_PERMISSIONS))],
)
def datahealth_multiple_ukrdcids(
    jtrace: Session = Depends(get_jtrace),
    statsdb: Session = Depends(get_statsdb),
):
    """Retreive list of patients with multiple UKRDC IDs"""
    return paginate_sequence(get_multiple_ukrdcids(statsdb, jtrace))


@router.get(
    "/multiple_ukrdcids/last_run",
    response_model=LastRunTime,
    dependencies=[Security(auth.permission(DATA_HEALTH_PERMISSIONS))],
)
def datahealth_multiple_ukrdcids_last_run(
    statsdb: Session = Depends(get_statsdb),
):
    """Retreive the datetime the multiple_ukrdcid table was fully refreshed"""
    return statsdb.get(LastRunTimes, ("multiple_ukrdcid", ""))


@router.get(
    "/record_workitem_counts",
    response_model=Page[WorkItemGroup],
    dependencies=[Security(auth.permission(DATA_HEALTH_PERMISSIONS))],
)
def record_workitem_counts(
    sorter: ObjectSorter = Depends(
        make_object_sorter(
            "WorkItemGroupSorterEnum",
            ["work_item_count", "master_record.id", "master_record.last_updated"],
            default_sort_by="work_item_count",
            default_order_by=OrderBy.DESC,
        )
    ),
    jtrace: Session = Depends(get_jtrace),
):
    """
    Retreive a list of all master records with open work items, and the number of work items on each.
    Most useful when sorted by descending work item count, to identify records most in need of work item resolution.
    """
    subq1 = select_workitems(statuses=[1]).subquery()

    subq2 = (
        select(subq1.c.masterid, func.count("*").label("workitem_count"))
        .group_by(subq1.c.masterid)
        .subquery()
    )

    count_query = select(MasterRecord, subq2.c.workitem_count).join(
        subq2, MasterRecord.id == subq2.c.masterid
    )

    result = jtrace.execute(count_query)

    items = [
        WorkItemGroup(master_record=record, work_item_count=count)
        for record, count in result
    ]

    return paginate_sequence(sorter.sort(items))
