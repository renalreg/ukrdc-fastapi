from typing import Optional

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import LinkRecord

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.schemas.empi import LinkRecordSchema
from ukrdc_fastapi.utils import filters
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


@router.get(
    "/",
    response_model=Page[LinkRecordSchema],
    dependencies=[Security(auth.permission(Permissions.READ_EMPI))],
)
def linkrecords(ni: Optional[str] = None, jtrace: Session = Depends(get_jtrace)):
    """Retreive a list of link records from the EMPI"""
    records = jtrace.query(LinkRecord)
    if ni:
        records = filters.linkrecords_by_ni(jtrace, records, ni)
    return paginate(records)
