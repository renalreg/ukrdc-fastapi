from sqlalchemy import and_
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import false as sql_false
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.ukrdc import PatientNumber, PatientRecord

from ukrdc_fastapi.query.masterrecords import get_masterrecords_related_to_masterrecord


def get_patientrecords_related_to_ukrdcid(ukrdcid: str, ukrdc3: Session) -> Query:
    """Get a query of PatientRecords with a particular UKRDCID

    Args:
        ukrdcid (str): UKRDC ID
        ukrdc3 (Session): UKRDC SQLAlchemy session

    Returns:
        Query: SQLAlchemy query
    """
    # Return all records with a matching UKRDC ID that the user has permission to access
    return ukrdc3.query(PatientRecord).filter(PatientRecord.ukrdcid == ukrdcid)


def get_patientrecords_related_to_ni(ni: str, ukrdc3: Session) -> Query:
    """Get a query of PatientRecords with a particular national identifier

    Args:
        ni (str): National ID
        ukrdc3 (Session): UKRDC SQLAlchemy session

    Returns:
        Query: SQLAlchemy query
    """
    # Return all records with a matching UKRDC ID that the user has permission to access
    return (
        ukrdc3.query(PatientRecord)
        .join(PatientNumber, PatientNumber.pid == PatientRecord.pid)
        .filter(and_(PatientNumber.numbertype == "NI", PatientNumber.patientid == ni))
    )


def get_patientrecords_related_to_message(
    message_obj: Message, ukrdc3: Session
) -> Query:
    """Get a query of PatientRecords related to a particular message

    Args:
        message_obj (Message): UKRDC Message object
        ukrdc3 (Session): UKRDC SQLAlchemy session

    Returns:
        Query: SQLAlchemy query
    """

    # If no NI exists on the message, return an empty query with the correct type
    if not message_obj.ni:
        return ukrdc3.query(PatientRecord).filter(sql_false())

    records = get_patientrecords_related_to_ni(message_obj.ni, ukrdc3)
    records = records.filter(PatientRecord.sendingfacility == message_obj.facility)

    return records


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
