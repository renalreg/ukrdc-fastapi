from sqlalchemy.sql.selectable import Select
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.exceptions import PermissionsError


def apply_message_list_permissions(stmt: Select, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return stmt

    return stmt.where(Message.facility.in_(units))


def assert_message_permissions(message: Message, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return

    if message.facility not in units:
        raise PermissionsError()
