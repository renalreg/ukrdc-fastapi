from httpx import Response
from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.exceptions import MirthChannelError, MirthPostError
from ukrdc_fastapi.query.masterrecords import get_masterrecord
from ukrdc_fastapi.utils.mirth import (
    MirthMessageResponseSchema,
    build_merge_message,
    get_channel_from_name,
)


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

    channel = get_channel_from_name("Merge Patient", mirth, redis)
    if not channel:
        raise MirthChannelError(
            "ID for Merge Patient channel not found"
        )  # pragma: no cover

    message: str = build_merge_message(
        superseding=superseding.id, superseded=superseded.id
    )

    response: Response = await channel.post_message(message)

    if response.status_code >= 400:
        raise MirthPostError(response.text)

    return MirthMessageResponseSchema(status="success", message=message)
