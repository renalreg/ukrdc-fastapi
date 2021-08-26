from typing import Optional

from httpx import Response
from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm.session import Session

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.exceptions import MirthChannelError, MirthPostError
from ukrdc_fastapi.query.masterrecords import get_masterrecord
from ukrdc_fastapi.query.persons import get_person, get_person_from_pid
from ukrdc_fastapi.utils.mirth import (
    MirthMessageResponseSchema,
    build_unlink_message,
    get_channel_from_name,
)


async def unlink_person_from_master_record(
    person_id: int,
    master_id: int,
    comment: Optional[str],
    user: UKRDCUser,
    jtrace: Session,
    mirth: MirthAPI,
    redis: Redis,
):
    """Unlink a particular Person record from a Master Record"""
    # Get records to assert user permission
    person = get_person(jtrace, person_id, user)
    master = get_masterrecord(jtrace, master_id, user)

    channel = get_channel_from_name("Unlink", mirth, redis)
    if not channel:
        raise MirthChannelError("ID for Unlink channel not found")  # pragma: no cover

    message: str = build_unlink_message(
        master.id, person.id, user.email, description=comment
    )

    response: Response = await channel.post_message(message)

    if response.status_code >= 400:
        raise MirthPostError(response.text)

    return MirthMessageResponseSchema(status="success", message=message)
