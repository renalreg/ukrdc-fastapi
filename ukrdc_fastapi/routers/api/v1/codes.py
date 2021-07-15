from typing import Optional

from fastapi import APIRouter, Depends, Query, Security
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.query.codes import get_code_maps, get_codes, get_coding_standards
from ukrdc_fastapi.schemas.code import CodeMapSchema, CodeSchema
from ukrdc_fastapi.utils.paginate import Page, paginate

router = APIRouter(tags=["Codes"])


@router.get(
    "/list/",
    response_model=Page[CodeSchema],
    dependencies=[Security(auth.permission(Permissions.READ_CODES))],
)
def code_list(
    ukrdc3: Session = Depends(get_ukrdc3),
    coding_standard: Optional[list[str]] = Query(None),
):
    """Retreive a list of internal codes"""
    return paginate(get_codes(ukrdc3, coding_standard))


@router.get(
    "/maps/",
    response_model=Page[CodeMapSchema],
    dependencies=[Security(auth.permission(Permissions.READ_CODES))],
)
def code_maps(
    ukrdc3: Session = Depends(get_ukrdc3),
    source_coding_standard: Optional[list[str]] = Query(None),
    destination_coding_standard: Optional[list[str]] = Query(None),
    source_code: Optional[str] = None,
    destination_code: Optional[str] = None,
):
    """Retreive a list of internal code maps"""
    return paginate(
        get_code_maps(
            ukrdc3,
            source_coding_standard,
            destination_coding_standard,
            source_code,
            destination_code,
        )
    )


@router.get(
    "/standards/",
    response_model=list[str],
    dependencies=[Security(auth.permission(Permissions.READ_CODES))],
)
def coding_standards_list(ukrdc3: Session = Depends(get_ukrdc3)):
    """Retreive a list of internal codeing standards"""
    return get_coding_standards(ukrdc3)
