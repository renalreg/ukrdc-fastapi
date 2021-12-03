from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
from fastapi import Security
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import LinkRecord, MasterRecord

from ukrdc_fastapi.dependencies import get_jtrace, get_ukrdc3
from ukrdc_fastapi.dependencies.audit import Auditer, AuditOperation, get_auditer
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.masterrecords import get_masterrecords
from ukrdc_fastapi.schemas.empi import MasterRecordSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.search.masterrecords import search_masterrecord_ids

router = APIRouter(tags=["Search"])


@router.get(
    "/",
    response_model=Page[MasterRecordSchema],
    dependencies=[Security(auth.permission([Permissions.READ_RECORDS]))],
)
def search_masterrecords(
    pid: list[str] = QueryParam([]),
    mrn_number: list[str] = QueryParam([]),
    ukrdc_number: list[str] = QueryParam([]),
    full_name: list[str] = QueryParam([]),
    dob: list[str] = QueryParam([]),
    facility: list[str] = QueryParam([]),
    search: list[str] = QueryParam([]),
    number_type: list[str] = QueryParam([]),
    include_ukrdc: bool = False,
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

    matched_records = get_masterrecords(jtrace, user).filter(
        MasterRecord.id.in_(master_ids)
    )

    if number_type:
        matched_records = matched_records.filter(
            MasterRecord.nationalid_type.in_(number_type)
        )

    if not include_ukrdc:
        matched_records = matched_records.filter(
            MasterRecord.nationalid_type != "UKRDC"
        )

    page: Page = paginate(matched_records)  # type: ignore

    for record in page.items:
        audit.add_master_record(record.id, AuditOperation.READ)

    return page
