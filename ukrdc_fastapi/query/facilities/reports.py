import datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, select
from sqlalchemy.sql.selectable import Select
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Facility, Patient, PatientRecord, ProgramMembership

from ukrdc_fastapi.exceptions import MissingFacilityError


def select_facility_report_cc001(
    ukrdc3: Session,
    facility_code: str,
) -> Select:
    """
    Custom Cohort Report 001:
        No treatment or programme membership to explain presence in UKRDC.
        Excludes patients with a known date of death prior to 5 years ago from the time of query.

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_code (str): Facility/unit code

    Returns:
        Select: Select of patients mathching the report conditions
    """
    # Assert the facility exists
    stmt = select(Facility).where(Facility.code == facility_code)
    facility = ukrdc3.scalars(stmt).first()

    if not facility:
        raise MissingFacilityError(facility_code)

    # Calculate the DoD cutoff date
    dod_cutoff = datetime.datetime.utcnow() - relativedelta(years=5)

    # Find all records in the facility with no treatment, matching the DoD condition
    q_no_treatment = (
        select(PatientRecord)
        .join(Patient)
        .where(PatientRecord.sendingfacility == facility.code)
        .where(PatientRecord.sendingextract == "UKRDC")
        .where(PatientRecord.treatments == None)  # noqa: E711 # No treatments
        .where(
            or_(
                Patient.deathtime == None,  # noqa: E711
                Patient.deathtime >= dod_cutoff,
            )
        )
    ).subquery()

    # Find all the rows in q_no_treatment with a UKRDCID that has memberships attached to it
    q_no_treatment_but_has_memberships = (
        select(PatientRecord.ukrdcid)
        .join(q_no_treatment, PatientRecord.ukrdcid == q_no_treatment.c.ukrdcid)
        .join(ProgramMembership, ProgramMembership.pid == PatientRecord.pid)
    ).subquery()

    # Return all the rows in q_no_treatment that do NOT appear in q_has_memberships
    q_no_treatment_and_no_memberships = select(q_no_treatment).where(
        q_no_treatment.c.ukrdcid.notin_(q_no_treatment_but_has_memberships)
    )

    # Return PatientRecord ORM objects from q_no_treatment_and_no_memberships
    return select(PatientRecord).where(
        PatientRecord.ukrdcid.in_(select(q_no_treatment_and_no_memberships.c.ukrdcid))
    )


def select_facility_report_pm001(
    ukrdc3: Session,
    facility_code: str,
) -> Select:
    """
    Program Membership Report 001:
        Patients with no *active* PKB membership record

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_code (str): Facility/unit code

    Returns:
        Select: Select of patients mathching the report conditions
    """
    # Assert the facility exists
    stmt = select(Facility).where(Facility.code == facility_code)
    facility = ukrdc3.execute(stmt).scalar_one()

    if not facility:
        raise MissingFacilityError(facility_code)

    # All UKRDC IDs with active PKB program memberships
    q2 = (
        select(PatientRecord.ukrdcid)
        .join(ProgramMembership, ProgramMembership.pid == PatientRecord.pid)
        .where(ProgramMembership.program_name == "PKB")
        .where(ProgramMembership.totime == None)  # noqa: E711 # No end time
    ).subquery()

    return (
        select(PatientRecord)
        .where(PatientRecord.sendingfacility == facility.code)
        .where(PatientRecord.sendingextract == "UKRDC")
        .where(PatientRecord.ukrdcid.notin_(q2))  # No related program memberships
    )
