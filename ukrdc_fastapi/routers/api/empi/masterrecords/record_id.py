import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.errors import get_errors, get_errors_related_to_masterrecord
from ukrdc_fastapi.query.masterrecords import (
    get_masterrecord,
    get_masterrecords_related_to_masterrecord,
)
from ukrdc_fastapi.query.patientrecords import get_patientrecords
from ukrdc_fastapi.query.persons import get_persons
from ukrdc_fastapi.query.workitems import get_workitems
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.empi import (
    LinkRecordSchema,
    MasterRecordSchema,
    PersonSchema,
    WorkItemSchema,
)
from ukrdc_fastapi.schemas.errors import MessageSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSchema
from ukrdc_fastapi.utils.links import find_related_ids
from ukrdc_fastapi.utils.paginate import Page, paginate


class MasterRecordStatisticsSchema(OrmModel):
    workitems: int
    errors: int
    ukrdcids: int


router = APIRouter(prefix="/{record_id}")


@router.get(
    "/",
    response_model=MasterRecordSchema,
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_detail(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a particular master record from the EMPI"""
    return get_masterrecord(jtrace, record_id, user)


@router.get(
    "/statistics",
    response_model=MasterRecordStatisticsSchema,
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_statistics(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
):
    """Retreive a particular master record from the EMPI"""
    record: MasterRecord = get_masterrecord(jtrace, record_id, user)

    errors = get_errors_related_to_masterrecord(errorsdb, jtrace, user, record.id)

    related = get_masterrecords_related_to_masterrecord(jtrace, record.id, user)
    workitems = get_workitems(
        jtrace, user, master_id=[record.id for record in related.all()]
    )

    ukrdc_records = related.filter(MasterRecord.nationalid_type == "UKRDC")

    return MasterRecordStatisticsSchema(
        workitems=workitems.count(),
        errors=errors.count(),
        ukrdcids=ukrdc_records.count(),
    )


@router.get(
    "/linkrecords/",
    response_model=list[LinkRecordSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_linkrecords(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of link records related to a particular master record"""
    # Find record and asserrt permissions
    records = get_masterrecords_related_to_masterrecord(jtrace, record_id, user).all()
    link_records: list[LinkRecord] = []
    for record in records:
        link_records.extend(record.link_records)
    return link_records


@router.get(
    "/related/",
    response_model=list[MasterRecordSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_related(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of other master records related to a particular master record"""
    return get_masterrecords_related_to_masterrecord(jtrace, record_id, user).all()


@router.get(
    "/errors/",
    response_model=Page[MessageSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_errors(
    record_id: int,
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
    return paginate(
        get_errors_related_to_masterrecord(
            errorsdb, jtrace, user, record_id, status, facility, since, until
        )
    )


@router.get(
    "/workitems/",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_workitems(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of work items related to a particular master record."""
    related: list[MasterRecord] = get_masterrecords_related_to_masterrecord(
        jtrace, record_id, user
    ).all()
    return get_workitems(
        jtrace, user, master_id=[record.id for record in related]
    ).all()


@router.get(
    "/persons/",
    response_model=list[PersonSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_persons(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of person records related to a particular master record."""
    # Find all related person record IDs by recursing through link records
    _, related_person_ids = find_related_ids(jtrace, {record_id}, set())
    return get_persons(jtrace, user).filter(Person.id.in_(related_person_ids)).all()


@router.get(
    "/patientrecords/",
    response_model=list[PatientRecordSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_record_patientrecords(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of patient records related to a particular master record."""
    _, related_person_ids = find_related_ids(jtrace, {record_id}, set())
    related_persons = get_persons(jtrace, user).filter(
        Person.id.in_(related_person_ids)
    )

    related_patient_ids = set()
    for person in related_persons:
        related_patient_ids.add(person.localid)

    records = get_patientrecords(ukrdc3, user).filter(
        PatientRecord.pid.in_(related_patient_ids)
    )

    return records.all()
