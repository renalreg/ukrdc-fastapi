import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Response, Security
from sqlalchemy.orm import Session
from starlette.status import HTTP_204_NO_CONTENT
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies import get_errorsdb, get_jtrace, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.masterrecords import (
    get_masterrecord,
    get_masterrecords_related_to_masterrecord,
)
from ukrdc_fastapi.query.messages import (
    ERROR_SORTER,
    get_last_message_on_masterrecord,
    get_messages_related_to_masterrecord,
)
from ukrdc_fastapi.query.patientrecords import get_patientrecords
from ukrdc_fastapi.query.persons import get_persons, get_persons_related_to_masterrecord
from ukrdc_fastapi.query.workitems import get_workitems
from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.empi import (
    LinkRecordSchema,
    MasterRecordSchema,
    PersonSchema,
    WorkItemSchema,
)
from ukrdc_fastapi.schemas.message import MessageSchema, MinimalMessageSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSchema
from ukrdc_fastapi.utils.links import find_related_ids
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.sort import Sorter


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
):
    """Retreive a particular master record from the EMPI"""
    return get_masterrecord(jtrace, record_id, user)


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
):
    """Retreive a particular master record from the EMPI"""
    record: MasterRecord = get_masterrecord(jtrace, record_id, user)

    errors = get_messages_related_to_masterrecord(
        errorsdb, jtrace, record.id, user, status="ERROR"
    )

    related_ukrdc_records = get_masterrecords_related_to_masterrecord(
        jtrace, record.id, user
    ).filter(MasterRecord.nationalid_type == "UKRDC")

    workitems = get_workitems(
        jtrace, user, master_id=[record.id for record in related_ukrdc_records.all()]
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
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_related(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of other master records related to a particular master record"""
    return get_masterrecords_related_to_masterrecord(
        jtrace, record_id, user, exclude_self=True
    ).all()


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
    status: Optional[str] = None,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    errorsdb: Session = Depends(get_errorsdb),
    sorter: Sorter = Depends(ERROR_SORTER),
):
    """
    Retreive a list of errors related to a particular master record.
    By default returns message created within the last 365 days.
    """
    query = get_messages_related_to_masterrecord(
        errorsdb, jtrace, record_id, user, status, facility, since, until
    )
    return paginate(sorter.sort(query))


@router.get(
    "/workitems/",
    response_model=list[WorkItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_workitems(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
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
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_persons(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of person records related to a particular master record."""
    return get_persons_related_to_masterrecord(jtrace, record_id, user).all()


@router.get(
    "/patientrecords/",
    response_model=list[PatientRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_record_patientrecords(
    record_id: int,
    user: UKRDCUser = Security(auth.get_user()),
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
