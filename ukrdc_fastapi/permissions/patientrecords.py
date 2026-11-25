from sqlalchemy import and_, exists, literal, or_, select
from sqlalchemy.orm import aliased
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.selectable import Select
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
        stmt = select(PatientRecord).where(PatientRecord.ukrdcid == record.ukrdcid)
        stmt = apply_patientrecord_list_permission(stmt, user)

        # Execute the statement and fetch all rows
        allowed_related_records = ukrdc3.scalars(stmt).all()

        # If the user has explicit permission to access another record with the same UKRDCID
        if record.pid in (record.pid for record in allowed_related_records):
            return

    raise PermissionsError()


def apply_patientrecord_list_permission(stmt: Select, user: UKRDCUser):
    """
    Filter a query of PatientRecords down to those the user can access.

    For queries across many patients, call restrict_records_to_accessible_patients
    first, or other patients' membership/informational records may be included.
    """
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return stmt

    # Find which records the user has explicit facility-permission to access
    stmt_explicit_permissions = stmt.where(PatientRecord.sendingfacility.in_(units))

    # Create a subquery to check if there are any rows that match the first condition
    subquery = (
        select(literal(1)).select_from(stmt_explicit_permissions.alias()).limit(1)
    )

    # Add the second condition if there are any rows that match the first condition
    return stmt.where(
        or_(
            PatientRecord.sendingfacility.in_(units),
            and_(
                exists(subquery),
                PatientRecord.sendingfacility.in_(ABSTRACT_FACILITIES),
            ),
        )
    )


def restrict_records_to_accessible_patients(stmt: Select, user: UKRDCUser):
    """
    Restrict a query of PatientRecords to patients (UKRDC IDs) with at least
    one record at one of the user's units.
    """
    units = Permissions.unit_codes(user.permissions)
    if Permissions.UNIT_WILDCARD in units:
        return stmt

    unit_record = aliased(PatientRecord)
    return stmt.where(
        exists().where(
            unit_record.ukrdcid == PatientRecord.ukrdcid,
            unit_record.sendingfacility.in_(units),
        )
    )
