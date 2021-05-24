from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from sqlalchemy.orm import Query as OrmQuery
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import Person

from ukrdc_fastapi.access_models.empi import MasterRecordAM, PersonAM
from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema
from ukrdc_fastapi.utils.filters.empi import find_masterrecords_related_to_person
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


def safe_get_person(jtrace: Session, person_id: str, user: UKRDCUser) -> Person:
    """Return a MasterRecord by ID if it exists and the user has permission

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        person_id (str): Person ID
        user (UKRDCUser): User object

    Raises:
        HTTPException: User does not have permission to access the resource

    Returns:
        Person: Person
    """
    person = jtrace.query(Person).get(person_id)
    if not person:
        raise HTTPException(404, detail="EMPI Person not found")
    PersonAM.assert_permission(person, user)
    return person


@router.get(
    "/",
    response_model=Page[PersonSchema],
    dependencies=[Security(auth.permission(Permissions.READ_EMPI))],
)
def persons(
    user: UKRDCUser = Security(auth.get_user), jtrace: Session = Depends(get_jtrace)
):
    """Retreive a list of person records from the EMPI"""
    people: OrmQuery = jtrace.query(Person)

    people = PersonAM.apply_query_permissions(people, user)
    return paginate(people)


@router.get(
    "/{person_id}/",
    response_model=PersonSchema,
    dependencies=[Security(auth.permission(Permissions.READ_EMPI))],
)
def person_detail(
    person_id: str,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a particular person record from the EMPI"""
    person = safe_get_person(jtrace, person_id, user)
    return person


@router.get(
    "/{person_id}/masterrecords/",
    response_model=list[MasterRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_EMPI))],
)
def person_masterrecords(
    person_id: str,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a particular person record from the EMPI"""
    person = safe_get_person(jtrace, person_id, user)

    records = find_masterrecords_related_to_person(person, jtrace)

    records = MasterRecordAM.apply_query_permissions(records, user)
    return records.all()
