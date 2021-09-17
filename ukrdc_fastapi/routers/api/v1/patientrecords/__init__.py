from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.patientrecords import get_patientrecords
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSummarySchema
from ukrdc_fastapi.utils.paginate import Page, paginate

from . import pid

router = APIRouter(tags=["Patient Records"])
router.include_router(pid.router)


@router.get(
    "/",
    response_model=Page[PatientRecordSummarySchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_records(
    user: UKRDCUser = Security(auth.get_user()), ukrdc3: Session = Depends(get_ukrdc3)
):
    """Retrieve a list of patient records"""
    return paginate(get_patientrecords(ukrdc3, user))
