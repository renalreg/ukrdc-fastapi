from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.query.masterrecords import get_masterrecords_related_to_masterrecord


def get_patientrecords_related_to_patientrecord(
    record: PatientRecord, ukrdc3: Session
) -> Query:
    """Get a query of PatientRecords with the same UKRDCID as a given PatientRecord

    Args:
        record (PatientRecord): PatientRecord object
        ukrdc3 (Session): UKRDC SQLAlchemy session

    Returns:
        Query: SQLAlchemy query
    """
    if not record.ukrdcid:
        raise AttributeError(
            f"UKRDC ID for record {record.pid} is missing or NULL. This should never happen."
        )

    # Return all records with a matching UKRDC ID that the user has permission to access
    return ukrdc3.query(PatientRecord).filter(PatientRecord.ukrdcid == record.ukrdcid)


def get_patientrecords_related_to_masterrecord(
    record: MasterRecord, ukrdc3: Session, jtrace: Session
) -> Query:
    """
    Get a list of patient records related to a Master Record.

    First finds all UKRDC Master Records linked to the given record ID via
    the LinkRecord tree. Then returns a list of all Patient Records with a
    UKRDC ID in that list.

    Args:
        ukrdc3 (Session): UKRDC SQLAlchemy session
        jtrace (Session): JTRACE SQLAlchemy session
        record_id (str): MasterRecord ID

    Returns:
        Query: SQLAlchemy query
    """
    # For the time being, it's possible for a patient to have multiple UKRDC IDs
    # Here, we get a list of all related UKRDC IDs from JTRACE
    related_ukrdc_records = get_masterrecords_related_to_masterrecord(
        record, jtrace
    ).filter(MasterRecord.nationalid_type == "UKRDC")

    # Strip whitespace. Needed until we fix the issue with fixed-length nationalid column
    related_ukrdcids = [record.nationalid.strip() for record in related_ukrdc_records]

    # Build queries for all records with matching UKRDC IDs
    return ukrdc3.query(PatientRecord).filter(
        PatientRecord.ukrdcid.in_(related_ukrdcids)
    )
