from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.exceptions import RecordTypeError
from ukrdc_fastapi.query.mirth.base import safe_send_mirth_message_to_name
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema
from ukrdc_fastapi.utils.mirth.messages import (
    build_export_all_message,
    build_export_docs_message,
    build_export_radar_message,
    build_export_tests_message,
)
from ukrdc_fastapi.utils.mirth.messages.pkb import build_pkb_sync_messages
from ukrdc_fastapi.utils.mirth.messages.mrc import build_mrc_sync_message
from ukrdc_fastapi.utils.records import record_is_data


async def export_all_to_pv(
    record: PatientRecord,
    mirth: MirthAPI,
    redis: Redis,
) -> MirthMessageResponseSchema:
    """Export a specific patient's data to PV"""
    # TODO: Remove now PV is shut down
    if not record_is_data(record):
        raise RecordTypeError(
            f"Cannot export a {record.sendingfacility}/{record.sendingextract} record to PatientView"
        )

    if not record.pid:
        raise ValueError("PatientRecord has no PID")  # pragma: no cover

    return await safe_send_mirth_message_to_name(
        "PV Outbound", build_export_all_message(record.pid), mirth, redis
    )


async def export_tests_to_pv(
    record: PatientRecord,
    mirth: MirthAPI,
    redis: Redis,
) -> MirthMessageResponseSchema:
    """Export a specific patient's test data to PV"""
    # TODO: Remove now PV is shut down
    if not record_is_data(record):
        raise RecordTypeError(
            f"Cannot export a {record.sendingfacility}/{record.sendingextract} record to PatientView"
        )

    if not record.pid:
        raise ValueError("PatientRecord has no PID")  # pragma: no cover

    return await safe_send_mirth_message_to_name(
        "PV Outbound", build_export_tests_message(record.pid), mirth, redis
    )


async def export_docs_to_pv(
    record: PatientRecord,
    mirth: MirthAPI,
    redis: Redis,
) -> MirthMessageResponseSchema:
    """Export a specific patient's docs data to PV"""
    # TODO: Remove now PV is shut down
    if not record_is_data(record):
        raise RecordTypeError(
            f"Cannot export a {record.sendingfacility}/{record.sendingextract} record to PatientView"
        )

    if not record.pid:
        raise ValueError("PatientRecord has no PID")  # pragma: no cover

    return await safe_send_mirth_message_to_name(
        "PV Outbound", build_export_docs_message(record.pid), mirth, redis
    )


async def export_all_to_radar(
    record: PatientRecord,
    mirth: MirthAPI,
    redis: Redis,
) -> MirthMessageResponseSchema:
    """Export a specific patient's data to RaDaR"""
    if not record_is_data(record):
        raise RecordTypeError(
            f"Cannot export a {record.sendingfacility}/{record.sendingextract} record to RADAR"
        )

    if not record.pid:
        raise ValueError("PatientRecord has no PID")  # pragma: no cover

    return await safe_send_mirth_message_to_name(
        "RADAR Outbound", build_export_radar_message(record.pid), mirth, redis
    )


async def export_all_to_pkb(
    record: PatientRecord,
    ukrdc3: Session,
    mirth: MirthAPI,
    redis: Redis,
) -> list[MirthMessageResponseSchema]:
    """
    Export a specific patient's data to PKB.

    Notes:
    - Unlike other export functions, this sends multiple messages to Mirth
    in order to sync the patient record with PKB.
    - Because of this, it may take a while to complete.
    - Upstream functions calling export_all_to_pkb should probably run this
    function in the background (thread or asyncio etc.)
    """
    if not record_is_data(record):
        raise RecordTypeError(
            f"Cannot export a {record.sendingfacility}/{record.sendingextract} record to PKB"
        )

    messages = build_pkb_sync_messages(record, ukrdc3)

    responses: list[MirthMessageResponseSchema] = []

    for message in messages:
        responses.append(
            await safe_send_mirth_message_to_name(
                "PKB Outbound - Partner", message, mirth, redis
            )
        )

    return responses


async def export_all_to_mrc(
    record: PatientRecord,
    ukrdc3: Session,
    mirth: MirthAPI,
    redis: Redis,
) -> list[MirthMessageResponseSchema]:
    """
    Export a specific patient's data to MRC.
    """
    if not record_is_data(record):
        raise RecordTypeError(
            f"Cannot export a {record.sendingfacility}/{record.sendingextract} record to MRC"
        )

    message = build_mrc_sync_message(record, ukrdc3)

    return await safe_send_mirth_message_to_name(
        "MRC Outbound - Data - RDA", message, mirth, redis
    )
