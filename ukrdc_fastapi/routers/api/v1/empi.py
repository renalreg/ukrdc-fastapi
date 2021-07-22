from fastapi import APIRouter, Depends, Security
from mirth_client.mirth import MirthAPI
from pydantic.fields import Field
from pydantic.main import BaseModel
from redis import Redis
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace, get_mirth, get_redis
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.mirth.merge import merge_master_records
from ukrdc_fastapi.query.mirth.unlink import unlink_person_from_master_record
from ukrdc_fastapi.schemas.base import JSONModel
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema

router = APIRouter(tags=["Patient Index Operations"])


class MergeRequestSchema(JSONModel):
    superceding: int = Field(..., title="Superceding master-record ID")
    superceeded: int = Field(..., title="Superceeded master-record ID")


class UnlinkRequestSchema(JSONModel):
    person_id: int = Field(..., title="ID of the person-record to be unlinked")
    master_id: int = Field(..., title="ID of the master-record to unlink from")


@router.post(
    "/merge/",
    response_model=MirthMessageResponseSchema,
    dependencies=[
        Security(
            auth.permission(
                [auth.permissions.READ_RECORDS, auth.permissions.WRITE_RECORDS]
            )
        )
    ],
)
async def empi_merge(
    args: MergeRequestSchema,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Merge a pair of MasterRecords"""

    return await merge_master_records(
        args.superceding, args.superceeded, user, jtrace, mirth, redis
    )


@router.post(
    "/unlink/",
    response_model=MirthMessageResponseSchema,
    dependencies=[
        Security(
            auth.permission(
                [auth.permissions.READ_RECORDS, auth.permissions.WRITE_RECORDS]
            )
        )
    ],
)
async def empi_unlink(
    args: UnlinkRequestSchema,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
    mirth: MirthAPI = Depends(get_mirth),
    redis: Redis = Depends(get_redis),
):
    """Unlink the master record and person record in a particular work item"""
    return await unlink_person_from_master_record(
        args.person_id, args.master_id, user, jtrace, mirth, redis
    )
