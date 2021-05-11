import datetime
from typing import Iterable, Optional, Union

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import or_
from sqlalchemy.sql.functions import concat
from stdnum.gb import nhs
from stdnum.util import isdigits
from ukrdc_sqla.empi import MasterRecord, Person, PidXRef

from ukrdc_fastapi.utils import parse_date
from ukrdc_fastapi.utils.filters import find_ids_related_to_person


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
        """Add a datetime formatted string to the search query set.
        If the string cannot be parsed as a datetime, it will be ignored"""

        parsed_date: Optional[datetime.datetime] = parse_date(item)
        if parsed_date:
            self.dates.append(parsed_date.date())

    def add_nhs_number(self, item: str):
        """Add an NHS number string to the search query set.
        If the string cannot be parsed as an NHS number, it will be ignored"""

        if nhs.is_valid(item):
            self.nhs_numbers.append(nhs.compact(item))

    def add_mrn_number(self, item: str):
        """Add an MRN number formatted string to the search query set.
        If the string cannot be parsed as an MRN number, it will be ignored"""

        if len(item) <= 17:
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

    def add_empi_id(self, item: str):
        """Add an EMPI ID formatted string to the search query set.
        If the string cannot be parsed as an EMPI ID, it will be ignored"""

        # Extract EMPI IDs (by int4 type)
        if isdigits(item) and (-2147483648 <= int(item) <= 2147483647):
            self.empi_ids.append(item)

    def add_name(self, item: str):
        """Add a name string to the search query set."""

        self.names.append(item)

    def add_terms(self, terms: list[str]):
        """
        Add a list of strings to the search query set.
        Each string will be added to any search query group in which it is valid
        """

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


def masterrecord_ids_from_nhs_no(session: Session, nhs_nos: Iterable[str]):
    """Finds IDs from NHS number."""
    conditions = [MasterRecord.nationalid.ilike(nhs_no.strip()) for nhs_no in nhs_nos]
    matched_ids = {
        record.id
        for record in session.query(MasterRecord)
        .filter(
            or_(*conditions),
            MasterRecord.nationalid_type.in_(["NHS", "HSC", "CHI"]),
        )
        .all()
    }

    return matched_ids


def masterrecord_ids_from_mrn_no(session: Session, mrn_nos: Iterable[str]):
    """
    Finds IDs from MRN number.

    Naievely we would just match Person.localid, however the EMPI has
    an extra step to work around MRNs (local IDs) changing.
    We actually want to look up the MRN in our PidXRef table, then
    work backwards to find the Person/MasterRecord associated with it.

    The actual MRN will be in PidXRef.localid. The associated PidXRef.pid
    will match to a corresponding Person.localid, and from there we can
    obtain the associated MasterRecords.
    """
    conditions = [PidXRef.localid.like(mrn_no) for mrn_no in mrn_nos]
    matched_persons = session.query(Person).join(PidXRef).filter(or_(*conditions)).all()

    matched_ids: set = find_ids_related_to_person(
        [person.localid for person in matched_persons], session
    )[0]

    return matched_ids


def masterrecord_ids_from_ukrdc_no(session: Session, ukrdc_nos: Iterable[str]):
    """
    Finds Ids from UKRDC number

    Note: We use the pattern {nhs_no}_ since our nationalid field seems
    to have trailing spaces. This has a side-effect of allowing partial matching.
    """
    conditions = [
        MasterRecord.nationalid.like(f"{ukrdc_no.strip()}_") for ukrdc_no in ukrdc_nos
    ]
    matched_ids = {
        mr.id
        for mr in session.query(MasterRecord.id)
        .filter(
            or_(*conditions),
            MasterRecord.nationalid_type.in_(["UKRDC"]),
        )
        .all()
    }

    return matched_ids


def masterrecord_ids_from_full_name(session: Session, names: Iterable[str]):
    """Finds Ids from full name"""
    conditions = []
    # SQLite has no concat func, so skip for tests :(
    if session.bind.dialect.name != "sqlite":
        conditions += [
            concat(MasterRecord.givenname, " ", MasterRecord.surname).ilike(name)
            for name in names
        ]
    conditions += [MasterRecord.givenname.ilike(name) for name in names]
    conditions += [MasterRecord.surname.ilike(name) for name in names]
    matched_ids = {
        mr.id for mr in session.query(MasterRecord.id).filter(or_(*conditions)).all()
    }

    return matched_ids


def masterrecord_ids_from_dob(
    session: Session, dobs: Iterable[Union[str, datetime.date]]
):
    """Finds Ids from date of birth"""
    conditions = [MasterRecord.date_of_birth == dob for dob in dobs]
    matched_ids = {
        mr.id for mr in session.query(MasterRecord.id).filter(or_(*conditions)).all()
    }

    return matched_ids


def masterrecord_ids_from_pidxref_no(session: Session, pid_nos: Iterable[str]):
    """Finds Ids from pidxref"""
    # We're searching for PidXRef entries, so we only care about Person.localid
    # if it's a CLPID (i.e. the ID type corresponding to a PidXRef lookup)
    query = session.query(Person).filter(Person.localid_type == "CLPID")

    conditions = [Person.localid.like(pid_no) for pid_no in pid_nos]
    matched_persons = query.filter(or_(*conditions)).all()

    matched_ids = set()

    for person in matched_persons:
        matched_ids |= find_ids_related_to_person([person.localid], session)[0]

    return matched_ids


def search_masterrecord_ids(  # pylint: disable=too-many-branches
    nhs_number: list[str],
    mrn_number: list[str],
    ukrdc_number: list[str],
    full_name: list[str],
    pidx: list[str],
    dob: list[str],
    search: list[str],
    jtrace: Session,
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

    return matched_ids
