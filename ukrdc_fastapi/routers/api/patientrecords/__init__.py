from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.schemas.patientrecord import PatientRecordShortSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

from . import pid

router = APIRouter(tags=["Patient Records"])
router.include_router(pid.router)


@router.get(
    "/",
    response_model=Page[PatientRecordShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_PATIENTRECORDS))],
)
def patient_records(ukrdc3: Session = Depends(get_ukrdc3)):
    """Retrieve a list of patient records"""
    return paginate(ukrdc3.query(PatientRecord))
