from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from httpx import Response
from mirth_client import Channel
from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm import Query, Session
from ukrdc_sqla.ukrdc import LabOrder, Medication, Observation, PatientRecord, Survey

from ukrdc_fastapi.auth import Auth0User, Scopes, Security, auth
from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies import get_mirth, get_redis, get_ukrdc3
from ukrdc_fastapi.schemas.laborder import LabOrderSchema, LabOrderShortSchema
from ukrdc_fastapi.schemas.medication import MedicationSchema
from ukrdc_fastapi.schemas.observation import ObservationSchema
from ukrdc_fastapi.schemas.patientrecord import (
    PatientRecordSchema,
    PatientRecordShortSchema,
)
from ukrdc_fastapi.schemas.survey import SurveySchema
from ukrdc_fastapi.utils import filters
from ukrdc_fastapi.utils.mirth import (
    MirthMessageResponseSchema,
    build_export_all_message,
    build_export_docs_message,
    build_export_radar_message,
    build_export_tests_message,
    get_channel_from_name,
)
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


@router.get("/", response_model=Page[PatientRecordShortSchema])
def patient_records(
    ni: Optional[str] = None,
    ukrdc3: Session = Depends(get_ukrdc3),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_PATIENTRECORDS]),
):
    """Retrieve a list of patient records"""
    records: Query = ukrdc3.query(PatientRecord)
    if ni:
        # Find all the records with ukrdc ids
        records = filters.patientrecords_by_ni(ukrdc3, records, ni)

    # Return page
    return paginate(records)


@router.get("/{pid}/", response_model=PatientRecordSchema)
def patient_record(
    pid: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_PATIENTRECORDS]),
):
    """Retreive a specific patient record"""
    record = ukrdc3.query(PatientRecord).filter(PatientRecord.pid == pid).first()
    if not record:
        raise HTTPException(404, detail="Record not found")
    return record


@router.get("/{pid}/laborders/", response_model=list[LabOrderSchema])
def patient_laborders(
    pid: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_PATIENTRECORDS]),
):
    """Retreive a specific patient's lab orders"""
    orders = ukrdc3.query(LabOrder).filter(LabOrder.pid == pid)
    items: list[LabOrder] = orders.order_by(
        LabOrder.specimen_collected_time.desc()
    ).all()
    return items


@router.get("/{pid}/observations/", response_model=list[ObservationSchema])
def patient_observations(
    pid: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_PATIENTRECORDS]),
):
    """Retreive a specific patient's lab orders"""
    observations = ukrdc3.query(Observation).filter(Observation.pid == pid)
    return observations.order_by(Observation.observation_time.desc()).all()


@router.get("/{pid}/medications/", response_model=list[MedicationSchema])
def patient_medications(
    pid: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_PATIENTRECORDS]),
):
    """Retreive a specific patient's medications"""
    medications = ukrdc3.query(Medication).filter(Medication.pid == pid)
    return medications.order_by(Medication.from_time).all()


@router.get("/{pid}/surveys/", response_model=list[SurveySchema])
def patient_surveys(
    pid: str,
    ukrdc3: Session = Depends(get_ukrdc3),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_PATIENTRECORDS]),
):
    """Retreive a specific patient's surveys"""
    surveys = ukrdc3.query(Survey).filter(Survey.pid == pid)
    return surveys.order_by(Survey.surveytime.desc()).all()


@router.post("/{pid}/export-pv/", response_model=MirthMessageResponseSchema)
async def patient_export_pv(
    pid: str,
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    _: Auth0User = Security(
        auth.get_user, scopes=[Scopes.READ_PATIENTRECORDS, Scopes.WRITE_MIRTH]
    ),
):
    """Export a specific patient's data to PV"""
    channel = await get_channel_from_name("PV Outbound", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for PV Outbound channel not found"
        )  # pragma: no cover

    message: str = build_export_all_message(pid)

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


@router.post("/{pid}/export-pv-tests/", response_model=MirthMessageResponseSchema)
async def patient_export_pv_tests(
    pid: str,
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    _: Auth0User = Security(
        auth.get_user, scopes=[Scopes.READ_PATIENTRECORDS, Scopes.WRITE_MIRTH]
    ),
):
    """Export a specific patient's test data to PV"""
    channel = await get_channel_from_name("PV Outbound", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for PV Outbound channel not found"
        )  # pragma: no cover

    message: str = build_export_tests_message(pid)

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


@router.post("/{pid}/export-pv-docs/", response_model=MirthMessageResponseSchema)
async def patient_export_pv_docs(
    pid: str,
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    _: Auth0User = Security(
        auth.get_user, scopes=[Scopes.READ_PATIENTRECORDS, Scopes.WRITE_MIRTH]
    ),
):
    """Export a specific patient's documents data to PV"""
    channel = await get_channel_from_name("PV Outbound", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for PV Outbound channel not found"
        )  # pragma: no cover

    message: str = build_export_docs_message(pid)

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


@router.post("/{pid}/export-radar/", response_model=MirthMessageResponseSchema)
async def patient_export_radar(
    pid: str,
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    _: Auth0User = Security(
        auth.get_user, scopes=[Scopes.READ_PATIENTRECORDS, Scopes.WRITE_MIRTH]
    ),
):
    """Export a specific patient's data to RaDaR"""
    channel = await get_channel_from_name("RADAR Outbound", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for RADAR Outbound channel not found"
        )  # pragma: no cover

    message: str = build_export_radar_message(pid)

    response: Response = await channel.post_message(message)

    if response.status_code != 204:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)
