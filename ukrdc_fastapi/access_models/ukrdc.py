from fastapi import HTTPException
from sqlalchemy.orm import Query
from ukrdc_sqla import ukrdc

from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser


class PatientRecordAM:
    @classmethod
    def apply_query_permissions(cls, query: Query, user: UKRDCUser):
        units = Permissions.unit_codes(user.permissions)
        if Permissions.UNIT_WILDCARD in units:
            return query

        return query.filter(ukrdc.PatientRecord.sendingfacility.in_(units))

    @classmethod
    def assert_permission(cls, patient_record: ukrdc.PatientRecord, user: UKRDCUser):
        units = Permissions.unit_codes(user.permissions)
        if Permissions.UNIT_WILDCARD in units:
            return

        if patient_record.sendingfacility not in units:
            raise HTTPException(
                403,
                detail="You do not have permission to access this resource. Sending facility does not match.",
            )


class LabOrderAM:
    @classmethod
    def apply_query_permissions(cls, query: Query, user: UKRDCUser):
        units = Permissions.unit_codes(user.permissions)
        if Permissions.UNIT_WILDCARD in units:
            return query

        return query.filter(
            ukrdc.LabOrder.receiving_location.in_(units)
            | ukrdc.LabOrder.entered_at.in_(units)
            | ukrdc.LabOrder.entering_organization_code.in_(units)
        )

    @classmethod
    def assert_permission(cls, laborder: ukrdc.LabOrder, user: UKRDCUser):
        units = Permissions.unit_codes(user.permissions)
        if Permissions.UNIT_WILDCARD in units:
            return

        if not (
            laborder.receiving_location in units
            or laborder.entered_at in units
            or laborder.entering_organization_code in units
        ):
            raise HTTPException(
                403,
                detail="You do not have permission to access this resource. Sending facility does not match.",
            )


class ResultItemAM:
    @classmethod
    def apply_query_permissions(cls, query: Query, user: UKRDCUser):
        query = query.join(ukrdc.LabOrder)
        return LabOrderAM.apply_query_permissions(query, user)

    @classmethod
    def assert_permission(cls, result: ukrdc.ResultItem, user: UKRDCUser):
        laborder = result.order
        return LabOrderAM.assert_permission(laborder, user)
