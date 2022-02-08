from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.query.masterrecords import get_masterrecord_from_ukrdcid
from ukrdc_fastapi.query.mirth.base import safe_send_mirth_message_to_name
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema
from ukrdc_fastapi.utils.mirth.messages.pkb import build_pkb_membership_message


async def create_pkb_membership(
    ukrdcid: str,
    user: UKRDCUser,
    jtrace: Session,
    mirth: MirthAPI,
    redis: Redis,
) -> MirthMessageResponseSchema:
    """Export a specific patient's data to PV"""
    master_record: MasterRecord = get_masterrecord_from_ukrdcid(jtrace, ukrdcid, user)
    return await safe_send_mirth_message_to_name(
        "PKB - New Patients",
        build_pkb_membership_message(master_record.nationalid),
        mirth,
        redis,
    )
