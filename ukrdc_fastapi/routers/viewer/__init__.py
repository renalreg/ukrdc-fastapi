from ukrdc_fastapi.schemas.patientrecord import PatientRecordShortSchema
from ukrdc_fastapi.models.ukrdc import PatientNumber, PatientRecord
from typing import List
from sqlalchemy.orm import Session
from fastapi import Depends
from ukrdc_fastapi.dependencies import get_ukrdc3
from fastapi import APIRouter

from . import record

router = APIRouter()
router.include_router(record.router, prefix="/record")


@router.get("/records", response_model=List[PatientRecordShortSchema])
def patient_records(ni: str, ukrdc3: Session = Depends(get_ukrdc3)):

    # Only look for data if an NI was given
    if ni:
        pids = ukrdc3.query(PatientNumber.pid).filter(
            PatientNumber.patientid == ni,
            PatientNumber.numbertype == "NI",
        )
        if pids.count() == 0:
            return []

        # Find different ukrdcids
        query = (
            ukrdc3.query(PatientRecord.ukrdcid)
            .filter(PatientRecord.pid.in_(pids))
            .distinct()
        )

        ukrdcids = [ukrdcid for (ukrdcid,) in query.all()]

        if not ukrdcids:
            return []

        # Find all the records with ukrdc ids
        records = (
            ukrdc3.query(PatientRecord)
            .filter(PatientRecord.ukrdcid.in_(ukrdcids))
            .all()
        )
        return records

    return []
