from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import LinkRecord

from ukrdc_fastapi.auth import Auth0User, Scopes, Security, auth
from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.schemas.empi import LinkRecordSchema
from ukrdc_fastapi.utils import filters
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter()


@router.get("/", response_model=Page[LinkRecordSchema])
def linkrecords(
    ni: Optional[str] = None,
    jtrace: Session = Depends(get_jtrace),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_EMPI]),
):
    """Retreive a list of link records from the EMPI"""
    records = jtrace.query(LinkRecord)
    if ni:
        records = filters.linkrecords_by_ni(jtrace, records, ni)
    return paginate(records)
