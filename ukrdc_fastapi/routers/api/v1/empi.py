from typing import Optional

from fastapi import APIRouter, Depends, Security
from mirth_client.mirth import MirthAPI
from pydantic.fields import Field
from redis import Redis
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace, get_mirth, get_redis
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
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

    return await merge_master_records(
        args.superseding, args.superseded, user, jtrace, mirth, redis
    )


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
    return await unlink_person_from_master_record(
        args.person_id,
        args.master_id,
        args.comment,
        user,
        jtrace,
        mirth,
        redis,
    )
