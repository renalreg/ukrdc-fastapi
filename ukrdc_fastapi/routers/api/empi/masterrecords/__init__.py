from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.schemas.empi import MasterRecordSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

from . import record_id

router = APIRouter(tags=["Patient Index/Master Records"])
router.include_router(record_id.router)


@router.get(
    "/",
    response_model=Page[MasterRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_EMPI))],
)
def master_records(
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of master records from the EMPI"""
    return paginate(jtrace.query(MasterRecord))
