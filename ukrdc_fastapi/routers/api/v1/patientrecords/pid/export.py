from fastapi import APIRouter, Depends, Security
from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_mirth, get_redis, get_ukrdc3
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    RecordOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.mirth.export import (
    export_all_to_pv,
    export_all_to_radar,
    export_docs_to_pv,
    export_tests_to_pv,
)
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema

router = APIRouter(tags=["Patient Records/Export"])


@router.post(
    "/pv/",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv(
    pid: str,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Export a specific patient's data to PV"""
    response = await export_all_to_pv(pid, user, ukrdc3, mirth, redis)
    audit.add_event(Resource.PATIENT_RECORD, pid, RecordOperation.EXPORT_PV)
    return response


@router.post(
    "/pv-tests/",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv_tests(
    pid: str,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Export a specific patient's test data to PV"""
    response = await export_tests_to_pv(pid, user, ukrdc3, mirth, redis)
    audit.add_event(Resource.PATIENT_RECORD, pid, RecordOperation.EXPORT_PV_TESTS)
    return response


@router.post(
    "/pv-docs/",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv_docs(
    pid: str,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Export a specific patient's documents data to PV"""
    response = await export_docs_to_pv(pid, user, ukrdc3, mirth, redis)
    audit.add_event(Resource.PATIENT_RECORD, pid, RecordOperation.EXPORT_PV_DOCS)
    return response


@router.post(
    "/radar/",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_radar(
    pid: str,
    user: UKRDCUser = Security(auth.get_user()),
    ukrdc3: Session = Depends(get_ukrdc3),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Export a specific patient's data to RaDaR"""
    response = await export_all_to_radar(pid, user, ukrdc3, mirth, redis)
    audit.add_event(Resource.PATIENT_RECORD, pid, RecordOperation.EXPORT_RADAR)
    return response
