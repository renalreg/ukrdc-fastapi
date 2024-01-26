import datetime
import re
from typing import Iterable, Optional, Union
from sqlalchemy import select

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import or_
from sqlalchemy.sql.functions import concat
from stdnum.gb import nhs
from stdnum.util import isdigits
from ukrdc_sqla.ukrdc import Facility, Name, Patient, PatientNumber, PatientRecord

from ukrdc_fastapi.utils import parse_date


class SearchSet:
    def __init__(self) -> None:
        # Dates
        self.dates: list[datetime.date] = []  # DoB, DoD etc

        # External IDs
        self.mrn_numbers: list[str] = []

        # Internal IDs
        self.ukrdc_numbers: list[str] = []  # UKRDCID
        self.pids: list[str] = []  # Internal PIDs

        # Chars
        self.names: list[str] = []  # Patient names

        # Facilities
        self.facilities: list[str] = []

    def add_date(self, item: str):
        """Add a datetime formatted string to the search query set.
        If the string cannot be parsed as a datetime, it will be ignored"""

        parsed_date: Optional[datetime.datetime] = parse_date(item)
        if parsed_date:
            self.dates.append(parsed_date.date())

    def add_mrn_number(self, item: str):
        """Add an MRN number formatted string to the search query set.
        If the string cannot be parsed as an MRN number, it will be ignored"""
        # Compact NHS numbers before searching
        if nhs.is_valid(item):
            self.mrn_numbers.append(nhs.compact(item))
        elif nhs.is_valid(item.zfill(10)):
            self.mrn_numbers.append(nhs.compact(item.zfill(10)))
        # Search anything else as-is
        elif len(item) <= 17:
            self.mrn_numbers.append(item)

    def add_ukrdc_number(self, item: str):
        """Add a UKRDC number formatted string to the search query set.
        If the string cannot be parsed as a UKRDC number, it will be ignored"""

        if isdigits(item) and (100000000 <= int(item) < 1000000000):
            self.ukrdc_numbers.append(item)

    def add_pid(self, item: str):
        """Add a patient ID formatted string to the search query set.
        If the string cannot be parsed as a PID, it will be ignored"""

        if isdigits(item) and (1000000000 <= int(item) <= 10000000000):
            self.pids.append(item)

    def add_name(self, item: str):
        """Add a name string to the search query set."""
        # Exclude strings containing only 0-9, -, _, ., or /
        if not re.match(r"^[0-9-/_.]*$", item):
            self.names.append(item)

    def add_facility(self, item: str):
        """Add a facility name to the search query set."""
        self.facilities.append(item)

    def add_terms(self, terms: list[str], ukrdc3: Session):
        """
        Add a list of strings to the search query set.
        Each string will be added to any search query group in which it is valid
        """
        stmt = select(Facility.code)
        facility_codes = ukrdc3.scalars(stmt).all()

        for item in terms:
            item = item.strip()

            # Extract dates
            self.add_date(item)

            # Extract MRN numbers
            self.add_mrn_number(item)

            # Extract Patient Records (by range)
            self.add_ukrdc_number(item)

            # Extract PIDs (by range)
            self.add_pid(item)

            # Match facility codes
            if item in facility_codes:
                self.add_facility(item)

            # Absolutely anything can be a name
            self.add_name(item)


def _term_is_exact(item: str) -> bool:
    """Determine is a search string is intended to be exact,
    by being wrapped in queryuotes.

    Args:
        item (str): Search term

    Returns:
        bool: Is the term an exact query
    """
    return item[0] == item[-1] == '"'


def _convert_query_to_pg_like(item: str) -> str:
    """Convert a search query into a postgres LIKE expression.
    E.g. a term wrapped in queryuotes will be matched exactly (but case
    insensitive), but without quotes will be fuzzy-searched

    Args:
        item (str): Search term

    Returns:
        str: Postgres ilike expression string
    """
    if _term_is_exact(item):
        return item.strip('"')
    return f"{item}%"


def records_from_mrn_no(ukrdc3: Session, mrn_nos: Iterable[str]) -> list[PatientRecord]:
    """
    Patient Records from MRN/NHS/HSC/CHI/RADAR number.
    """
    return ukrdc3.scalars(
        select(PatientRecord)
        .join(Patient)
        .join(PatientNumber)
        .where(PatientNumber.patientid.in_(mrn_nos))
    ).all()


