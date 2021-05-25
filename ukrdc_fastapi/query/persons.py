from fastapi import HTTPException
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import Person

from ukrdc_fastapi.access_models.empi import PersonAM
from ukrdc_fastapi.dependencies.auth import UKRDCUser


def get_persons(jtrace: Session, user: UKRDCUser):
    people = jtrace.query(Person)
    return PersonAM.apply_query_permissions(people, user)


def get_person(jtrace: Session, person_id: str, user: UKRDCUser) -> Person:
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
