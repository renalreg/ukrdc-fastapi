from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from ukrdc_sqla.empi import Person, PidXRef
from ukrdc_sqla.utils.links import find_related_ids

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.exceptions import (
    AmbigousQueryError,
    EmptyQueryError,
    ResourceNotFoundError,
)
from ukrdc_fastapi.query.common import PermissionsError, person_belongs_to_units


def _apply_query_permissions(query: Query, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return query

    return query.join(PidXRef).filter(PidXRef.sending_facility.in_(units))


def _assert_permission(person: Person, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return

    if person_belongs_to_units(person, units):
        return

    raise PermissionsError()


def get_persons(jtrace: Session, user: UKRDCUser) -> Query:
    """Get a list of Person records

    Args:
        jtrace (Session): SQLAlchemy session
        user (UKRDCUser): Logged-in user object

    Returns:
        Query: SQLAlchemy query of Person records
    """
    people = jtrace.query(Person)
    return _apply_query_permissions(people, user)


def get_person(jtrace: Session, person_id: int, user: UKRDCUser) -> Person:
    """Return a MasterRecord by ID if it exists and the user has permission

    Args:
        jtrace (Session): JTRACE SQLAlchemy session
        person_id (int): Person ID
        user (UKRDCUser): Logged-in user object

    Returns:
        Person: Person record
    """
    person = jtrace.query(Person).get(person_id)
    if not person:
        raise ResourceNotFoundError("EMPI Person not found")
    _assert_permission(person, user)
    return person


def get_person_from_pid(jtrace: Session, pid: str, user: UKRDCUser) -> Person:
    """Get a list of Person records from a given PID

    Args:
        jtrace (Session): SQLAlchemy session
        pid (str): PID to find records related to
        user (UKRDCUser): Logged-in user object

    Returns:
        Query: SQLAlchemy query of Person records
    """
    persons: list[Person] = (
        jtrace.query(Person)
        .filter(Person.localid_type == "CLPID", Person.localid == pid)
        .all()
    )
    if len(persons) > 1:
        raise AmbigousQueryError(f"Multiple Person records found for PID {pid}")
    if not persons:
        raise EmptyQueryError(f"No Person records found for PID {pid}")

    person = persons[0]
    _assert_permission(person, user)
    return person


def get_persons_related_to_masterrecord(
    jtrace: Session, record_id: int, user: UKRDCUser
) -> Query:
    """Get a list of Person records related to a given Master Record

    Args:
        jtrace (Session): SQLAlchemy session
        record_id (int): Master Record ID
        user (UKRDCUser): Logged-in user object

    Returns:
        Query: SQLAlchemy query of Person records
    """
    _, related_person_ids = find_related_ids(jtrace, {record_id}, set())
    return get_persons(jtrace, user).filter(Person.id.in_(related_person_ids))
