import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Security
from mirth_client.mirth import MirthAPI
from redis import Redis
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies import get_mirth, get_redis
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    RecordOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.query.mirth.rda import update_patient_demographics
from ukrdc_fastapi.schemas.base import JSONModel
from ukrdc_fastapi.schemas.patient import AddressSchema, GenderType, NameSchema
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema

from .dependencies import _get_patientrecord

router = APIRouter(tags=["Patient Records/Update"])


class DemographicUpdateSchema(JSONModel):
    name: Optional[NameSchema]
    birth_time: Optional[datetime.date]
    gender: Optional[GenderType]
    address: Optional[AddressSchema]


@router.post(
    "/demographics/",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(Permissions.WRITE_RECORDS))],
)
async def patient_update_demographics(
    demographics: DemographicUpdateSchema,
    patient_record: PatientRecord = Depends(_get_patientrecord),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """
    Update the demographic data of a given patient record

    Args:
        demographics (DemographicUpdateSchema): [description]
        patient_record (PatientRecord, optional): [description]. Defaults to Depends(_get_patientrecord).
        mirth (MirthAPI, optional): [description]. Defaults to Depends(get_mirth).
        redis (Redis, optional): [description]. Defaults to Depends(get_redis).
        audit (Auditer, optional): [description]. Defaults to Depends(get_auditer).

    Returns:
        [type]: [description]
    """
    response = await update_patient_demographics(
        patient_record,
        demographics.name,
        demographics.birth_time,
        demographics.gender,
        demographics.address,
        mirth,
        redis,
    )
    audit.add_event(Resource.PATIENT_RECORD, patient_record.pid, RecordOperation.UPDATE)
    return response
