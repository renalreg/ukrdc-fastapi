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
)

from ukrdc_fastapi.access_models.ukrdc import LabOrderAM, PatientRecordAM
from ukrdc_fastapi.dependencies import get_jtrace, get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
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


def safe_get_patient(ukrdc3: Session, pid: str, user: UKRDCUser) -> Person:
    """Return a MasterRecord by ID if it exists and the user has permission

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        pid (str): Patient ID
        user (UKRDCUser): User object

    Raises:
        HTTPException: User does not have permission to access the resource

    Returns:
        PatientRecord: PatientRecord
    """
    record = ukrdc3.query(PatientRecord).get(pid)
    if not record:
        raise HTTPException(404, detail="Record not found")
    PatientRecordAM.assert_permission(record, user)
    return record


@router.get(
    "/",
    response_model=PatientRecordSchema,
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_record(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a specific patient record"""
    record = safe_get_patient(ukrdc3, pid, user)
    return record


@router.get(
    "/related/",
    response_model=list[PatientRecordShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_related(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive patient records related to a specific patient record"""
    record = safe_get_patient(ukrdc3, pid, user)

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

    related_records = PatientRecordAM.apply_query_permissions(related_records, user)
    return related_records.all()


@router.get(
    "/laborders/",
    response_model=Page[LabOrderShortSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_laborders(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a specific patient's lab orders"""
    orders = ukrdc3.query(LabOrder).filter(LabOrder.pid == pid)
    orders = orders.order_by(LabOrder.specimen_collected_time.desc())

    orders = LabOrderAM.apply_query_permissions(orders, user)
    return paginate(orders)


@router.get(
    "/resultitems/",
    response_model=Page[ResultItemSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_resultitems(
    pid: str,
    service_id: Optional[list[str]] = QueryParam([]),
    order_id: Optional[list[str]] = QueryParam([]),
    since: Optional[datetime.datetime] = None,
    until: Optional[datetime.datetime] = None,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a specific patient's lab orders"""
    query = (
        ukrdc3.query(ResultItem).join(LabOrder.result_items).filter(LabOrder.pid == pid)
    )
    query = LabOrderAM.apply_query_permissions(query, user)

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
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_resultitems_services(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of resultitem services available for a specific patient"""
    items = (
        ukrdc3.query(ResultItem).join(LabOrder.result_items).filter(LabOrder.pid == pid)
    )
    items = LabOrderAM.apply_query_permissions(items, user)

    services = items.distinct(ResultItem.service_id)
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
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_observations(
    pid: str,
    code: Optional[list[str]] = QueryParam([]),
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a specific patient's lab orders"""
    record: PatientRecord = safe_get_patient(ukrdc3, pid, user)
    observations = record.observations

    if code:
        observations = observations.filter(Observation.observation_code.in_(code))
    observations = observations.order_by(Observation.observation_time.desc())
    return paginate(observations)


@router.get(
    "/observations/codes",
    response_model=list[str],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_observations_codes(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of observation codes available for a specific patient"""
    record: PatientRecord = safe_get_patient(ukrdc3, pid, user)
    observations = record.observations
    codes = observations.distinct(Observation.observation_code)
    return [item.observation_code for item in codes.all()]


@router.get(
    "/medications/",
    response_model=list[MedicationSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_medications(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a specific patient's medications"""
    record: PatientRecord = safe_get_patient(ukrdc3, pid, user)
    medications = record.medications
    return medications.order_by(Medication.from_time).all()


@router.get(
    "/surveys/",
    response_model=list[SurveySchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def patient_surveys(
    pid: str,
    user: UKRDCUser = Security(auth.get_user),
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a specific patient's surveys"""
    record: PatientRecord = safe_get_patient(ukrdc3, pid, user)
    return record.surveys
