from asyncio import sleep
from typing import Optional

from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import LinkRecord, MasterRecord, Person

from ukrdc_fastapi.query.mirth.base import safe_send_mirth_message_to_name
from ukrdc_fastapi.schemas.empi import LinkRecordSchema
from ukrdc_fastapi.utils.mirth.messages import build_unlink_message


async def unlink_person_from_master_record(
    person: Person,
    master: MasterRecord,
    comment: Optional[str],
    user_id: str,
    jtrace: Session,
    mirth: MirthAPI,
    redis: Redis,
) -> LinkRecordSchema:
    """Unlink a particular Person record from a Master Record"""
    # Get records to assert user permission

    # Build and send the unlink message
    await safe_send_mirth_message_to_name(
        "Unlink",
        build_unlink_message(master.id, person.id, user_id, description=comment),
        mirth,
        redis,
    )

    await sleep(0.5)  # Wait for the message to be processed (complete guess)

    # Find the new Master Record
    stmt = select(LinkRecord).where(LinkRecord.person_id == person.id)
    first_link_related_to_person = jtrace.scalars(stmt).first()

    return LinkRecordSchema.from_orm(first_link_related_to_person)
