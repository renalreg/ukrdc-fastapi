from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Query as OrmQuery
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord, Person, WorkItem
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies import get_jtrace, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Scopes, Security, User, auth
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema, WorkItemSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordShortSchema
from ukrdc_fastapi.utils.filters import find_ids_related_to_masterrecord
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


@router.get("/", response_model=Page[MasterRecordSchema])
def master_records(
    ni: Optional[list[str]] = Query(None),
    jtrace: Session = Depends(get_jtrace),
    _: User = Security(auth.get_user, scopes=[Scopes.READ_EMPI]),
):
    """Retreive a list of master records from the EMPI"""
    records: OrmQuery = jtrace.query(MasterRecord)
    if ni:
        records = records.filter(MasterRecord.nationalid.in_(ni))
    return paginate(records)


@router.get("/{record_id}/", response_model=MasterRecordSchema)
def master_record_detail(
    record_id: str,
    jtrace: Session = Depends(get_jtrace),
    _: User = Security(auth.get_user, scopes=[Scopes.READ_EMPI]),
):
    """Retreive a particular master record from the EMPI"""
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    return record


@router.get("/{record_id}/related/", response_model=list[MasterRecordSchema])
def master_record_related(
    record_id: str,
    jtrace: Session = Depends(get_jtrace),
    _: User = Security(auth.get_user, scopes=[Scopes.READ_EMPI]),
):
    """Retreive a list of other master records related to a particular master record"""
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    related_master_ids, _ = find_ids_related_to_masterrecord(
        [record.nationalid], jtrace
    )

    other_records = jtrace.query(MasterRecord).filter(
        MasterRecord.id.in_(related_master_ids), MasterRecord.id != record_id
    )

    return other_records.all()


@router.get("/{record_id}/workitems/", response_model=list[WorkItemSchema])
def master_record_workitems(
    record_id: str,
    jtrace: Session = Depends(get_jtrace),
    _: User = Security(auth.get_user, scopes=[Scopes.READ_EMPI]),
):
    """Retreive a list of work items related to a particular master record."""
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    related_workitems: OrmQuery = jtrace.query(WorkItem).filter(
        WorkItem.master_id == record.id,
        WorkItem.status == 1,
    )

    return related_workitems.all()


@router.get("/{record_id}/persons/", response_model=list[PersonSchema])
def master_record_persons(
    record_id: str,
    jtrace: Session = Depends(get_jtrace),
    _: User = Security(auth.get_user, scopes=[Scopes.READ_EMPI]),
):
    """Retreive a list of person records related to a particular master record."""
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    _, related_person_ids = find_ids_related_to_masterrecord(
        [record.nationalid], jtrace
    )

    persons: OrmQuery = jtrace.query(Person).filter(Person.id.in_(related_person_ids))

    return persons.all()


@router.get(
    "/{record_id}/patientrecords/", response_model=list[PatientRecordShortSchema]
)
def master_record_patientrecords(
    record_id: str,
    jtrace: Session = Depends(get_jtrace),
    ukrdc3: Session = Depends(get_ukrdc3),
    _: User = Security(
        auth.get_user, scopes=[Scopes.READ_EMPI, Scopes.READ_PATIENTRECORDS]
    ),
):
    """Retreive a list of patient records related to a particular master record."""
    record: MasterRecord = jtrace.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, detail="Master Record not found")

    _, related_person_ids = find_ids_related_to_masterrecord(
        [record.nationalid], jtrace
    )

    related_patient_ids = set()
    for person_id in related_person_ids:
        person: Optional[Person] = jtrace.query(Person).get(person_id)
        if person:
            related_patient_ids.add(person.localid)

    patient_records: OrmQuery = ukrdc3.query(PatientRecord).filter(
        PatientRecord.pid.in_(related_patient_ids)
    )

    return patient_records.all()
