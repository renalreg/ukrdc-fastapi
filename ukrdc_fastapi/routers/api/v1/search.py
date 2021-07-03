from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
from fastapi import Security
from sqlalchemy.orm import Session
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.auth import Permissions, UKRDCUser, auth
from ukrdc_fastapi.query.masterrecords import get_masterrecords
from ukrdc_fastapi.schemas.empi import MasterRecordSchema
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.search.masterrecords import search_masterrecord_ids

router = APIRouter()


@router.get(
    "/",
    response_model=Page[MasterRecordSchema],
    dependencies=[
        Security(auth.permission([Permissions.READ_EMPI, Permissions.READ_RECORDS]))
    ],
)
def search_masterrecords(
    nhs_number: list[str] = QueryParam([]),
    mrn_number: list[str] = QueryParam([]),
    ukrdc_number: list[str] = QueryParam([]),
    full_name: list[str] = QueryParam([]),
    pidx: list[str] = QueryParam([]),
    dob: list[str] = QueryParam([]),
    search: list[str] = QueryParam([]),
    number_type: list[str] = QueryParam([]),
    include_ukrdc: bool = False,
    user: UKRDCUser = Security(auth.get_user),
    jtrace: Session = Depends(get_jtrace),
):
    """Search the EMPI for a particular master record"""
    matched_ids = search_masterrecord_ids(
        nhs_number, mrn_number, ukrdc_number, full_name, pidx, dob, search, jtrace
    )

    matched_records = get_masterrecords(jtrace, user).filter(
        MasterRecord.id.in_(matched_ids)
    )

    if number_type:
        matched_records = matched_records.filter(
            MasterRecord.nationalid_type.in_(number_type)
        )
    if not include_ukrdc:
        matched_records = matched_records.filter(
            MasterRecord.nationalid_type != "UKRDC"
        )

    return paginate(matched_records)
