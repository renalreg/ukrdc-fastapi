from sqlalchemy.orm.query import Query
from ukrdc_sqla.errorsdb import Message

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.exceptions import PermissionsError


def apply_message_list_permissions(query: Query, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return query

    return query.filter(Message.facility.in_(units))


def assert_message_permissions(message: Message, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return

    if message.facility not in units:
        raise PermissionsError()
