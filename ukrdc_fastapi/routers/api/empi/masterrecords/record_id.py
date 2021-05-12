import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.param_functions import Query
from sqlalchemy.orm import Query as ORMQuery
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord, Person, WorkItem
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema, WorkItemSchema
from ukrdc_fastapi.schemas.errors import MessageSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordShortSchema
from ukrdc_fastapi.utils.filters.empi import (
    find_persons_related_to_masterrecord,
    find_related_masterrecords,
)
from ukrdc_fastapi.utils.filters.errors import filter_error_messages
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter(prefix="/{record_id}")


@router.get(
    "/",
    response_model=MasterRecordSchema,
    dependencies=[Security(auth.permission(Permissions.READ_EMPI))],
)
def master_record_detail(record_id: str, jtrace: Session = Depends(get_jtrace)):
    """Retreive a particular master record from the EMPI"""
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    return record


@router.get(
    "/related/",
    response_model=list[MasterRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_EMPI))],
)
def master_record_related(record_id: str, jtrace: Session = Depends(get_jtrace)):
    """Retreive a list of other master records related to a particular master record"""
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    other_records = find_related_masterrecords(record, jtrace).filter(
        MasterRecord.id != record_id
    )

    return other_records.all()


@router.get(
    "/errors/",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(Permissions.READ_EMPI))],
)
def master_record_errors(
    record_id: str,
    facility: Optional[str] = None,
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    status: Optional[str] = None,
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
):
    """
    Retreive a list of errors related to a particular master record.
    By default returns message created within the last 7 days.
    """
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)

    related_master_records = find_related_masterrecords(record, jtrace)

    related_national_ids: list[str] = [
        record.nationalid for record in related_master_records.all()
    ]

    messages: ORMQuery = errorsdb.query(Message).filter(
        Message.ni.in_(related_national_ids)
    )

    messages = filter_error_messages(messages, facility, since, until, status)

    return paginate(messages)


@router.get(
    "/workitems/",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_EMPI))],
)
def master_record_workitems(record_id: str, jtrace: Session = Depends(get_jtrace)):
    """Retreive a list of work items related to a particular master record."""
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    related_workitems: ORMQuery = jtrace.query(WorkItem).filter(
        WorkItem.master_id == record.id,
        WorkItem.status == 1,
    )

    return related_workitems.all()


@router.get(
    "/persons/",
    response_model=list[PersonSchema],
    dependencies=[Security(auth.permission(Permissions.READ_EMPI))],
)
def master_record_persons(record_id: str, jtrace: Session = Depends(get_jtrace)):
    """Retreive a list of person records related to a particular master record."""
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    persons = find_persons_related_to_masterrecord(record, jtrace)
    return persons.all()


@router.get(
    "/patientrecords/",
    response_model=list[PatientRecordShortSchema],
    dependencies=[
        Security(
            auth.permission([Permissions.READ_EMPI, Permissions.READ_PATIENTRECORDS])
        )
    ],
)
def master_record_patientrecords(
    record_id: str,
    jtrace: Session = Depends(get_jtrace),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of patient records related to a particular master record."""
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    related_persons = find_persons_related_to_masterrecord(record, jtrace)

    related_patient_ids = set()
    for person in related_persons:
        related_patient_ids.add(person.localid)

    patient_records: ORMQuery = ukrdc3.query(PatientRecord).filter(
        PatientRecord.pid.in_(related_patient_ids)
    )

    return patient_records.all()
