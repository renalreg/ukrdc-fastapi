from mirth_client.mirth import MirthAPI
from redis import Redis

from ukrdc_fastapi.query.mirth.base import safe_send_mirth_message_to_name
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema

from ukrdc_fastapi.utils.mirth.messages import build_create_partner_membership


async def create_partner_membership_for_ukrdcid(
    ukrdcid: str,
    mirth: MirthAPI,
    redis: Redis,
    partner: str,
) -> MirthMessageResponseSchema:
    """Export a specific patient's data to PV"""

    return await safe_send_mirth_message_to_name(
        "Partner - New Patients",
        build_create_partner_membership(ukrdcid, partner),
        mirth,
        redis,
    )
