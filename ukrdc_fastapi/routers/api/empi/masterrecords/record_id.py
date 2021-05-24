import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Query as ORMQuery
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord, WorkItem
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.access_models.empi import MasterRecordAM, PersonAM, WorkItemAM
from ukrdc_fastapi.access_models.errorsdb import MessageAM
from ukrdc_fastapi.access_models.ukrdc import PatientRecordAM
from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema, WorkItemSchema
from ukrdc_fastapi.schemas.errors import MessageSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordShortSchema
from ukrdc_fastapi.utils.filters.empi import (
    find_persons_related_to_masterrecord,
    find_related_masterrecords,
)
from ukrdc_fastapi.utils.filters.errors import filter_error_messages
from ukrdc_fastapi.utils.paginate import Page, paginate


class MasterRecordStatisticsSchema(OrmModel):
    workitems: int
    errors: int
    ukrdcids: int


def safe_get_record(jtrace: Session, record_id: str, user: UKRDCUser) -> MasterRecord:
    """Return a MasterRecord by ID if it exists and the user has permission

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        record_id (str): MasterRecord ID
        user (UKRDCUser): User object

    Raises:
        HTTPException: User does not have permission to access the resource

    Returns:
        MasterRecord: MasterRecord
    """
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")
    MasterRecordAM.assert_permission(record, user)
    return record


router = APIRouter(prefix="/{record_id}")


@router.get(
    "/",
    response_model=MasterRecordSchema,
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_detail(
    record_id: str,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a particular master record from the EMPI"""
    record: MasterRecord = safe_get_record(jtrace, record_id, user)

    return record


@router.get(
    "/statistics",
    response_model=MasterRecordStatisticsSchema,
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_statistics(
    record_id: str,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
):
    """Retreive a particular master record from the EMPI"""
    record: MasterRecord = safe_get_record(jtrace, record_id, user)

    errors = errorsdb.query(Message).filter(Message.ni == record.nationalid)
    errors = filter_error_messages(errors, None, None, None, "ERROR")

    workitems = jtrace.query(WorkItem).filter(
        WorkItem.master_id == record.id,
        WorkItem.status == 1,
    )

    ukrdc_records = find_related_masterrecords(record, jtrace).filter(
        MasterRecord.nationalid_type == "UKRDC"
    )

    return MasterRecordStatisticsSchema(
        workitems=workitems.count(),
        errors=errors.count(),
        ukrdcids=ukrdc_records.count(),
    )


@router.get(
    "/related/",
    response_model=list[MasterRecordSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_related(
    record_id: str,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of other master records related to a particular master record"""
    record: MasterRecord = safe_get_record(jtrace, record_id, user)

    records = find_related_masterrecords(record, jtrace).filter(
        MasterRecord.id != record_id
    )

    records = MasterRecordAM.apply_query_permissions(records, user)
    return records.all()


@router.get(
    "/errors/",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_errors(
    record_id: str,
    user: UKRDCUser = Security(auth.get_user),
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: str = "ERROR",
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
):
    """
    Retreive a list of errors related to a particular master record.
    By default returns message created within the last 365 days.
    """
    record: MasterRecord = safe_get_record(jtrace, record_id, user)

    related_master_records = find_related_masterrecords(record, jtrace)

    related_national_ids: list[str] = [
        record.nationalid for record in related_master_records.all()
    ]

    messages: ORMQuery = errorsdb.query(Message).filter(
        Message.ni.in_(related_national_ids)
    )

    messages = filter_error_messages(
        messages, facility, since, until, status, default_since_delta=365
    )

    messages = MessageAM.apply_query_permissions(messages, user)
    return paginate(messages)


@router.get(
    "/workitems/",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_workitems(
    record_id: str,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of work items related to a particular master record."""
    record: MasterRecord = safe_get_record(jtrace, record_id, user)

    related_workitems: ORMQuery = jtrace.query(WorkItem).filter(
        WorkItem.master_id == record.id,
        WorkItem.status == 1,
    )

    related_workitems = WorkItemAM.apply_query_permissions(related_workitems, user)
    return related_workitems.all()


@router.get(
    "/persons/",
    response_model=list[PersonSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_persons(
    record_id: str,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of person records related to a particular master record."""
    record: MasterRecord = safe_get_record(jtrace, record_id, user)

    persons = find_persons_related_to_masterrecord(record, jtrace)

    persons = PersonAM.apply_query_permissions(persons, user)
    return persons.all()


@router.get(
    "/patientrecords/",
    response_model=list[PatientRecordShortSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_patientrecords(
    record_id: str,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of patient records related to a particular master record."""
    record: MasterRecord = safe_get_record(jtrace, record_id, user)

    related_persons = find_persons_related_to_masterrecord(record, jtrace)

    related_patient_ids = set()
    for person in related_persons:
        related_patient_ids.add(person.localid)

    records: ORMQuery = ukrdc3.query(PatientRecord).filter(
        PatientRecord.pid.in_(related_patient_ids)
    )

    records = PatientRecordAM.apply_query_permissions(records, user)
    return records.all()
