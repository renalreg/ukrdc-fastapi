from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.query.mirth.base import safe_send_mirth_message_to_name
from ukrdc_fastapi.query.patientrecords import get_patientrecord
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema
from ukrdc_fastapi.utils.mirth.messages import (
    build_export_all_message,
    build_export_docs_message,
    build_export_radar_message,
    build_export_tests_message,
)


async def export_all_to_pv(
    pid: str,
    user: UKRDCUser,
    ukrdc3: Session,
    mirth: MirthAPI,
    redis: Redis,
) -> MirthMessageResponseSchema:
    """Export a specific patient's data to PV"""
    record: PatientRecord = get_patientrecord(ukrdc3, pid, user)
    return await safe_send_mirth_message_to_name(
        "PV Outbound", build_export_all_message(record.pid), mirth, redis
    )


async def export_tests_to_pv(
    pid: str,
    user: UKRDCUser,
    ukrdc3: Session,
    mirth: MirthAPI,
    redis: Redis,
) -> MirthMessageResponseSchema:
    """Export a specific patient's test data to PV"""
    record: PatientRecord = get_patientrecord(ukrdc3, pid, user)
    return await safe_send_mirth_message_to_name(
        "PV Outbound", build_export_tests_message(record.pid), mirth, redis
    )


async def export_docs_to_pv(
    pid: str,
    user: UKRDCUser,
    ukrdc3: Session,
    mirth: MirthAPI,
    redis: Redis,
) -> MirthMessageResponseSchema:
    """Export a specific patient's docs data to PV"""
    record: PatientRecord = get_patientrecord(ukrdc3, pid, user)
    return await safe_send_mirth_message_to_name(
        "PV Outbound", build_export_docs_message(record.pid), mirth, redis
    )


async def export_all_to_radar(
    pid: str,
    user: UKRDCUser,
    ukrdc3: Session,
    mirth: MirthAPI,
    redis: Redis,
) -> MirthMessageResponseSchema:
    """Export a specific patient's data to RaDaR"""
    record: PatientRecord = get_patientrecord(ukrdc3, pid, user)
    return await safe_send_mirth_message_to_name(
        "RADAR Outbound", build_export_radar_message(record.pid), mirth, redis
    )
