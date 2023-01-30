from sqlalchemy.orm.query import Query
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person, PidXRef

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.exceptions import PermissionsError
from ukrdc_fastapi.query.common import person_belongs_to_units


def assert_masterrecord_permission(record: MasterRecord, user: UKRDCUser):
    """
    Assert that the user has permission to access the given MasterRecord

    Args:
        record (MasterRecord): MasterRecord object
        user (UKRDCUser): Logged-in user

    Raises:
        PermissionsError: If the user does not have permission to access the facility
    """
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return

    link: LinkRecord
    for link in record.link_records:
        person: Person = link.person
        if person_belongs_to_units(person, units):
            return

    raise PermissionsError()


def apply_masterrecord_list_permissions(query: Query, user: UKRDCUser) -> Query:
    """
    Apply permissions to a list of MasterRecords based on the user's permissions

    Args:
        query (Query): Query of MasterRecord objects
        user (UKRDCUser): Logged-in user

    Returns:
        Query: Query of MasterRecord objects with permissions applied
    """
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return query

    return (
        query.join(LinkRecord)
        .join(Person)
        .join(PidXRef)
        .filter(PidXRef.sending_facility.in_(units))
    )
