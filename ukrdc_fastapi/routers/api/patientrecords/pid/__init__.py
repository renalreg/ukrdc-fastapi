import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query as QueryParam
from fastapi import Security
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import Person
from ukrdc_sqla.ukrdc import (
    LabOrder,
    Medication,
    Observation,
    PatientRecord,
    ResultItem,
    Survey,
)

from ukrdc_fastapi.dependencies import get_jtrace, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.schemas.laborder import (
    LabOrderShortSchema,
    ResultItemSchema,
    ResultItemServiceSchema,
)
from ukrdc_fastapi.schemas.medication import MedicationSchema
from ukrdc_fastapi.schemas.observation import ObservationSchema
from ukrdc_fastapi.schemas.patientrecord import (
    PatientRecordSchema,
    PatientRecordShortSchema,
)
from ukrdc_fastapi.schemas.survey import SurveySchema
from ukrdc_fastapi.utils.filters.empi import find_related_ids
from ukrdc_fastapi.utils.paginate import Page, paginate

from . import export

router = APIRouter(prefix="/{pid}")
router.include_router(export.router, prefix="/export")


@router.get(
    "/",
    response_model=PatientRecordSchema,
    dependencies=[Security(auth.permission(Permissions.READ_PATIENTRECORDS))],
)
def patient_record(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    """Retreive a specific patient record"""
    record = ukrdc3.query(PatientRecord).filter(PatientRecord.pid == pid).first()
    if not record:
        raise HTTPException(404, detail="Record not found")
    return record


@router.get(
    "/related/",
    response_model=list[PatientRecordShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_PATIENTRECORDS))],
)
def patient_related(
    pid: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive patient records related to a specific patient record"""
    record = ukrdc3.query(PatientRecord).filter(PatientRecord.pid == pid).first()
    if not record:
        raise HTTPException(404, detail="Record not found")

    # Get Person records directly related to the Patient Record
    record_persons = jtrace.query(Person).filter(Person.localid == record.pid)

    # Find all Person IDs indirectly related to the Person record
    _, related_person_ids = find_related_ids(
        jtrace, set(), {related_person.id for related_person in record_persons}
    )
    # Find all Person records in the list of related Person IDs
    related_persons = jtrace.query(Person).filter(Person.id.in_(related_person_ids))

    # Find all Patient IDs from the related Person records
    related_patient_ids = {person.localid for person in related_persons}

    # Find all Patient records in the list of related Patient IDs
    related_records = ukrdc3.query(PatientRecord).filter(
        PatientRecord.pid.in_(related_patient_ids)
    )

    return related_records.all()


@router.get(
    "/laborders/",
    response_model=Page[LabOrderShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_PATIENTRECORDS))],
)
def patient_laborders(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    """Retreive a specific patient's lab orders"""
    orders = ukrdc3.query(LabOrder).filter(LabOrder.pid == pid)
    orders = orders.order_by(LabOrder.specimen_collected_time.desc())
    return paginate(orders)


@router.get(
    "/resultitems/",
    response_model=Page[ResultItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_PATIENTRECORDS))],
)
def patient_resultitems(
    pid: str,
    service_id: Optional[list[str]] = QueryParam([]),
    order_id: Optional[list[str]] = QueryParam([]),
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a specific patient's lab orders"""
    query = (
        ukrdc3.query(ResultItem).join(LabOrder.result_items).filter(LabOrder.pid == pid)
    )

    if service_id:
        query = query.filter(ResultItem.service_id.in_(service_id))
    if order_id:
        query = query.filter(ResultItem.order_id.in_(order_id))
    if since:
        query = query.filter(ResultItem.observation_time >= since)
    if until:
        query = query.filter(ResultItem.observation_time <= until)

    items = query.order_by(ResultItem.observation_time.desc())
    return paginate(items)


@router.get(
    "/resultitems/services",
    response_model=list[ResultItemServiceSchema],
    dependencies=[Security(auth.permission(Permissions.READ_PATIENTRECORDS))],
)
def patient_resultitems_services(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    """Retreive a list of resultitem services available for a specific patient"""
    services = (
        ukrdc3.query(ResultItem)
        .join(LabOrder.result_items)
        .filter(LabOrder.pid == pid)
        .distinct(ResultItem.service_id)
    )
    return [
        ResultItemServiceSchema(
            id=item.service_id,
            description=item.service_id_description,
            standard=item.service_id_std,
        )
        for item in services.all()
    ]


@router.get(
    "/observations/",
    response_model=Page[ObservationSchema],
    dependencies=[Security(auth.permission(Permissions.READ_PATIENTRECORDS))],
)
def patient_observations(
    pid: str,
    code: Optional[list[str]] = QueryParam([]),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a specific patient's lab orders"""
    observations = ukrdc3.query(Observation).filter(Observation.pid == pid)
    if code:
        observations = observations.filter(Observation.observation_code.in_(code))
    observations = observations.order_by(Observation.observation_time.desc())
    return paginate(observations)


@router.get(
    "/observations/codes",
    response_model=list[str],
    dependencies=[Security(auth.permission(Permissions.READ_PATIENTRECORDS))],
)
def patient_observations_codes(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    """Retreive a list of observation codes available for a specific patient"""
    codes = (
        ukrdc3.query(Observation.observation_code, Observation.pid)
        .filter(Observation.pid == pid)
        .distinct(Observation.observation_code)
    )
    return [item.observation_code for item in codes.all()]


@router.get(
    "/medications/",
    response_model=list[MedicationSchema],
    dependencies=[Security(auth.permission(Permissions.READ_PATIENTRECORDS))],
)
def patient_medications(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    """Retreive a specific patient's medications"""
    medications = ukrdc3.query(Medication).filter(Medication.pid == pid)
    return medications.order_by(Medication.from_time).all()


@router.get(
    "/surveys/",
    response_model=list[SurveySchema],
    dependencies=[Security(auth.permission(Permissions.READ_PATIENTRECORDS))],
)
def patient_surveys(pid: str, ukrdc3: Session = Depends(get_ukrdc3)):
    """Retreive a specific patient's surveys"""
    surveys = ukrdc3.query(Survey).filter(Survey.pid == pid)
    return surveys.order_by(Survey.surveytime.desc()).all()
