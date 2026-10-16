"""
Query code snippets that are useful in more than one type of resource query
"""

from sqlalchemy import false, or_, select
from sqlalchemy.orm import Session, aliased
from ukrdc_sqla.empi import Person
from ukrdc_sqla.ukrdc import PatientNumber, PatientRecord


def person_belongs_to_units(person: Person, units: list[str]) -> bool:
    """Find if a Person record is associated with any of a set of unit codes

    Args:
        person (Person): Person record to check
        units (list[str]): List of unit codes

    Returns:
        bool: True if the Person is associated with a unit from the list.
    """
    return any(xref.sending_facility in units for xref in person.xref_entries)


def get_nis_for_programs(ukrdc3: Session, programs: list[str]) -> list[str]:
    """Find the patient numbers of patients who have a PKB and/or RADAR record.

    Args:
        ukrdc3 (Session): SQLAlchemy session for the ukrdc3 database
        programs (list[str]): "PKB" and/or "RADAR". Any other value matches nothing.

    Returns:
        list[str]: NHS/CHI/HSC numbers of matching patients, for filtering
        errorsdb messages by Message.ni
    """

    membership = aliased(PatientRecord)

    conditions = []
    if "PKB" in programs:
        conditions.append(membership.sendingfacility == "PKB")
    if "RADAR" in programs:
        conditions.append(membership.sendingextract == "RADAR")

    stmt_ukrdcids = (
        select(PatientRecord.ukrdcid)
        .join(membership, membership.ukrdcid == PatientRecord.ukrdcid)
        .where(PatientRecord.sendingextract.in_(["PV", "UKRDC"]))
        .where(or_(*conditions) if conditions else false())
        .distinct()
    )
    matching_ukrdcids = ukrdc3.scalars(stmt_ukrdcids).all()

    stmt_ni = (
        select(PatientNumber.patientid)
        .join(PatientRecord, PatientRecord.pid == PatientNumber.pid)
        .where(PatientRecord.ukrdcid.in_(matching_ukrdcids))
        .where(PatientNumber.organization.in_(["NHS", "CHI", "HSC"]))
    )
    return list(ukrdc3.scalars(stmt_ni).all())
