from fastapi.exceptions import HTTPException
from httpx import Response
from mirth_client.mirth import MirthAPI
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.query.masterrecords import get_masterrecord
from ukrdc_fastapi.query.persons import get_person
from ukrdc_fastapi.utils.links import PersonMasterLink, find_related_link_records
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

    channel = await get_channel_from_name("Merge Patient", mirth, redis)
    if not channel:
        raise HTTPException(
            500, detail="ID for Merge Patient channel not found"
        )  # pragma: no cover

    message: str = build_merge_message(
        superseding=superseding.id, superseded=superseded.id
    )

    response: Response = await channel.post_message(message)

    if response.status_code >= 400:
        raise HTTPException(500, detail=response.text)

    return MirthMessageResponseSchema(status="success", message=message)


async def merge_person_into_master_record(
    person_id: int,
    master_id: int,
    user: UKRDCUser,
    jtrace: Session,
    mirth: MirthAPI,
    redis: Redis,
):
    """Merge a particular Person record into a Master Record"""
    # Get records to assert user permission
    person = get_person(jtrace, person_id, user)
    master = get_masterrecord(jtrace, master_id, user)

    # Get a set of related link record (id, person_id, master_id) tuples
    related_person_master_links: set[PersonMasterLink] = find_related_link_records(
        jtrace, master.id, person_id=person.id
    )

    # Find all related master records within the UKRDC
    master_with_ukrdc = (
        jtrace.query(MasterRecord)
        .filter(
            MasterRecord.id.in_(
                [link.master_id for link in related_person_master_links]
            )
        )
        .filter(MasterRecord.nationalid_type == "UKRDC")
        .order_by(MasterRecord.id)
        .all()
    )

    # If we don't have 2 records, something has gone wrong
    if len(master_with_ukrdc) != 2:
        raise HTTPException(
            400,
            detail=f"Got {len(master_with_ukrdc)} master record(s) with different UKRDC IDs. Expected 2.",
        )

    return await merge_master_records(
        master_with_ukrdc[0].id, master_with_ukrdc[1].id, user, jtrace, mirth, redis
    )
