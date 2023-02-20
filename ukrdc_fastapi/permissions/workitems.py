from sqlalchemy.orm.query import Query
from ukrdc_sqla.empi import Person, PidXRef, WorkItem

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.exceptions import PermissionsError
from ukrdc_fastapi.query.common import person_belongs_to_units


def apply_workitem_list_permission(query: Query, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return query

    return query.join(Person).join(PidXRef).filter(PidXRef.sending_facility.in_(units))


def assert_workitem_permission(workitem: WorkItem, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return

    person: Person = workitem.person
    if person_belongs_to_units(person, units):
        return

    raise PermissionsError()
