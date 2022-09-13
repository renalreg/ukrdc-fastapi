import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, Security
from sqlalchemy.orm import Session

from ukrdc_fastapi.dependencies import get_ukrdc3
from ukrdc_fastapi.dependencies.auth import Permissions, auth
from ukrdc_fastapi.query.codes import (
    ExtendedCodeSchema,
    get_code,
    get_code_exclusions,
    get_code_maps,
    get_codes,
    get_coding_standards,
)
from ukrdc_fastapi.schemas.code import CodeExclusionSchema, CodeMapSchema, CodeSchema
from ukrdc_fastapi.utils.paginate import Page, paginate


class CSVResponse(Response):
    media_type = "text/csv"


router = APIRouter(tags=["Codes"])


@router.get(
    "/list",
    response_model=Page[CodeSchema],
    dependencies=[Security(auth.permission(Permissions.READ_CODES))],
)
def code_list(
    ukrdc3: Session = Depends(get_ukrdc3),
    coding_standard: Optional[list[str]] = Query(None),
    search: Optional[str] = Query(None),
):
    """Retreive a list of internal codes"""
    return paginate(get_codes(ukrdc3, coding_standard, search))


@router.get(
    "/list/{coding_standard}.{code}",
    response_model=ExtendedCodeSchema,
    dependencies=[Security(auth.permission(Permissions.READ_CODES))],
)
def code_details(
    coding_standard: str,
    code: str,
    ukrdc3: Session = Depends(get_ukrdc3),
):
    """Retreive a list of internal codes"""
    return get_code(ukrdc3, coding_standard, code)


@router.get(
    "/maps",
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
    "/exclusions",
    response_model=Page[CodeExclusionSchema],
    dependencies=[Security(auth.permission(Permissions.READ_CODES))],
)
def code_exclusions(
    ukrdc3: Session = Depends(get_ukrdc3),
    coding_standard: Optional[list[str]] = Query(None),
    code: Optional[list[str]] = Query(None),
    system: Optional[list[str]] = Query(None),
):
    """Retreive a list of internal code maps"""
    return paginate(get_code_exclusions(ukrdc3, coding_standard, code, system))


@router.get(
    "/standards",
    response_model=list[str],
    dependencies=[Security(auth.permission(Permissions.READ_CODES))],
)
def coding_standards_list(ukrdc3: Session = Depends(get_ukrdc3)):
    """Retreive a list of internal codeing standards"""
    return get_coding_standards(ukrdc3)


@router.get(
    "/export/list",
    response_class=CSVResponse,
    dependencies=[Security(auth.permission(Permissions.READ_CODES))],
)
def code_list_export(
    ukrdc3: Session = Depends(get_ukrdc3),
    coding_standard: Optional[list[str]] = Query(None),
    search: Optional[str] = Query(None),
):
    """Export a CSV of a list of internal codes"""
    selected_codes = get_codes(ukrdc3, coding_standard, search)

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    for code in selected_codes:
        writer.writerow([code.coding_standard, code.code, code.description])

    return output.getvalue()


@router.get(
    "/export/maps",
    response_class=CSVResponse,
    dependencies=[Security(auth.permission(Permissions.READ_CODES))],
)
def code_maps_export(
    ukrdc3: Session = Depends(get_ukrdc3),
    source_coding_standard: Optional[list[str]] = Query(None),
    destination_coding_standard: Optional[list[str]] = Query(None),
    source_code: Optional[str] = None,
    destination_code: Optional[str] = None,
):
    """Export a CSV of a list of internal codes"""
    selected_maps = get_code_maps(
        ukrdc3,
        source_coding_standard,
        destination_coding_standard,
        source_code,
        destination_code,
    )

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    for codemap in selected_maps:
        writer.writerow(
            [
                codemap.source_coding_standard,
                codemap.source_code,
                codemap.destination_coding_standard,
                codemap.destination_code,
            ]
        )

    return output.getvalue()


@router.get(
    "/export/exclusions",
    response_class=CSVResponse,
    dependencies=[Security(auth.permission(Permissions.READ_CODES))],
)
def code_exclusions_export(
    ukrdc3: Session = Depends(get_ukrdc3),
    coding_standard: Optional[list[str]] = Query(None),
    code: Optional[list[str]] = Query(None),
    system: Optional[list[str]] = Query(None),
):
    """Export a CSV of a list of internal codes"""
    selected_exclusions = get_code_exclusions(ukrdc3, coding_standard, code, system)

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    for exclusion in selected_exclusions:
        writer.writerow(
            [
                exclusion.coding_standard,
                exclusion.code,
                exclusion.system,
            ]
        )

    return output.getvalue()
