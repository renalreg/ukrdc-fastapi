from fastapi import APIRouter, Depends, Security
from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies import get_mirth, get_redis, get_ukrdc3
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.query.mirth.export import (
    export_all_to_pkb,
    export_all_to_pv,
    export_all_to_radar,
    export_docs_to_pv,
    export_tests_to_pv,
    export_all_to_mrc,
)
from ukrdc_fastapi.schemas.export import ExportResponseSchema

from .dependencies import _get_patientrecord

router = APIRouter(tags=["Patient Records/Export"])


@router.post(
    "/pv",
    response_model=ExportResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Export a specific patient's data to PV"""
    response = await export_all_to_pv(patient_record, mirth, redis)
    audit.add_event(
        Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.EXPORT_PV
    )

    return ExportResponseSchema(status=response.status, number_of_messages=1)


@router.post(
    "/pv-tests",
    response_model=ExportResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv_tests(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Export a specific patient's test data to PV"""
    response = await export_tests_to_pv(patient_record, mirth, redis)
    audit.add_event(
        Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.EXPORT_PV_TESTS
    )

    return ExportResponseSchema(status=response.status, number_of_messages=1)


@router.post(
    "/pv-docs",
    response_model=ExportResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pv_docs(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Export a specific patient's documents data to PV"""
    response = await export_docs_to_pv(patient_record, mirth, redis)
    audit.add_event(
        Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.EXPORT_PV_DOCS
    )

    return ExportResponseSchema(status=response.status, number_of_messages=1)


@router.post(
    "/radar",
    response_model=ExportResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_radar(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """Export a specific patient's data to RaDaR"""
    response = await export_all_to_radar(patient_record, mirth, redis)
    audit.add_event(
        Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.EXPORT_RADAR
    )

    return ExportResponseSchema(status=response.status, number_of_messages=1)


@router.post(
    "/pkb",
    response_model=ExportResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_pkb(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    ukrdc3: Session = Depends(get_ukrdc3),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """
    Export a specific patient's data to PKB.
    """
    response = await export_all_to_pkb(patient_record, ukrdc3, mirth, redis)
    audit.add_event(
        Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.EXPORT_PKB
    )

    combined_status = (
        "success"
        if all(response.status == "success" for response in response)
        else "fail"
    )

    return ExportResponseSchema(
        status=combined_status, number_of_messages=len(response)
    )


@router.post(
    "/mrc",
    response_model=ExportResponseSchema,
    dependencies=[Security(auth.permission(Permissions.EXPORT_RECORDS))],
)
async def patient_export_mrc(
    patient_record: PatientRecord = Depends(_get_patientrecord),
    ukrdc3: Session = Depends(get_ukrdc3),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
    audit: Auditer = Depends(get_auditer),
):
    """
    Export a specific patient's data to PKB.
    """

    response = await export_all_to_mrc(patient_record, ukrdc3, mirth, redis)

    audit.add_event(
        Resource.PATIENT_RECORD, patient_record.pid, AuditOperation.EXPORT_MRC
    )

    return ExportResponseSchema(status=response.status, number_of_messages=1)
