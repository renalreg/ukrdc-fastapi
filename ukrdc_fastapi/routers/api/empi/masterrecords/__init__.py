from typing import Optional

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.access_models.empi import MasterRecordAM
from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.auth import UKRDCUser, auth
from ukrdc_fastapi.schemas.empi import MasterRecordSchema
from ukrdc_fastapi.utils.filters.empi import filter_masterrecords_by_facility
from ukrdc_fastapi.utils.paginate import Page, paginate

from . import record_id

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
    records = jtrace.query(MasterRecord)

    if facility:
        records = filter_masterrecords_by_facility(records, facility)

    records = MasterRecordAM.apply_query_permissions(records, user)

    return paginate(records)
