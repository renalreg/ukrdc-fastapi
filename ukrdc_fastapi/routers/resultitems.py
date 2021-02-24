from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.models.ukrdc import LabOrder, ResultItem
from ukrdc_fastapi.schemas.laborder import ResultItemSchema
from ukrdc_fastapi.utils import filter
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


@router.get("/", response_model=Page[ResultItemSchema])
def resultitems(ni: Optional[str] = None, ukrdc3: Session = Depends(get_ukrdc3)):
    resultitems = ukrdc3.query(ResultItem)
    # Optionally filter by NI
    if ni:
        resultitems = filter.resultitems_by_ni(ukrdc3, resultitems, ni)
    resultitems = resultitems.order_by(ResultItem.service_id_description)
    return paginate(resultitems)
