from typing import Optional

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.masterrecords import get_masterrecords
from ukrdc_fastapi.schemas.empi import MasterRecordSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

from . import record_id

router = APIRouter(tags=["Master Records"])
router.include_router(record_id.router)


@router.get(
    "/",
    response_model=Page[MasterRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_RECORDS))],
)
def master_records(
    user: UKRDCUser = Security(auth.get_user()),
    facility: Optional[str] = None,
    jtrace: Session = Depends(get_jtrace),
):
    """Retreive a list of master records from the EMPI"""
    return paginate(get_masterrecords(jtrace, user, facility=facility))
