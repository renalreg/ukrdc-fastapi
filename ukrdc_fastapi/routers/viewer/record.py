from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.models.ukrdc import LabOrder, PatientRecord
from ukrdc_fastapi.schemas.laborder import LabOrderShortSchema
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSchema

router = APIRouter()


@router.get("/{pid}", response_model=PatientRecordSchema)
def patient_records(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    record = ukrdc3.query(PatientRecord).filter(PatientRecord.pid == pid).first()
    if not record:
        raise HTTPException(404, detail="Record not found")
    return record


@router.get("/{pid}/laborders", response_model=List[LabOrderShortSchema])
def patient_laborders(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    laborders = ukrdc3.query(LabOrder).filter(LabOrder.pid == pid)
    return laborders.order_by(LabOrder.specimen_collected_time.desc()).all()