def records_from_pid(ukrdc3: Session, pid_nos: Iterable[str]) -> list[PatientRecord]:
    """
    Finds Patient Records from PIDs
    """
    return ukrdc3.scalars(
        select(PatientRecord).where(PatientRecord.pid.in_(pid_nos))
    ).all()


def records_from_ukrdcid(
    ukrdc3: Session, ukrdcids: Iterable[str]
) -> list[PatientRecord]:
    """
    Finds Patient Records from UKRDC IDs
    """
    return ukrdc3.scalars(
        select(PatientRecord).where(PatientRecord.ukrdcid.in_(ukrdcids))
    ).all()


def records_from_facility(
    ukrdc3: Session, facilities: Iterable[str]
) -> list[PatientRecord]:
    """
    Finds Patient Records from facilities
    """
    ignore_extracts = {"PVMIG", "HSMIG"}
    return ukrdc3.scalars(
        select(PatientRecord)
        .where(PatientRecord.sendingfacility.in_(facilities))
        .where(PatientRecord.sendingextract.notin_(ignore_extracts))
    ).all()


def records_from_full_name(
    ukrdc3: Session, names: Iterable[str]
) -> list[PatientRecord]:
    """Finds Ids from full name"""
    conditions = []

    for name in names:
        query_term: str = _convert_query_to_pg_like(name).upper()

        conditions.extend(
            [
                concat(Name.given, " ", Name.family).like(query_term),
                concat(Name.family, " ", Name.given).like(query_term),
                Name.given.like(query_term),
                Name.family.like(query_term),
            ]
        )

    return ukrdc3.scalars(
        select(PatientRecord).join(Patient).join(Name).where(or_(*conditions))
    ).all()


def records_from_dob(
    ukrdc3: Session, dobs: Iterable[Union[str, datetime.date]]
) -> list[PatientRecord]:
    """Finds Ids from date of birth"""
    conditions = [Patient.birth_time == dob for dob in dobs]
    return ukrdc3.scalars(
        select(PatientRecord).join(Patient).where(or_(*conditions))
    ).all()


def search_ukrdcids(  # pylint: disable=too-many-branches
    mrn_number: list[str],
    ukrdc_number: list[str],
    full_name: list[str],
    pids: list[str],
    dob: list[str],
    facility: list[str],
    search: list[str],
    ukrdc3: Session,
) -> set[str]:
    """Search the UKRDC for a set of search items, and return a set of matching UKRDC IDs"""
    match_sets: list[set[str]] = []

    searchset = SearchSet()

    # Add all explicit search terms to the search set
    for item in mrn_number:
        searchset.add_mrn_number(item)
    for item in ukrdc_number:
        searchset.add_ukrdc_number(item)
    for item in full_name:
        searchset.add_name(item)
    for item in pids:
        searchset.add_pid(item)
    for item in dob:
        searchset.add_date(item)
    for item in facility:
        searchset.add_facility(item)

    # Add all implicit search terms to the search set
    searchset.add_terms(search, ukrdc3)

    if searchset.ukrdc_numbers:
        query = records_from_ukrdcid(ukrdc3, searchset.ukrdc_numbers)
        match_sets.append({record.ukrdcid for record in query if record.ukrdcid})

    if searchset.mrn_numbers:
        query = records_from_mrn_no(ukrdc3, searchset.mrn_numbers)
        match_sets.append({record.ukrdcid for record in query if record.ukrdcid})

    if searchset.names:
        query = records_from_full_name(ukrdc3, searchset.names)
        match_sets.append({record.ukrdcid for record in query if record.ukrdcid})

    if searchset.dates:
        query = records_from_dob(ukrdc3, searchset.dates)
        match_sets.append({record.ukrdcid for record in query if record.ukrdcid})

    if searchset.pids:
        query = records_from_pid(ukrdc3, searchset.pids)
        match_sets.append({record.ukrdcid for record in query if record.ukrdcid})

    if searchset.facilities:
        query = records_from_facility(ukrdc3, searchset.facilities)
        match_sets.append({record.ukrdcid for record in query if record.ukrdcid})

    non_empty_sets: list[set[str]] = [
        match_set for match_set in match_sets if match_set
    ]

    matched_ids: set[str]
    if non_empty_sets:
        matched_ids = set.intersection(*non_empty_sets)
    else:
        matched_ids = set()

    return matched_ids
