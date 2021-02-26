from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.models.empi import LinkRecord
from ukrdc_fastapi.schemas.empi import LinkRecordSchema
from ukrdc_fastapi.utils import filter
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


@router.get("/", response_model=Page[LinkRecordSchema])
def linkrecords(ni: Optional[str] = None, jtrace: Session = Depends(get_jtrace)):
    linkrecords = jtrace.query(LinkRecord)
    if ni:
        linkrecords = filter.linkrecords_by_ni(jtrace, linkrecords, ni)
    return paginate(linkrecords)
