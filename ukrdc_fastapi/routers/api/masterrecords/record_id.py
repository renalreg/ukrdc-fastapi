import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Response, Security
from fastapi import Query as QueryParam
from pydantic import Field
from sqlalchemy.orm import Session
from starlette.status import HTTP_204_NO_CONTENT
from ukrdc_sqla.empi import LinkRecord, MasterRecord
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_ukrdc3
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.permissions.masterrecords import apply_masterrecord_list_permissions
from ukrdc_fastapi.permissions.messages import (
    apply_message_list_permissions,
    assert_message_permissions,
)
from ukrdc_fastapi.permissions.patientrecords import apply_patientrecord_list_permission
from ukrdc_fastapi.permissions.persons import apply_persons_list_permission
from ukrdc_fastapi.permissions.workitems import apply_workitem_list_permission
from ukrdc_fastapi.query.masterrecords import (
    select_masterrecords_related_to_masterrecord,
)
from ukrdc_fastapi.query.messages import select_messages_related_to_masterrecord
from ukrdc_fastapi.query.patientrecords import (
    select_patientrecords_related_to_masterrecord,
)
from ukrdc_fastapi.query.persons import select_persons_related_to_masterrecord
from ukrdc_fastapi.query.utils import count_rows
from ukrdc_fastapi.query.workitems import get_workitems
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.empi import (
    LinkRecordSchema,
    MasterRecordSchema,
    PersonSchema,
    WorkItemSchema,
)
from ukrdc_fastapi.schemas.message import MessageSchema, MinimalMessageSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSummarySchema
from ukrdc_fastapi.sorters import ERROR_SORTER
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import SQLASorter

from .dependencies import _get_masterrecord


class MasterRecordStatisticsSchema(OrmModel):
    """Counts of various objects related to a master record"""

    workitems: int = Field(
        ..., description="Number of workitems related to this master record"
    )
    errors: int = Field(
        ..., description="Number of error messages related to this master record"
    )
    ukrdcids: int = Field(
        ..., description="Number of UKRDC IDs related to this master record"
    )


router = APIRouter()


