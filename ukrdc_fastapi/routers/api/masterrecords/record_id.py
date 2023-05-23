import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, Security
from fastapi import Query as QueryParam
from mirth_client import MirthAPI
from pydantic import Field
from redis import Redis
from sqlalchemy.orm import Session
from starlette.status import HTTP_204_NO_CONTENT
from ukrdc_sqla.empi import LinkRecord, MasterRecord
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.dependencies import (
    get_auditdb,
    get_errorsdb,
    get_jtrace,
    get_mirth,
    get_redis,
    get_ukrdc3,
)
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.models.audit import AccessEvent, AuditEvent
from ukrdc_fastapi.permissions.masterrecords import apply_masterrecord_list_permissions
from ukrdc_fastapi.permissions.messages import (
    apply_message_list_permissions,
    assert_message_permissions,
)
from ukrdc_fastapi.permissions.patientrecords import apply_patientrecord_list_permission
from ukrdc_fastapi.permissions.persons import apply_persons_list_permission
from ukrdc_fastapi.permissions.workitems import apply_workitem_list_permission
from ukrdc_fastapi.query.audit import get_auditevents_related_to_masterrecord
from ukrdc_fastapi.query.masterrecords import get_masterrecords_related_to_masterrecord
from ukrdc_fastapi.query.messages import get_messages_related_to_masterrecord
from ukrdc_fastapi.query.mirth.memberships import create_pkb_membership_for_masterrecord
from ukrdc_fastapi.query.patientrecords import (
    get_patientrecords_related_to_masterrecord,
)
from ukrdc_fastapi.query.persons import get_persons_related_to_masterrecord
from ukrdc_fastapi.query.workitems import get_workitems
from ukrdc_fastapi.schemas.audit import AuditEventSchema
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
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import SQLASorter, make_sqla_sorter

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
    related_records = get_masterrecords_related_to_masterrecord(
        record,
        jtrace,
        nationalid_type=nationalid_type,
        exclude_self=exclude_self,
    )

    # Apply permissions and store list of records
    related_records = apply_masterrecord_list_permissions(related_records, user)

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

    return related_records.all()


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
    msgs = (
        get_messages_related_to_masterrecord(
            record,
            errorsdb,
            jtrace,
            since=datetime.datetime.utcnow() - datetime.timedelta(days=365),
        )
        .filter(Message.facility != "TRACING")
        .filter(Message.filename.isnot(None))
    )

    # Apply permissions
    msgs = apply_message_list_permissions(msgs, user)

    # Get latest message
    latest = msgs.order_by(Message.received.desc()).first()

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
    errors = get_messages_related_to_masterrecord(
        record, errorsdb, jtrace, statuses=["ERROR"]
    )

    related_records = get_masterrecords_related_to_masterrecord(record, jtrace)

    related_ukrdc_records = related_records.filter(
        MasterRecord.nationalid_type == "UKRDC"
    )

    workitems = get_workitems(
        jtrace, master_id=[record.id for record in related_records.all()]
    )

    audit.add_event(
        Resource.STATISTICS,
        None,
        AuditOperation.READ,
        parent=audit.add_event(Resource.MASTER_RECORD, record.id, AuditOperation.READ),
    )

    return MasterRecordStatisticsSchema(
        workitems=workitems.count(),
        errors=errors.count(),
        # Workaround for https://jira.ukrdc.org/browse/UI-56
        # For some reason, if you log in as a non-admin user,
        # related_ukrdc_records.count() returns the wrong value
        # sometimes, despite the query returning the right data.
        # I truly, deeply do not understand why this would happen,
        # so I've had to implement this slightly slower workaround.
        # Assuming the patient doesn't somehow have hundreds of
        # UKRDC records, the speed decrease should be negligable.
        ukrdcids=len(related_ukrdc_records.all()),
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
    related_records = get_masterrecords_related_to_masterrecord(record, jtrace)

    # Apply permissions to related records
    related_records = apply_masterrecord_list_permissions(related_records, user)

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
    messages = get_messages_related_to_masterrecord(
        record,
        errorsdb,
        jtrace,
        statuses=status,
        channels=channel,
        facility=facility,
        since=since,
        until=until,
    )

    # Apply permissions
    messages = apply_message_list_permissions(messages, user)

    # Add audit events
    audit.add_event(
        Resource.MESSAGES,
        None,
        AuditOperation.READ,
        parent=audit.add_event(Resource.MASTER_RECORD, record.id, AuditOperation.READ),
    )
    return paginate(sorter.sort(messages))


@router.get(
    "/{record_id}/workitems",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_workitems(
    record: MasterRecord = Depends(_get_masterrecord),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of work items related to a particular master record."""

    # Find work items related to record
    related_records = get_masterrecords_related_to_masterrecord(record, jtrace)
    workitems = get_workitems(
        jtrace, master_id=[record.id for record in related_records]
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
    persons = get_persons_related_to_masterrecord(record, jtrace)

    # Apply permissions
    persons = apply_persons_list_permission(persons, user)

    # Add audit events
    record_audit = audit.add_event(
        Resource.MASTER_RECORD, record.id, AuditOperation.READ
    )
    for person in persons:
        audit.add_event(
            Resource.PERSON, person.id, AuditOperation.READ, parent=record_audit
        )

    return persons.all()


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
    related_records = get_patientrecords_related_to_masterrecord(record, ukrdc3, jtrace)

    # Apply permissions
    related_records = apply_patientrecord_list_permission(related_records, user)

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

    return related_records.all()


@router.get(
    "/{record_id}/audit",
    response_model=Page[AuditEventSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS_AUDIT))],
)
def master_record_audit(
    record: MasterRecord = Depends(_get_masterrecord),
    jtrace: Session = Depends(get_jtrace),
    ukrdc3: Session = Depends(get_ukrdc3),
    auditdb: Session = Depends(get_auditdb),
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    sorter: SQLASorter = Depends(
        make_sqla_sorter(
            [AuditEvent.id, AccessEvent.time],
            default_sort_by=AuditEvent.id,
        )
    ),
):
    """
    Retreive a page of audit events related to a particular master record.
    """
    page = paginate(
        sorter.sort(
            get_auditevents_related_to_masterrecord(
                record, auditdb, ukrdc3, jtrace, since=since, until=until
            )
        )
    )

    for item in page.items:  # type: ignore
        item.populate_identifiers(jtrace, ukrdc3)

    return page


@router.post(
    "/{record_id}/memberships/create/pkb",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(Permissions.CREATE_MEMBERSHIPS))],
)
async def master_record_memberships_create_pkb(
    record: MasterRecord = Depends(_get_masterrecord),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    audit: Auditer = Depends(get_auditer),
    redis: Redis = Depends(get_redis),
):
    """
    Create a new PKB membership for a master record.
    """

    # If the request was not triggered from a UKRDC MasterRecord
    if record.nationalid_type != "UKRDC":
        # Find all linked UKRDC MasterRecords
        records = get_masterrecords_related_to_masterrecord(
            record,
            jtrace,
            nationalid_type="UKRDC",
        ).all()
        if len(records) > 1:
            raise HTTPException(
                500,
                "Cannot create PKB membership for a patient with multiple UKRDC IDs",
            )
        if not records:
            raise HTTPException(
                500,
                "Cannot create PKB membership for a patient with no UKRDC ID",
            )
        # Use the UKRDC MasterRecord to create the PKB membership
        record = records[0]

    audit.add_event(
        Resource.MEMBERSHIP,
        "PKB",
        AuditOperation.CREATE,
        parent=audit.add_event(Resource.MASTER_RECORD, record.id, AuditOperation.READ),
    )

    return await create_pkb_membership_for_masterrecord(record, mirth, redis)
