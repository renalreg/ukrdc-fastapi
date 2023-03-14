from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
from fastapi import Security
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import LinkRecord, MasterRecord

from ukrdc_fastapi.dependencies import get_jtrace, get_ukrdc3
from ukrdc_fastapi.dependencies.audit import (
    Auditer,
    AuditOperation,
    Resource,
    get_auditer,
)
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.permissions.masterrecords import apply_masterrecord_list_permissions
from ukrdc_fastapi.schemas.empi import MasterRecordSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.search.masterrecords import search_masterrecord_ids

router = APIRouter(tags=["Search"])


@router.get(
    "",
    response_model=Page[MasterRecordSchema],
    dependencies=[Security(auth.permission([Permissions.READ_RECORDS]))],
)
def search_masterrecords(
    pid: list[str] = QueryParam([], description="Patient PID"),
    mrn_number: list[str] = QueryParam(
        [], description="Patient MRN number, e.g. NHS, CHI or HSC number"
    ),
    ukrdc_number: list[str] = QueryParam([], description="UKRDC record number"),
    full_name: list[str] = QueryParam([], description="Patient full name"),
    dob: list[str] = QueryParam([], description="Patient date of birth"),
    facility: list[str] = QueryParam([], description="Facility code"),
    search: list[str] = QueryParam([], description="Free-text search query"),
    number_type: list[str] = QueryParam(
        [], description="Number types to return, e.g. UKRDC, NHS, CHI, HSC"
    ),
    user: UKRDCUser = Security(auth.get_user()),
    jtrace: Session = Depends(get_jtrace),
    ukrdc3: Session = Depends(get_ukrdc3),
    audit: Auditer = Depends(get_auditer),
):
    """Search the EMPI for a particular master record"""
    matched_ukrdc_ids = search_masterrecord_ids(
        mrn_number, ukrdc_number, full_name, pid, dob, facility, search, ukrdc3
    )

    # Matched UKRDC IDs will only give us UKRDC-type Master Records,
    # but we also want the associated NHS/CHI/HSC master records.
    # So, we do a single pass of the link records to expand our selection.
    person_ids = (
        jtrace.query(LinkRecord.person_id)
        .join(MasterRecord)
        .filter(MasterRecord.nationalid.in_(matched_ukrdc_ids))
    )

    master_ids = (
        jtrace.query(MasterRecord.id)
        .join(LinkRecord)
        .filter(LinkRecord.person_id.in_(person_ids))
    )

    matched_records = jtrace.query(MasterRecord).filter(MasterRecord.id.in_(master_ids))

    # If a number type filter is explicitly given
    if number_type:
        # Filter by number types
        matched_records = matched_records.filter(
            MasterRecord.nationalid_type.in_(number_type)
        )

    # Apply permissions
    matched_records = apply_masterrecord_list_permissions(matched_records, user)

    # Paginate results
    page: Page[MasterRecord] = paginate(matched_records)  # type: ignore

    for record in page.items:
        audit.add_event(Resource.MASTER_RECORD, record.id, AuditOperation.READ)  # type: ignore  # MyPy doesn't like the generic page.item type T being used here

    return page
