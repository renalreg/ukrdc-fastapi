import datetime
from typing import Optional

from mirth_client.mirth import MirthAPI
from redis import Redis
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.query.mirth.base import safe_send_mirth_message_to_name
from ukrdc_fastapi.schemas.patient import AddressSchema, GenderType, NameSchema
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema
from ukrdc_fastapi.utils.mirth.messages.rda import build_demographic_update_message


async def update_patient_demographics(
    record: PatientRecord,
    name: Optional[NameSchema],
    birth_time: Optional[datetime.date],
    gender: Optional[GenderType],
    address: Optional[AddressSchema],
    mirth: MirthAPI,
    redis: Redis,
) -> MirthMessageResponseSchema:
    """
    Update the demographic data of a given patient record

    Args:
        record (PatientRecord): Base patient record to update
        name (Optional[NameSchema]): New name to set
        dob (Optional[datetime.date]): New date of birth to set
        gender (Optional[GenderType]): New gender code to set
        address (Optional[AddressSchema]): New address to set
        mirth (MirthAPI): Mirth API session
        redis (Redis): Redis session

    Returns:
        MirthMessageResponseSchema: Mirth message response
    """
    return await safe_send_mirth_message_to_name(
        "Generic RDA Inbound",
        build_demographic_update_message(record, name, birth_time, gender, address),
        mirth,
        redis,
    )
