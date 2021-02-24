from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Query, Session

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.models.ukrdc import (
    LabOrder,
    Medication,
    Observation,
    PatientRecord,
    Survey,
)
from ukrdc_fastapi.schemas.laborder import LabOrderShortSchema
from ukrdc_fastapi.schemas.medication import MedicationSchema
from ukrdc_fastapi.schemas.observation import ObservationSchema
from ukrdc_fastapi.schemas.patientrecord import (
    PatientRecordSchema,
    PatientRecordShortSchema,
)
from ukrdc_fastapi.schemas.survey import SurveySchema
from ukrdc_fastapi.utils import filter, post_mirth_message_and_catch
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


class ExportResponseSchema(BaseModel):
    """Response schema for data export view"""

    status: str
    message: str


class ExportRequestSchema(BaseModel):
    data: str
    path: str
    mirth: Optional[bool] = True


# Mirth export message templates
EXPORT_TEMPLATES = {
    "FULL_PV_TESTS_EXTRACT_TEMPLATE": (
        "<result><pid>{pid}</pid><tests>FULL</tests></result>"
    ),
    "FULL_PV_DOCUMENTS_EXTRACT_TEMPLATE": (
        "<result><pid>{pid}</pid><documents>FULL</documents></result>"
    ),
    "FULL_PV_EXTRACT_TEMPLATE": "<result><pid>{pid}</pid><tests>FULL</tests><documents>FULL</documents></result>",
    "RADAR_EXTRACT_TEMPLATE": "<result><pid>{pid}</pid></result>",
}


@router.get("/", response_model=Page[PatientRecordShortSchema])
def patient_records(ni: Optional[str] = None, ukrdc3: Session = Depends(get_ukrdc3)):
    records: Query = ukrdc3.query(PatientRecord)
    if ni:
        # Find all the records with ukrdc ids
        records = filter.patientrecords_by_ni(ukrdc3, records, ni)

    # Return page
    return paginate(records)


@router.get("/{pid}", response_model=PatientRecordSchema)
def patient_record(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    record = ukrdc3.query(PatientRecord).filter(PatientRecord.pid == pid).first()
    if not record:
        raise HTTPException(404, detail="Record not found")
    return record


@router.get("/{pid}/laborders", response_model=List[LabOrderShortSchema])
def patient_laborders(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    laborders = ukrdc3.query(LabOrder).filter(LabOrder.pid == pid)
    items: List[LabOrder] = laborders.order_by(
        LabOrder.specimen_collected_time.desc()
    ).all()
    return items


@router.get("/{pid}/observations", response_model=List[ObservationSchema])
def patient_observations(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    observations = ukrdc3.query(Observation).filter(Observation.pid == pid)
    return observations.order_by(Observation.observation_time.desc()).all()


@router.get("/{pid}/medications", response_model=List[MedicationSchema])
def patient_medications(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    medications = ukrdc3.query(Medication).filter(Medication.pid == pid)
    return medications.order_by(Medication.from_time).all()


@router.get("/{pid}/surveys", response_model=List[SurveySchema])
def patient_surveys(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    surveys = ukrdc3.query(Survey).filter(Survey.pid == pid)
    return surveys.order_by(Survey.surveytime).all()


@router.post("/{pid}/export-data", response_model=ExportResponseSchema)
def patient_export(pid: str, args: ExportRequestSchema):
    # Fetch the relevant template
    template: Optional[str] = EXPORT_TEMPLATES.get(args.data, "")
    if not template:
        raise HTTPException(400, detail=f"Unknown export data operation {args.data}")
    message: str = template.format(pid=pid)

    return post_mirth_message_and_catch(args.path, message.strip(), args.mirth)
