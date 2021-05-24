from fastapi import HTTPException
from sqlalchemy.orm import Query
from ukrdc_sqla import errorsdb

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser


class MessageAM:
    @classmethod
    def apply_query_permissions(cls, query: Query, user: UKRDCUser):
        units = Permissions.unit_codes(user.permissions)
        if Permissions.UNIT_WILDCARD in units:
            return query

        return query.filter(errorsdb.Message.facility.in_(units))

    @classmethod
    def assert_permission(cls, message: errorsdb.Message, user: UKRDCUser):
        units = Permissions.unit_codes(user.permissions)
        if Permissions.UNIT_WILDCARD in units:
            return

        if message.facility not in units:
            raise HTTPException(
                403,
                detail="You do not have permission to access this resource. Sending facility does not match.",
            )
