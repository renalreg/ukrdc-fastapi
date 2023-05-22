import datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from sqlalchemy.orm import Query, Session
from ukrdc_sqla.ukrdc import Facility, Patient, PatientRecord, ProgramMembership

from ukrdc_fastapi.exceptions import MissingFacilityError


def get_facility_report_cc001(
    ukrdc3: Session,
    facility_code: str,
) -> Query:
    """
    Custom Cohort Report 001:
        No treatment or programme membership to explain presence in UKRDC.
        Excludes patients with a known date of death prior to 5 years ago from the time of query.

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_code (str): Facility/unit code

    Returns:
        Query: Query of patients mathching the report conditions
    """
    # Assert the facility exists
    facility = ukrdc3.query(Facility).filter(Facility.code == facility_code).first()

    if not facility:
        raise MissingFacilityError(facility_code)

    # Calculate the DoD cutoff date
    dod_cutoff = datetime.datetime.utcnow() - relativedelta(years=5)

    # Find all records in the facility with no treatment, matching the DoD condition
    q_no_treatment = (
        ukrdc3.query(PatientRecord)
        .join(Patient)
        .filter(PatientRecord.sendingfacility == facility.code)
        .filter(PatientRecord.sendingextract == "UKRDC")
        .filter(PatientRecord.treatments == None)  # noqa: E711 # No treatments
        .filter(
            or_(
                Patient.deathtime == None,  # noqa: E711
                Patient.deathtime >= dod_cutoff,
            )
        )
    )

    # Create a subquery for all records in the facility with no treatment
    q_ukrdcids_to_check = q_no_treatment.subquery()

    # Find all the rows in q_no_treatment with a UKRDCID that has memberships attached to it
    q_no_treatment_but_has_memberships = (
        ukrdc3.query(PatientRecord.ukrdcid)
        .join(
            q_ukrdcids_to_check, PatientRecord.ukrdcid == q_ukrdcids_to_check.c.ukrdcid
        )
        .join(ProgramMembership, ProgramMembership.pid == PatientRecord.pid)
    )

    # Return all the rows in q_no_treatment that do NOT appear in q_has_memberships
    q_no_treatment_and_no_memberships = q_no_treatment.filter(
        PatientRecord.ukrdcid.notin_(q_no_treatment_but_has_memberships)
    )

    return q_no_treatment_and_no_memberships


def get_facility_report_pm001(
    ukrdc3: Session,
    facility_code: str,
) -> Query:
    """
    Program Membership Report 001:
        Patients with no *active* PKB membership record

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_code (str): Facility/unit code

    Returns:
        Query: Query of patients mathching the report conditions
    """
    # Assert the facility exists
    facility = ukrdc3.query(Facility).filter(Facility.code == facility_code).first()

    if not facility:
        raise MissingFacilityError(facility_code)

    # All UKRDC IDs with active PKB program memberships
    q2 = (
        ukrdc3.query(PatientRecord.ukrdcid)
        .join(ProgramMembership, ProgramMembership.pid == PatientRecord.pid)
        .filter(ProgramMembership.program_name == "PKB")
        .filter(ProgramMembership.totime == None)  # noqa: E711 # No end time
    )

    q = (
        ukrdc3.query(PatientRecord)
        .filter(PatientRecord.sendingfacility == facility.code)
        .filter(PatientRecord.sendingextract == "UKRDC")
        .filter(PatientRecord.ukrdcid.notin_(q2))  # No related program memberships
    )

    return q
    return q
