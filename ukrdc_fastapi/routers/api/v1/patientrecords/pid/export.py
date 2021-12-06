from fastapi import APIRouter, Depends, HTTPException, Security
from mirth_client.exceptions import MirthPostError
from mirth_client.mirth import MirthAPI
from redis import Redis
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies import get_mirth, get_redis
from ukrdc_fastapi.dependencies.audit import Auditer, RecordOperation, get_auditer
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.utils.mirth import (
    MirthMessageResponseSchema,
    build_export_all_message,
    build_export_docs_message,
    build_export_radar_message,
    build_export_tests_message,
    get_channel_from_name,
)

from .dependencies import _get_patientrecord

router = APIRouter(tags=["Patient Records/Export"])


@router.post(
    "/pv/",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Export a specific patient's data to PV"""
    channel = get_channel_from_name("PV Outbound", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for PV Outbound channel not found"
        )  # pragma: no cover

    message: str = build_export_all_message(patient_record.pid)
    try:
        await channel.post_message(message)
    except MirthPostError as e:
        raise HTTPException(500, str(e)) from e  # pragma: no cover

    audit.add_patient_record(patient_record.pid, None, None, RecordOperation.EXPORT_PV)

    return MirthMessageResponseSchema(status="success", message=message)


@router.post(
    "/pv-tests/",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv_tests(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Export a specific patient's test data to PV"""
    channel = get_channel_from_name("PV Outbound", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for PV Outbound channel not found"
        )  # pragma: no cover

    message: str = build_export_tests_message(patient_record.pid)
    try:
        await channel.post_message(message)
    except MirthPostError as e:
        raise HTTPException(500, str(e)) from e  # pragma: no cover

    audit.add_patient_record(
        patient_record.pid, None, None, RecordOperation.EXPORT_PV_TESTS
    )

    return MirthMessageResponseSchema(status="success", message=message)


@router.post(
    "/pv-docs/",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv_docs(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Export a specific patient's documents data to PV"""
    channel = get_channel_from_name("PV Outbound", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for PV Outbound channel not found"
        )  # pragma: no cover

    message: str = build_export_docs_message(patient_record.pid)
    try:
        await channel.post_message(message)
    except MirthPostError as e:
        raise HTTPException(500, str(e)) from e  # pragma: no cover

    audit.add_patient_record(
        patient_record.pid, None, None, RecordOperation.EXPORT_PV_DOCS
    )

    return MirthMessageResponseSchema(status="success", message=message)


@router.post(
    "/radar/",
    response_model=MirthMessageResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_radar(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Export a specific patient's data to RaDaR"""
    channel = get_channel_from_name("RADAR Outbound", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for RADAR Outbound channel not found"
        )  # pragma: no cover

    message: str = build_export_radar_message(patient_record.pid)
    try:
        await channel.post_message(message)
    except MirthPostError as e:
        raise HTTPException(500, str(e)) from e  # pragma: no cover

    audit.add_patient_record(
        patient_record.pid, None, None, RecordOperation.EXPORT_RADAR
    )

    return MirthMessageResponseSchema(status="success", message=message)
