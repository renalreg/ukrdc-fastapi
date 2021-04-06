import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
from sqlalchemy.orm import Query, Session
from ukrdc_sqla.empi import MasterRecord, Person

from ukrdc_fastapi.auth import Auth0User, Scopes, Security, auth
from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema
from ukrdc_fastapi.utils import parse_date
from ukrdc_fastapi.utils.paginate import Page, paginate
from ukrdc_fastapi.utils.search.masterrecords import (
    masterrecord_ids_from_dob,
    masterrecord_ids_from_full_name,
    masterrecord_ids_from_mrn_no,
    masterrecord_ids_from_nhs_no,
    masterrecord_ids_from_pidxref_no,
    masterrecord_ids_from_ukrdc_no,
)
from ukrdc_fastapi.utils.search.persons import (
    person_ids_from_dob,
    person_ids_from_full_name,
    person_ids_from_mrn_no,
    person_ids_from_nhs_no,
    person_ids_from_pidxref_no,
    person_ids_from_ukrdc_no,
)

router = APIRouter()


def _pop_dates(search_items: list[str]) -> tuple[list[str], list[datetime.date]]:
    dates: list[datetime.date] = []
    strings: list[str] = []
    for item in search_items:
        parsed_date: Optional[datetime.datetime] = parse_date(item)
        if parsed_date:
            dates.append(parsed_date)
        else:
            strings.append(item)
    return (strings, dates)


def _is_int(val):
    try:
        int(val)
    except ValueError:
        return False
    return True


@router.get("/person", response_model=Page[PersonSchema])
def search_person(
    nhs_number: Optional[list[str]] = QueryParam(None),
    mrn_number: Optional[list[str]] = QueryParam(None),
    ukrdc_number: Optional[list[str]] = QueryParam(None),
    full_name: Optional[list[str]] = QueryParam(None),
    dob: Optional[list[str]] = QueryParam(None),
    pidx: Optional[list[str]] = QueryParam(None),
    search: Optional[list[str]] = QueryParam(None),
    jtrace: Session = Depends(get_jtrace),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_EMPI]),
):
    """Search the EMPI for a particular person record"""
    match_sets: list[set[str]] = []

    nhs_number_list: list[str] = nhs_number or []
    mrn_number_list: list[str] = mrn_number or []
    ukrdc_number_list: list[str] = ukrdc_number or []
    full_name_list: list[str] = full_name or []
    pidx_list: list[str] = pidx or []

    search_list: list[str]
    date_list: list[datetime.date]
    search_list, date_list = _pop_dates((search or []) + (dob or []))

    if nhs_number or search_list:
        match_sets.append(
            person_ids_from_nhs_no(jtrace, (*nhs_number_list, *search_list))
        )

    if mrn_number or search_list:
        match_sets.append(
            person_ids_from_mrn_no(jtrace, (*mrn_number_list, *search_list))
        )

    if ukrdc_number or search_list:
        match_sets.append(
            person_ids_from_ukrdc_no(jtrace, (*ukrdc_number_list, *search_list))
        )

    if full_name or search_list:
        match_sets.append(
            person_ids_from_full_name(jtrace, (*full_name_list, *search_list))
        )

    if date_list:
        match_sets.append(person_ids_from_dob(jtrace, date_list))

    if pidx or search_list:
        match_sets.append(
            person_ids_from_pidxref_no(jtrace, (*pidx_list, *search_list))
        )

    non_empty_sets: list[set[str]] = [
        match_set for match_set in match_sets if match_set
    ]

    matched_ids: set[str]
    if non_empty_sets:
        matched_ids = set.intersection(*non_empty_sets)
    else:
        matched_ids = set()

    matched_persons: Query = jtrace.query(Person).filter(Person.id.in_(matched_ids))

    return paginate(matched_persons)


@router.get("/masterrecords", response_model=Page[MasterRecordSchema])
def search_masterrecords(
    nhs_number: Optional[list[str]] = QueryParam(None),
    mrn_number: Optional[list[str]] = QueryParam(None),
    ukrdc_number: Optional[list[str]] = QueryParam(None),
    full_name: Optional[list[str]] = QueryParam(None),
    dob: Optional[list[str]] = QueryParam(None),
    pidx: Optional[list[str]] = QueryParam(None),
    search: Optional[list[str]] = QueryParam(None),
    number_type: Optional[list[str]] = QueryParam(None),
    jtrace: Session = Depends(get_jtrace),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_EMPI]),
):
    """Search the EMPI for a particular master record"""
    match_sets: list[set[str]] = []

    nhs_number_list: list[str] = nhs_number or []
    mrn_number_list: list[str] = mrn_number or []
    ukrdc_number_list: list[str] = ukrdc_number or []
    full_name_list: list[str] = full_name or []
    pidx_list: list[str] = pidx or []

    number_type_list: list[str] = number_type or []

    search_list: list[str] = search or []
    date_list: list[datetime.date]
    search_list, date_list = _pop_dates((search or []) + (dob or []))

    # Check if the search query matches a MasterRecord ID
    match_sets.append(
        {
            record.id
            for record in (
                jtrace.query(MasterRecord).get(id_)
                for id_ in search_list
                if _is_int(id_)
            )
            if record
        }
    )

    if nhs_number or search_list:
        match_sets.append(
            masterrecord_ids_from_nhs_no(jtrace, (*nhs_number_list, *search_list))
        )

    if mrn_number or search_list:
        match_sets.append(
            masterrecord_ids_from_mrn_no(jtrace, (*mrn_number_list, *search_list))
        )

    if ukrdc_number or search_list:
        match_sets.append(
            masterrecord_ids_from_ukrdc_no(jtrace, (*ukrdc_number_list, *search_list))
        )

    if full_name or search_list:
        match_sets.append(
            masterrecord_ids_from_full_name(jtrace, (*full_name_list, *search_list))
        )

    if date_list:
        match_sets.append(masterrecord_ids_from_dob(jtrace, date_list))

    if pidx or search_list:
        match_sets.append(
            masterrecord_ids_from_pidxref_no(jtrace, (*pidx_list, *search_list))
        )

    non_empty_sets: list[set[str]] = [
        match_set for match_set in match_sets if match_set
    ]

    matched_ids: set[str]
    if non_empty_sets:
        matched_ids = set.intersection(*non_empty_sets)
    else:
        matched_ids = set()

    matched_records: Query = jtrace.query(MasterRecord).filter(
        MasterRecord.id.in_(matched_ids)
    )

    if number_type_list:
        matched_records = matched_records.filter(
            MasterRecord.nationalid_type.in_(number_type_list)
        )

    return paginate(matched_records)
