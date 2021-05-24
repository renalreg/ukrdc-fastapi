from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.access_models.ukrdc import PatientRecordAM
from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.schemas.patientrecord import PatientRecordShortSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

from . import pid

router = APIRouter(tags=["Patient Records"])
router.include_router(pid.router)


@router.get(
    "/",
    response_model=Page[PatientRecordShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_records(
    user: UKRDCUser = Security(auth.get_user), ukrdc3: Session = Depends(get_ukrdc3)
):
    """Retrieve a list of patient records"""

    records = ukrdc3.query(PatientRecord)

    records = PatientRecordAM.apply_query_permissions(records, user)
    return paginate(ukrdc3.query(PatientRecord))
