from sqlalchemy.orm import Query, Session
from ukrdc_sqla.ukrdc import PatientRecord, ProgramMembership


def get_active_memberships_for_patientrecord(
    ukrdc3: Session, record: PatientRecord
) -> Query:
    """
    Get a list of active program memberships on any record
    related to a given PatientRecord.

    Args:
        ukrdc3 (Session): UKRDC3 database session
        record (PatientRecord): PatientRecord to find memberships for

    Returns:
        Query: [description]
    """
    return (
        ukrdc3.query(ProgramMembership)
        .join(PatientRecord)
        .filter(PatientRecord.ukrdcid == record.ukrdcid)
        .filter(
            ProgramMembership.to_time == None  # pylint: disable=singleton-comparison
        )
    )


def record_has_active_membership(
    ukrdc3: Session, record: PatientRecord, membership_type: str
) -> bool:
    """
    Check if any record related to a given PatientRecord has an active
    membership of a given type.

    Args:
        ukrdc3 (Session): UKRDC3 database session
        record (PatientRecord): PatientRecord to find memberships for
        membership_type (str): Program membership type to check for

    Returns:
        bool: Does the patient have the specified membership
    """
    active_memberships = get_active_memberships_for_patientrecord(ukrdc3, record)

    active_memberships_of_this_type = active_memberships.filter(
        ProgramMembership.program_name.like(membership_type + "%")
    ).all()

    if len(active_memberships_of_this_type) > 0:
        return True
    return False
