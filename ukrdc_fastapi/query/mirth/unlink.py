from fastapi.exceptions import HTTPException
from httpx import Response
from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm.session import Session

from ukrdc_fastapi.dependencies.auth import UKRDCUser
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
        raise HTTPException(
            500, detail="ID for Unlink channel not found"
        )  # pragma: no cover

    message: str = build_unlink_message(master.id, person.id, user.email)

    response: Response = await channel.post_message(message)

    if response.status_code >= 400:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


async def unlink_patient_from_master_record(
    pid: str,
    master_id: int,
    user: UKRDCUser,
    jtrace: Session,
    mirth: MirthAPI,
    redis: Redis,
):
    """Unlink a particular PatientRecord from a Master Record"""
    # Get records to assert user permission
    person = get_person_from_pid(jtrace, pid, user)
    return await unlink_person_from_master_record(
        person.id, master_id, user, jtrace, mirth, redis
    )
