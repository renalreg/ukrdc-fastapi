from typing import Optional

from fastapi import APIRouter, Depends, Security
from mirth_client.mirth import MirthAPI
from pydantic.fields import Field
from pydantic.main import BaseModel
from redis import Redis
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace, get_mirth, get_redis
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.query.masterrecords import get_masterrecords
from ukrdc_fastapi.query.mirth.merge import merge_master_records
from ukrdc_fastapi.schemas.empi import MasterRecordSchema
from ukrdc_fastapi.utils.mirth import MirthMessageResponseSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

from . import record_id


class MergeRequestSchema(BaseModel):
    superceding: int = Field(..., title="Superceding master-record ID")
    superceeded: int = Field(..., title="Superceeded master-record ID")


router = APIRouter(tags=["Patient Index/Master Records"])
router.include_router(record_id.router)


@router.get(
    "/",
    response_model=Page[MasterRecordSchema],
    dependencies=[Security(auth.permission(auth.permissions.READ_RECORDS))],
)
def master_records(
    user: UKRDCUser = Security(auth.get_user),
    facility: Optional[str] = None,
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of master records from the EMPI"""
    return paginate(get_masterrecords(jtrace, user, facility=facility))


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
