from typing import Optional

from fastapi import APIRouter, Depends, Security
from mirth_client.mirth import MirthAPI
from pydantic.fields import Field
from redis import Redis
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord, Person

from ukrdc_fastapi.dependencies import get_jtrace, get_mirth, get_redis
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.exceptions import ResourceNotFoundError
from ukrdc_fastapi.permissions.masterrecords import assert_masterrecord_permission
from ukrdc_fastapi.permissions.persons import assert_person_permission
from ukrdc_fastapi.query.mirth.merge import merge_master_records
from ukrdc_fastapi.query.mirth.unlink import unlink_person_from_master_record
from ukrdc_fastapi.schemas.base import JSONModel
from ukrdc_fastapi.schemas.empi import LinkRecordSchema
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema

router = APIRouter(tags=["Patient Index Operations"])


class MergeRequest(JSONModel):
    superseding: int = Field(..., title="Superseding master-record ID")
    superseded: int = Field(..., title="Superseded master-record ID")


class UnlinkRequest(JSONModel):
    person_id: int = Field(..., title="ID of the person-record to be unlinked")
    master_id: int = Field(..., title="ID of the master-record to unlink from")
    comment: Optional[str] = Field(None, max_length=100)


class UnlinkPatientRequest(JSONModel):
    pid: str = Field(..., title="PID of the patient-record to be unlinked")
    master_id: int = Field(..., title="ID of the master-record to unlink from")


@router.post(
    "/merge",
    response_model=MirthMessageResponseSchema,
    dependencies=[
        Security(auth.permission([Permissions.READ_RECORDS, Permissions.WRITE_RECORDS]))
    ],
)
async def empi_merge(
    args: MergeRequest,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Merge a pair of MasterRecords"""
    # Get the records
    superseding: Optional[MasterRecord] = jtrace.get(MasterRecord, args.superseding)
    superseded: Optional[MasterRecord] = jtrace.get(MasterRecord, args.superseded)

    if not (superseding and superseded):
        raise ResourceNotFoundError("Master Record not found")

    # Assert permissions
    assert_masterrecord_permission(superseding, user)
    assert_masterrecord_permission(superseded, user)

    return await merge_master_records(superseding, superseded, mirth, redis)


@router.post(
    "/unlink",
    response_model=LinkRecordSchema,
    dependencies=[
        Security(auth.permission([Permissions.WRITE_EMPI, Permissions.WRITE_RECORDS]))
    ],
)
async def empi_unlink(
    args: UnlinkRequest,
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Unlink a Person from a specified MasterRecord"""
    # Get the records
    person = jtrace.get(Person, args.person_id)
    master = jtrace.get(MasterRecord, args.master_id)

    if not person:
        raise ResourceNotFoundError("Person not found")
    if not master:
        raise ResourceNotFoundError("Master Record not found")

    # Assert permissions
    assert_masterrecord_permission(master, user)
    assert_person_permission(person, user)

    return await unlink_person_from_master_record(
        person,
        master,
        args.comment,
        user.email,
        jtrace,
        mirth,
        redis,
    )
