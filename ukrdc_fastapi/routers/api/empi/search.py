import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
from sqlalchemy.orm import Query, Session
from stdnum.gb import nhs
from stdnum.util import isdigits
from ukrdc_sqla.empi import MasterRecord

from ukrdc_fastapi.dependencies import get_jtrace
from ukrdc_fastapi.dependencies.auth import Auth0User, Scopes, Security, auth
from ukrdc_fastapi.schemas.empi import MasterRecordSchema
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

router = APIRouter()


class SearchSet:
    def __init__(self, terms: Optional[list[str]] = None) -> None:
        # Dates
        self.dates: list[datetime.date] = []  # DoB, DoD etc

        # String IDs
        self.nhs_numbers: list[str] = []  # NHS, CHI, or HSC
        self.mrn_numbers: list[str] = []  # Any unit-specific local ID

        # Integer IDs
        self.ukrdc_numbers: list[str] = []  # UKRDCID
        self.pids: list[str] = []  # Internal PIDs
        self.empi_ids: list[str] = []  # MasterRecord or Person IDs

        # Chars
        self.names: list[str] = []  # Patient names

        # Assign each term to a list
        if terms:
            self.add_terms(terms)

    def add_date(self, item: str):
        parsed_date: Optional[datetime.datetime] = parse_date(item)
        if parsed_date:
            self.dates.append(parsed_date.date())

    def add_nhs_number(self, item: str):
        if nhs.is_valid(item):
            self.nhs_numbers.append(nhs.compact(item))

    def add_mrn_number(self, item: str):
        if len(item) <= 17:
            self.mrn_numbers.append(item)

    def add_ukrdc_number(self, item: str):
        if isdigits(item) and (100000000 <= int(item) < 1000000000):
            self.ukrdc_numbers.append(item)

    def add_pid(self, item: str):
        if isdigits(item) and (1000000000 <= int(item) <= 10000000000):
            self.pids.append(item)

    def add_empi_id(self, item: str):
        # Extract EMPI IDs (by int4 type)
        if isdigits(item) and (-2147483648 <= int(item) <= 2147483647):
            self.empi_ids.append(item)

    def add_name(self, item: str):
        self.names.append(item)

    def add_terms(self, terms: list[str]):
        for item in terms:
            item = item.strip()

            # Extract dates
            self.add_date(item)

            # Extract NHS numbers
            self.add_nhs_number(item)

            # Extract MRN numbers
            self.add_mrn_number(item)

            # Extract UKRDC IDs (by range)
            self.add_ukrdc_number(item)

            # Extract PIDs (by range)
            self.add_pid(item)

            # Extract EMPI IDs (by int4 type)
            self.add_empi_id(item)

            # Absolutely anything can be a name
            self.add_name(item)


def _pop_dates(search_items: list[str]) -> tuple[list[str], list[datetime.date]]:
    dates: list[datetime.date] = []
    strings: list[str] = []
    for item in search_items:
        parsed_date: Optional[datetime.datetime] = parse_date(item)
        if parsed_date:
            dates.append(parsed_date.date())
        else:
            strings.append(item)
    return (strings, dates)


@router.get("/masterrecords/", response_model=Page[MasterRecordSchema])
def search_masterrecords(
    nhs_number: list[str] = QueryParam([]),
    mrn_number: list[str] = QueryParam([]),
    ukrdc_number: list[str] = QueryParam([]),
    full_name: list[str] = QueryParam([]),
    pidx: list[str] = QueryParam([]),
    dob: list[str] = QueryParam([]),
    search: list[str] = QueryParam([]),
    number_type: list[str] = QueryParam([]),
    jtrace: Session = Depends(get_jtrace),
    _: Auth0User = Security(auth.get_user, scopes=[Scopes.READ_EMPI]),
):
    """Search the EMPI for a particular master record"""
    match_sets: list[set[str]] = []

    searchset = SearchSet()

    for item in nhs_number:
        searchset.add_nhs_number(item)
    for item in mrn_number:
        searchset.add_mrn_number(item)
    for item in ukrdc_number:
        searchset.add_ukrdc_number(item)
    for item in full_name:
        searchset.add_name(item)
    for item in pidx:
        searchset.add_pid(item)
    for item in dob:
        searchset.add_date(item)

    searchset.add_terms(search)

    # Check if the search query contains MasterRecord IDs
    match_sets.append(
        {
            record.id
            for record in (
                jtrace.query(MasterRecord).get(id_) for id_ in searchset.empi_ids
            )
            if record
        }
    )

    if searchset.nhs_numbers:
        match_sets.append(masterrecord_ids_from_nhs_no(jtrace, searchset.nhs_numbers))

    if searchset.mrn_numbers:
        match_sets.append(masterrecord_ids_from_mrn_no(jtrace, searchset.mrn_numbers))

    if searchset.ukrdc_numbers:
        match_sets.append(
            masterrecord_ids_from_ukrdc_no(jtrace, searchset.ukrdc_numbers)
        )

    if searchset.names:
        match_sets.append(masterrecord_ids_from_full_name(jtrace, searchset.names))

    if searchset.dates:
        match_sets.append(masterrecord_ids_from_dob(jtrace, searchset.dates))

    if searchset.pids:
        match_sets.append(masterrecord_ids_from_pidxref_no(jtrace, searchset.pids))

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

    if number_type:
        matched_records = matched_records.filter(
            MasterRecord.nationalid_type.in_(number_type)
        )

    return paginate(matched_records)
