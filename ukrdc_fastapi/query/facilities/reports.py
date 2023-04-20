from sqlalchemy.orm import Query, Session
from ukrdc_sqla.ukrdc import Facility, PatientRecord, ProgramMembership

from ukrdc_fastapi.exceptions import MissingFacilityError


def get_facility_report_cc001(
    ukrdc3: Session,
    facility_code: str,
) -> Query:
    """
    Custom Cohort Report 001:
        No treatment or programme membership to explain presence in UKRDC

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

    q2 = ukrdc3.query(PatientRecord.ukrdcid).join(
        ProgramMembership, ProgramMembership.pid == PatientRecord.pid
    )  # All UKRDC IDs with program memberships

    q = (
        ukrdc3.query(PatientRecord)
        .filter(PatientRecord.sendingfacility == facility.code)
        .filter(PatientRecord.sendingextract == "UKRDC")
        .filter(PatientRecord.treatments == None)  # noqa: E711 # No treatments
        .filter(PatientRecord.ukrdcid.notin_(q2))  # No related program memberships
    )

    return q
