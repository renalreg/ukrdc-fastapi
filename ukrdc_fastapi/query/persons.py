from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.empi import Person, PidXRef

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser


def _apply_query_permissions(query: Query, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return query

    return query.join(PidXRef).filter(PidXRef.sending_facility.in_(units))


def _assert_permission(person: Person, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return

    xref: PidXRef
    for xref in person.xref_entries:
        if xref.sending_facility in units:
            return

    raise HTTPException(
        403,
        detail="You do not have permission to access this resource. Sending facility does not match.",
    )


def get_persons(jtrace: Session, user: UKRDCUser):
    people = jtrace.query(Person)
    return _apply_query_permissions(people, user)


def get_person(jtrace: Session, person_id: int, user: UKRDCUser) -> Person:
    """Return a MasterRecord by ID if it exists and the user has permission

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        person_id (int): Person ID
        user (UKRDCUser): User object

    Raises:
        HTTPException: User does not have permission to access the resource

    Returns:
        Person: Person
    """
    person = jtrace.query(Person).get(person_id)
    if not person:
        raise HTTPException(404, detail="EMPI Person not found")
    _assert_permission(person, user)
    return person
