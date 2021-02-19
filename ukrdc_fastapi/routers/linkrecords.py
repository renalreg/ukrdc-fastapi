from typing import Optional

from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.models.empi import LinkRecord
from ukrdc_fastapi.schemas.empi import LinkRecordSchema
from ukrdc_fastapi.utils import filters

router = APIRouter()


@router.get("/", response_model=Page[LinkRecordSchema])
def linkrecords(ni: Optional[str] = None, jtrace: Session = Depends(get_jtrace)):
    linkrecords = jtrace.query(LinkRecord)
    if ni:
        linkrecords = filters.linkrecords_by_ni(jtrace, linkrecords, ni)
    return paginate(linkrecords)
