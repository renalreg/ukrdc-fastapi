from fastapi import APIRouter, Depends, Security
from mirth_client.mirth import MirthAPI
from pydantic.fields import Field
from pydantic.main import BaseModel
from redis import Redis
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace, get_mirth, get_redis
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.mirth.merge import merge_master_records
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema

from . import masterrecords, persons, search, workitems

router = APIRouter(tags=["Patient Index"])

router.include_router(workitems.router, prefix="/workitems")
router.include_router(persons.router, prefix="/persons")
router.include_router(masterrecords.router, prefix="/masterrecords")
router.include_router(search.router, prefix="/search")


class MergeRequestSchema(BaseModel):
    superceding: int = Field(..., title="Superceding master-record ID")
    superceeded: int = Field(..., title="Superceeded master-record ID")


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
async def master_records_merge(
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
