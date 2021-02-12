from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.models.ukrdc import Name, PatientRecord
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSchema

router = APIRouter()


@router.get("/{pid}", response_model=PatientRecordSchema)
def patient_records(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    response = ukrdc3.query(PatientRecord).filter(PatientRecord.pid == pid).first()
    return response
