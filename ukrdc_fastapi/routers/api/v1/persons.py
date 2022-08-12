from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord, Person

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.masterrecords import get_masterrecords
from ukrdc_fastapi.query.persons import get_person
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema

router = APIRouter(tags=["Persons"])


@router.get(
    "/{person_id}/",
    response_model=PersonSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def person(
    person_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive a particular Person record from the EMPI"""
    person = get_person(jtrace, person_id, user)
    audit.add_event(Resource.PERSON, person.id, AuditOperation.READ)
    return person


@router.get(
    "/{person_id}/masterrecords/",
    response_model=list[MasterRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def person_masterrecords(
    person_id: int,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    audit: Auditer = Depends(get_auditer),
):
    """Retreive MasterRecords directly linked to a particular Person record"""
    person: Person = get_person(jtrace, person_id, user)
    related_master_ids = [link.master_id for link in person.link_records]
    records = (
        get_masterrecords(jtrace, user)
        .filter(MasterRecord.id.in_(related_master_ids))
        .all()
    )

    for record in records:
        audit.add_event(Resource.MASTER_RECORD, record.id, AuditOperation.READ)

    return records
