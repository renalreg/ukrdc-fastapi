from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.permissions.facilities import assert_facility_permission
from ukrdc_fastapi.query.facilities.reports import (
    get_facility_report_cc001,
    get_facility_report_pm001,
)
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSummarySchema
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter(tags=["Facilities/Reports"], prefix="/{code}/reports")

# Custom cohorts


@router.get(
    "/cc001",
    response_model=Page[PatientRecordSummarySchema],
    dependencies=[
        Security(auth.permission(Permissions.READ_RECORDS)),
        Security(auth.permission(Permissions.READ_REPORTS)),
    ],
)
def facility_reports_cc001(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    user: UKRDCUser = Security(auth.get_user()),
):
    """
    Custom Cohort Report 001:
        No treatment or programme membership to explain presence of record in the UKRDC
    """
    assert_facility_permission(code, user)

    return paginate(get_facility_report_cc001(ukrdc3, code))


# Program memberships


@router.get(
    "/pm001",
    response_model=Page[PatientRecordSummarySchema],
    dependencies=[
        Security(auth.permission(Permissions.READ_RECORDS)),
        Security(auth.permission(Permissions.READ_REPORTS)),
    ],
)
def facility_reports_pm001(
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    user: UKRDCUser = Security(auth.get_user()),
):
    """
    Program Membership Report 001:
        Patients with no *active* PKB membership record
    """
    assert_facility_permission(code, user)

    return paginate(get_facility_report_pm001(ukrdc3, code))
