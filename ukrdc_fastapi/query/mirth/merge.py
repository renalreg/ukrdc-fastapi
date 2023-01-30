from mirth_client.mirth import MirthAPI
from redis import Redis
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.query.mirth.base import safe_send_mirth_message_to_name
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema
from ukrdc_fastapi.utils.mirth.messages import build_merge_message


async def merge_master_records(
    superseding: MasterRecord,
    superseded: MasterRecord,
    mirth: MirthAPI,
    redis: Redis,
) -> MirthMessageResponseSchema:
    """Merge a pair of MasterRecords"""
    return await safe_send_mirth_message_to_name(
        "Merge Patient",
        build_merge_message(superseding=superseding.id, superseded=superseded.id),
        mirth,
        redis,
    )
