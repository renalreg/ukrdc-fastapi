from sqlalchemy import or_
from sqlalchemy.orm import Query
from sqlalchemy.orm.session import Session
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser
from ukrdc_fastapi.exceptions import PermissionsError
from ukrdc_fastapi.utils.records import ABSTRACT_FACILITIES


def assert_patientrecord_permission(
    record: PatientRecord, ukrdc3: Session, user: UKRDCUser
):
    units = Permissions.unit_codes(user.permissions)

    # If the user has full admin permissions, return success
    if Permissions.UNIT_WILDCARD in units:
        return

    # Else, if the user has explicit facility-permission to access the record, return success
    if record.sendingfacility in units:
        return

    # Otherwise, we have a more complicated situation like a multi-facility record.
    # We lean on our ability to determine permissions of groups of records
    if record.ukrdcid:
        related_related_records = ukrdc3.query(PatientRecord).filter(
            PatientRecord.ukrdcid == record.ukrdcid
        )
        allowed_related_records = apply_patientrecord_list_permission(
            related_related_records, user
        )

        # If the user has explicit permission to access another record with the same UKRDCID
        if record.pid in (record.pid for record in allowed_related_records):
            return

    raise PermissionsError()


def apply_patientrecord_list_permission(query: Query, user: UKRDCUser):
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return query

    # Find which records the user has explicit facility-permission to access
    query = query.filter(PatientRecord.sendingfacility.in_(units))

    # If the user doesn't have permission to see any, return the currently-empty query
    if query.count() < 1:
        return query

    # Else, if the user has explicit facility-permission to see more than 1 matching record,
    # include multi-facility records like membership and informational records
    return query.filter(
        or_(
            PatientRecord.sendingfacility.in_(units),
            PatientRecord.sendingfacility.in_(ABSTRACT_FACILITIES),
        )
    )
