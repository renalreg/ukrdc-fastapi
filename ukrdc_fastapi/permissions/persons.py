from sqlalchemy.sql.selectable import Select
from ukrdc_sqla.empi import Person, PidXRef

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.exceptions import PermissionsError
from ukrdc_fastapi.query.common import person_belongs_to_units


def apply_persons_list_permission(stmt: Select, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return stmt

    return stmt.join(PidXRef).where(PidXRef.sending_facility.in_(units))


def assert_person_permission(person: Person, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return

    if person_belongs_to_units(person, units):
        return

    raise PermissionsError()
