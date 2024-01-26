from sqlalchemy import null, select
from sqlalchemy.sql.selectable import Select
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import PatientRecord, ProgramMembership


def get_active_memberships_for_patientrecord(record: PatientRecord) -> Select:
    """
    Get a list of active program memberships on any record
    related to a given PatientRecord.

    Args:
        ukrdc3 (Session): UKRDC3 database session
        record (PatientRecord): PatientRecord to find memberships for

    Returns:
        Select: [description]
    """
    return (
        select(ProgramMembership)
        .join(PatientRecord)
        .where(PatientRecord.ukrdcid == record.ukrdcid)
        .where(ProgramMembership.to_time == null())
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
    stmt = get_active_memberships_for_patientrecord(record)
    stmt = stmt.where(ProgramMembership.program_name.like(membership_type + "%"))

    active_memberships_of_this_type = ukrdc3.scalars(stmt).all()

    if active_memberships_of_this_type:
        return True
    return False