@router.get(
    "/{record_id}",
    response_model=MasterRecordSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record(
    record: MasterRecord = Depends(_get_masterrecord),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a particular master record from the EMPI"""

    # Add audit event
    audit.add_event(Resource.MASTER_RECORD, record.id, AuditOperation.READ)

    return record


@router.get(
    "/{record_id}/related",
    response_model=list[MasterRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_related(
    record: MasterRecord = Depends(_get_masterrecord),
    exclude_self: bool = True,
    nationalid_type: Optional[str] = None,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of other master records related to a particular master record"""

    # Get related records
    stmt = select_masterrecords_related_to_masterrecord(
        record,
        jtrace,
        nationalid_type=nationalid_type,
        exclude_self=exclude_self,
    )
    stmt = apply_masterrecord_list_permissions(stmt, user)
    related_records = jtrace.scalars(stmt).all()

    # Add audit events
    record_audit = audit.add_event(
        Resource.MASTER_RECORD, record.id, AuditOperation.READ
    )
    for related_record in related_records:
        if related_record:
            audit.add_event(
                Resource.MASTER_RECORD,
                related_record.id,
                AuditOperation.READ,
                parent=record_audit,
            )

    return related_records


@router.get(
    "/{record_id}/latest_message",
    response_model=MinimalMessageSchema,
    responses={204: {"model": None}},
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_latest_message(
    record: MasterRecord = Depends(_get_masterrecord),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
):
    """
    Retreive a minimal representation of the latest file received for the patient,
    if received within the last year."""

    # Get messages related to the master record
    stmt = (
        select_messages_related_to_masterrecord(
            record,
            jtrace,
            since=datetime.datetime.utcnow() - datetime.timedelta(days=365),
        )
        .where(Message.facility != "TRACING")
        .where(Message.filename.isnot(None))
    )
    stmt = apply_message_list_permissions(stmt, user)

    # Get latest message
    stmt = stmt.order_by(Message.received.desc())
    latest = errorsdb.scalars(stmt).first()

    if not latest:
        return Response(status_code=HTTP_204_NO_CONTENT)

    assert_message_permissions(latest, user)

    return latest


@router.get(
    "/{record_id}/statistics",
    response_model=MasterRecordStatisticsSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_statistics(
    record: MasterRecord = Depends(_get_masterrecord),
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a particular master record from the EMPI"""
    # Select errors
    stmt_errors = select_messages_related_to_masterrecord(
        record, jtrace, statuses=["ERROR"]
    )

    # Get related records
    stmt = select_masterrecords_related_to_masterrecord(record, jtrace).where(
        MasterRecord.nationalid_type == "UKRDC"
    )
    related_records = jtrace.scalars(stmt).all()

    # Get workitems
    workitems = get_workitems(
        jtrace, master_id=[record.id for record in related_records]
    )

    # Add audit events
    audit.add_event(
        Resource.STATISTICS,
        None,
        AuditOperation.READ,
        parent=audit.add_event(Resource.MASTER_RECORD, record.id, AuditOperation.READ),
    )

    return MasterRecordStatisticsSchema(
        workitems=workitems.count(),
        errors=count_rows(stmt_errors, errorsdb),
        # Workaround for https://jira.ukrdc.org/browse/UI-56
        # For some reason, if you log in as a non-admin user,
        # related_ukrdc_records.count() returns the wrong value
        # sometimes, despite the query returning the right data.
        # I truly, deeply do not understand why this would happen,
        # so I've had to implement this slightly slower workaround.
        # Assuming the patient doesn't somehow have hundreds of
        # UKRDC records, the speed decrease should be negligable.
        ukrdcids=len(related_records),
    )


@router.get(
    "/{record_id}/linkrecords",
    response_model=list[LinkRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_linkrecords(
    record: MasterRecord = Depends(_get_masterrecord),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of link records related to a particular master record"""
    # Find record and asserrt permissions
    stmt = select_masterrecords_related_to_masterrecord(record, jtrace)
    stmt = apply_masterrecord_list_permissions(stmt, user)
    related_records = jtrace.scalars(stmt).all()

    # Get link records
    link_records: list[LinkRecord] = []

    for related_record in related_records:
        link_records.extend(related_record.link_records)

    record_audit = audit.add_event(
        Resource.MASTER_RECORD, record.id, AuditOperation.READ
    )
    audited_master_ids = set()
    audited_person_ids = set()
    for link in link_records:
        if link.master_id not in audited_master_ids:
            audit.add_event(
                Resource.MASTER_RECORD,
                link.master_id,
                AuditOperation.READ,
                parent=record_audit,
            )
            audited_master_ids.add(link.master_id)
        if link.person_id not in audited_person_ids:
            audit.add_event(
                Resource.PERSON,
                link.person_id,
                AuditOperation.READ,
                parent=record_audit,
            )
            audited_person_ids.add(link.person_id)

    return link_records


@router.get(
    "/{record_id}/messages",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_messages(
    record: MasterRecord = Depends(_get_masterrecord),
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: Optional[list[str]] = QueryParam(None),
    channel: Optional[list[str]] = QueryParam(None),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
    sorter: SQLASorter = Depends(ERROR_SORTER),
    audit: Auditer = Depends(get_auditer),
):
    """
    Retreive a list of errors related to a particular master record.
    By default returns message created within the last 365 days.
    """
    stmt = select_messages_related_to_masterrecord(
        record,
        jtrace,
        statuses=status,
        channels=channel,
        facility=facility,
        since=since,
        until=until,
    )
    stmt = apply_message_list_permissions(stmt, user)

    # Add audit events
    audit.add_event(
        Resource.MESSAGES,
        None,
        AuditOperation.READ,
        parent=audit.add_event(Resource.MASTER_RECORD, record.id, AuditOperation.READ),
    )
    return paginate(errorsdb, sorter.sort(stmt))


@router.get(
    "/{record_id}/workitems",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_workitems(
    record: MasterRecord = Depends(_get_masterrecord),
    status: Optional[list[int]] = QueryParam([1]),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of work items related to a particular master record."""

    # Find work items related to record
    stmt = select_masterrecords_related_to_masterrecord(record, jtrace)
    related_records = jtrace.scalars(stmt).all()

    workitems = get_workitems(
        jtrace,
        statuses=status or [],
        master_id=[record.id for record in related_records],
    )

    # Apply permissions
    workitems = apply_workitem_list_permission(workitems, user)

    # Add audit events
    record_audit = audit.add_event(
        Resource.MASTER_RECORD, record.id, AuditOperation.READ
    )
    for item in workitems:
        audit.add_workitem(item, parent=record_audit)

    return workitems.all()


@router.get(
    "/{record_id}/persons",
    response_model=list[PersonSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_persons(
    record: MasterRecord = Depends(_get_masterrecord),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of person records related to a particular master record."""
    stmt = select_persons_related_to_masterrecord(record, jtrace)
    stmt = apply_persons_list_permission(stmt, user)
    persons = jtrace.scalars(stmt).all()

    # Add audit events
    record_audit = audit.add_event(
        Resource.MASTER_RECORD, record.id, AuditOperation.READ
    )
    for person in persons:
        audit.add_event(
            Resource.PERSON, person.id, AuditOperation.READ, parent=record_audit
        )

    return persons


@router.get(
    "/{record_id}/patientrecords",
    response_model=list[PatientRecordSummarySchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_patientrecords(
    record: MasterRecord = Depends(_get_masterrecord),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    ukrdc3: Session = Depends(get_ukrdc3),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of patient records related to a particular master record."""
    stmt = select_patientrecords_related_to_masterrecord(record, jtrace)
    stmt = apply_patientrecord_list_permission(stmt, user)
    related_records = ukrdc3.scalars(stmt).all()

    record_audit = audit.add_event(
        Resource.MASTER_RECORD, record.id, AuditOperation.READ
    )
    for related_record in related_records:
        audit.add_event(
            Resource.PATIENT_RECORD,
            related_record.pid,
            AuditOperation.READ,
            parent=record_audit,
        )

    return related_records
