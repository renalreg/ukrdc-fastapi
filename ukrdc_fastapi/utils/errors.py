"""
Functions related to our extended error message object model.

The basic errors DB does not include some information we want returned
by the API. These functions and classes handle converting basic error
messages into something more useful.

NOTE: This entire submodule is essentially a hack to get extra info
not found in the errorsdb. Ideally we should look to include some of
this by default in the database.
"""

from typing import Optional

from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord, WorkItem

from ukrdc_fastapi.schemas.empi import MasterRecordSchema, WorkItemShortSchema
from ukrdc_fastapi.schemas.errors import MessageSchema


class ExtendedErrorSchema(MessageSchema):
    master_records: Optional[list[MasterRecordSchema]]
    work_items: Optional[list[WorkItemShortSchema]]


def make_extended_error(message: MessageSchema, jtrace: Session) -> ExtendedErrorSchema:
    """
    Take a basic errorsdb message and extend it to include
    associated master records and work items.

    Args:
        message (MessageSchema): ErrorsDB message object
        jtrace (Session): EMPI session

    Returns:
        ErrorSchema: Expanded error message object
    """
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
