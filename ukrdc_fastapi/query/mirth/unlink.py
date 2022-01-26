from asyncio import sleep
from typing import Optional

from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import LinkRecord

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.query.masterrecords import get_masterrecord
from ukrdc_fastapi.query.mirth.base import safe_send_mirth_message_to_name
from ukrdc_fastapi.query.persons import get_person
from ukrdc_fastapi.schemas.empi import LinkRecordSchema
from ukrdc_fastapi.utils.mirth.messages import build_unlink_message


async def unlink_person_from_master_record(
    person_id: int,
    master_id: int,
    comment: Optional[str],
    user: UKRDCUser,
    jtrace: Session,
    mirth: MirthAPI,
    redis: Redis,
) -> LinkRecordSchema:
    """Unlink a particular Person record from a Master Record"""
    # Get records to assert user permission
    person = get_person(jtrace, person_id, user)
    master = get_masterrecord(jtrace, master_id, user)

    # Build and send the unlink message
    await safe_send_mirth_message_to_name(
        "Unlink",
        build_unlink_message(master.id, person.id, user.email, description=comment),
        mirth,
        redis,
    )

    await sleep(0.5)  # Wait for the message to be processed (complete guess)

    # Find the new Master Record
    first_link_related_to_person = (
        jtrace.query(LinkRecord).filter(LinkRecord.person_id == person.id).first()
    )

    return LinkRecordSchema.from_orm(first_link_related_to_person)
