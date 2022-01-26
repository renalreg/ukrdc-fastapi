from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.query.masterrecords import get_masterrecord
from ukrdc_fastapi.query.mirth.base import safe_send_mirth_message_to_name
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema
from ukrdc_fastapi.utils.mirth.messages import build_merge_message


async def merge_master_records(
    superseding_id: int,
    superseded_id: int,
    user: UKRDCUser,
    jtrace: Session,
    mirth: MirthAPI,
    redis: Redis,
) -> MirthMessageResponseSchema:
    """Merge a pair of MasterRecords"""
    superseding: MasterRecord = get_masterrecord(jtrace, superseding_id, user)
    superseded: MasterRecord = get_masterrecord(jtrace, superseded_id, user)

    return await safe_send_mirth_message_to_name(
        "Merge Patient",
        build_merge_message(superseding=superseding.id, superseded=superseded.id),
        mirth,
        redis,
    )
