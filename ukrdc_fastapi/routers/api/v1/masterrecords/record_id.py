import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query as QueryParam
from fastapi import Response, Security
from mirth_client import MirthAPI
from redis import Redis
from sqlalchemy.orm import Session
from starlette.status import HTTP_204_NO_CONTENT
from ukrdc_sqla.empi import LinkRecord, MasterRecord

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
from ukrdc_fastapi.query.audit import get_auditevents_related_to_masterrecord
from ukrdc_fastapi.query.masterrecords import (
    get_masterrecord,
    get_masterrecords_related_to_masterrecord,
)
from ukrdc_fastapi.query.messages import (
    ERROR_SORTER,
    get_last_message_on_masterrecord,
    get_messages_related_to_masterrecord,
)
from ukrdc_fastapi.query.mirth.memberships import create_pkb_membership
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
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import SQLASorter, make_sqla_sorter


class MasterRecordStatisticsSchema(OrmModel):
    workitems: int
    errors: int
    ukrdcids: int


router = APIRouter(prefix="/{record_id}")


@router.get(
    "/",
    response_model=MasterRecordSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_detail(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a particular master record from the EMPI"""
    record = get_masterrecord(jtrace, record_id, user)

    audit.add_event(Resource.MASTER_RECORD, record.id, AuditOperation.READ)

    return record


@router.get(
    "/related/",
    response_model=list[MasterRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_related(
    record_id: int,
    exclude_self: bool = True,
    nationalid_type: Optional[str] = None,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of other master records related to a particular master record"""
    records = get_masterrecords_related_to_masterrecord(
        jtrace,
        record_id,
        user,
        nationalid_type=nationalid_type,
        exclude_self=exclude_self,
    ).all()

    record_audit = audit.add_event(
        Resource.MASTER_RECORD, record_id, AuditOperation.READ
    )
    for record in records:
        audit.add_event(
            Resource.MASTER_RECORD,
            record.id,
            AuditOperation.READ,
            parent=record_audit,
        )

    return records


@router.get(
    "/latest_message/",
    response_model=MinimalMessageSchema,
    responses={204: {"model": None}},
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_latest_message(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
):
    """
    Retreive a minimal representation of the latest file received for the patient,
    if received within the last year."""
    latest = get_last_message_on_masterrecord(jtrace, errorsdb, record_id, user)
    if not latest:
        return Response(status_code=HTTP_204_NO_CONTENT)

    return latest


@router.get(
    "/statistics/",
    response_model=MasterRecordStatisticsSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_statistics(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a particular master record from the EMPI"""
    record: MasterRecord = get_masterrecord(jtrace, record_id, user)

    errors = get_messages_related_to_masterrecord(
        errorsdb, jtrace, record.id, user, statuses=["ERROR"]
    )

    related_records = get_masterrecords_related_to_masterrecord(jtrace, record.id, user)

    related_ukrdc_records = related_records.filter(
        MasterRecord.nationalid_type == "UKRDC"
    )

    workitems = get_workitems(
        jtrace, user, master_id=[record.id for record in related_records.all()]
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
    "/linkrecords/",
    response_model=list[LinkRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_linkrecords(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of link records related to a particular master record"""
    # Find record and asserrt permissions
    records = get_masterrecords_related_to_masterrecord(jtrace, record_id, user).all()
    link_records: list[LinkRecord] = []

    for record in records:
        link_records.extend(record.link_records)

    record_audit = audit.add_event(
        Resource.MASTER_RECORD, record_id, AuditOperation.READ
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
    "/messages/",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_messages(
    record_id: int,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: Optional[list[str]] = QueryParam(None),
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
    audit.add_event(
        Resource.MESSAGES,
        None,
        AuditOperation.READ,
        parent=audit.add_event(Resource.MASTER_RECORD, record_id, AuditOperation.READ),
    )
    return paginate(
        sorter.sort(
            get_messages_related_to_masterrecord(
                errorsdb, jtrace, record_id, user, status, facility, since, until
            )
        )
    )


@router.get(
    "/workitems/",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_workitems(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of work items related to a particular master record."""
    related: list[MasterRecord] = get_masterrecords_related_to_masterrecord(
        jtrace, record_id, user
    ).all()

    workitems = get_workitems(
        jtrace, user, master_id=[record.id for record in related]
    ).all()

    record_audit = audit.add_event(
        Resource.MASTER_RECORD, record_id, AuditOperation.READ
    )
    for item in workitems:
        audit.add_workitem(item, parent=record_audit)

    return workitems


@router.get(
    "/persons/",
    response_model=list[PersonSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_persons(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of person records related to a particular master record."""
    persons = get_persons_related_to_masterrecord(jtrace, record_id, user).all()

    record_audit = audit.add_event(
        Resource.MASTER_RECORD, record_id, AuditOperation.READ
    )
    for person in persons:
        audit.add_event(
            Resource.PERSON, person.id, AuditOperation.READ, parent=record_audit
        )

    return persons


@router.get(
    "/patientrecords/",
    response_model=list[PatientRecordSummarySchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_patientrecords(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    ukrdc3: Session = Depends(get_ukrdc3),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a list of patient records related to a particular master record."""
    records = get_patientrecords_related_to_masterrecord(
        ukrdc3, jtrace, record_id, user
    ).all()

    record_audit = audit.add_event(
        Resource.MASTER_RECORD, record_id, AuditOperation.READ
    )
    for record in records:
        audit.add_event(
            Resource.PATIENT_RECORD,
            record.pid,
            AuditOperation.READ,
            parent=record_audit,
        )

    return records


@router.get(
    "/audit/",
    response_model=Page[AuditEventSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS_AUDIT))],
)
def master_record_audit(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
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
                auditdb, ukrdc3, jtrace, record_id, user, since=since, until=until
            )
        )
    )

    for item in page.items:  # type: ignore
        item.populate_identifiers(jtrace, ukrdc3)

    return page


@router.post(
    "/memberships/create/pkb",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(Permissions.CREATE_MEMBERSHIPS))],
)
async def master_record_memberships_create_pkb(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    audit: Auditer = Depends(get_auditer),
    redis: Redis = Depends(get_redis),
):
    """
    Create a new PKB membership for a master record.
    """
    record = get_masterrecord(jtrace, record_id, user)

    # If the request was not triggered from a UKRDC MasterRecord
    if record.nationalid_type != "UKRDC":
        # Find all linked UKRDC MasterRecords
        records = get_masterrecords_related_to_masterrecord(
            jtrace,
            record_id,
            user,
            nationalid_type="UKRDC",
        ).all()
        if len(records) > 1:
            raise HTTPException(
                500,
                "Cannot create PKB membership for a patient with multiple UKRDC IDs",
            )
        elif len(records) == 0:
            raise HTTPException(
                500,
                "Cannot create PKB membership for a patient with no UKRDC ID",
            )
        else:
            # Use the UKRDC MasterRecord to create the PKB membership
            record = records[0]

    audit.add_event(
        Resource.MEMBERSHIP,
        "PKB",
        AuditOperation.CREATE,
        parent=audit.add_event(Resource.MASTER_RECORD, record_id, AuditOperation.READ),
    )

    return await create_pkb_membership(record, mirth, redis)
