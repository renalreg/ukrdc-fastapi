import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord, WorkItem
from ukrdc_sqla.errorsdb import Facility, Message

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, WorkItemShortSchema
from ukrdc_fastapi.schemas.errors import MessageSchema
from ukrdc_fastapi.utils.filters.errors import filter_error_messages
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter(tags=["Errors"])


class ExtendedErrorSchema(MessageSchema):
    master_records: Optional[list[MasterRecordSchema]]
    work_items: Optional[list[WorkItemShortSchema]]


def make_extended_error(message: MessageSchema, jtrace: Session):
    # Get masterrecords directly referenced by the error
    direct_records: list[MasterRecord] = (
        jtrace.query(MasterRecord).filter(MasterRecord.nationalid == message.ni).all()
    )

    # Get workitems related to masterrecords directly referenced by the error
    related_workitems: list[WorkItem] = (
        jtrace.query(WorkItem)
        .filter(
            WorkItem.master_id.in_([record.id for record in direct_records]),
            WorkItem.status == 1,
        )
        .all()
    )

    return ExtendedErrorSchema(
        **message.dict(), master_records=direct_records, work_items=related_workitems
    )


@router.get(
    "/",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(Permissions.READ_MIRTH))],
)
def error_messages(
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: Optional[str] = None,
    errorsdb: Session = Depends(get_errorsdb),
):
    """
    Retreive a list of error messages, optionally filtered by NI, facility, or date.
    By default returns message created within the last 7 days.
    """
    messages = errorsdb.query(Message)

    messages = filter_error_messages(messages, facility, since, until, status)

    return paginate(messages)


@router.get(
    "/facilities",
    response_model=list[str],
    dependencies=[Security(auth.permission(Permissions.READ_MIRTH))],
)
def error_facilities(
    errorsdb: Session = Depends(get_errorsdb),
):
    # TODO: Filter by permissions
    facilities = errorsdb.query(Facility).all()
    return [item.facility for item in facilities if item]


@router.get(
    "/{error_id}",
    response_model=ExtendedErrorSchema,
    dependencies=[Security(auth.permission(Permissions.READ_MIRTH))],
)
def error_detail(
    error_id: str,
    errorsdb: Session = Depends(get_errorsdb),
    jtrace: Session = Depends(get_jtrace),
):
    error = errorsdb.query(Message).get(error_id)
    if not error:
        raise HTTPException(404, detail="Master Record not found")

    extended_error = make_extended_error(MessageSchema.from_orm(error), jtrace)
    return extended_error
