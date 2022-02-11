from mirth_client.mirth import MirthAPI
from redis import Redis
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.exceptions import RecordTypeError
from ukrdc_fastapi.query.mirth.base import safe_send_mirth_message_to_name
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema
from ukrdc_fastapi.utils.mirth.messages.pkb import build_pkb_membership_message


async def create_pkb_membership(
    master_record: MasterRecord,
    mirth: MirthAPI,
    redis: Redis,
) -> MirthMessageResponseSchema:
    """Export a specific patient's data to PV"""
    if master_record.nationalid_type != "UKRDC":
        raise RecordTypeError("Cannot create PKB membership from a non-UKRDC record")
    return await safe_send_mirth_message_to_name(
        "PKB - New Patients",
        build_pkb_membership_message(master_record.nationalid),
        mirth,
        redis,
    )
