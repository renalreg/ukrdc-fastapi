from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord, Person

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.masterrecords import get_masterrecords
from ukrdc_fastapi.query.persons import get_person, get_persons
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter(tags=["Persons"])


@router.get(
    "/",
    response_model=Page[PersonSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def persons(
    user: UKRDCUser = Security(auth.get_user), jtrace: Session = Depends(get_jtrace)
):
    """Retreive a list of Person records from the EMPI"""
    return paginate(get_persons(jtrace, user))


@router.get(
    "/{person_id}/",
    response_model=PersonSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def person_detail(
    person_id: int,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a particular Person record from the EMPI"""
    return get_person(jtrace, person_id, user)


@router.get(
    "/{person_id}/masterrecords/",
    response_model=list[MasterRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def person_masterrecords(
    person_id: int,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive MasterRecords directly linked to a particular Person record"""
    person: Person = get_person(jtrace, person_id, user)
    related_master_ids = [link.master_id for link in person.link_records]
    return (
        get_masterrecords(jtrace, user)
        .filter(MasterRecord.id.in_(related_master_ids))
        .all()
    )
