from sqlalchemy import and_, select
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import false as sql_false
from sqlalchemy.sql.selectable import Select
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.errorsdb import Message
from ukrdc_sqla.ukrdc import PatientNumber, PatientRecord

from ukrdc_fastapi.query.masterrecords import (
    select_masterrecords_related_to_masterrecord,
)


def select_patientrecords_related_to_ukrdcid(ukrdcid: str) -> Select:
    """Get a select of PatientRecords with a particular UKRDCID

    Args:
        ukrdcid (str): UKRDC ID

    Returns:
        Select: SQLAlchemy select
    """
    # Return all records with a matching UKRDC ID that the user has permission to access
    return select(PatientRecord).where(PatientRecord.ukrdcid == ukrdcid)


def select_patientrecords_related_to_ni(ni: str) -> Select:
    """Get a select of PatientRecords with a particular national identifier

    Args:
        ni (str): National ID

    Returns:
        Select: SQLAlchemy select
    """
    # Return all records with a matching UKRDC ID that the user has permission to access
    return (
        select(PatientRecord)
        .join(PatientNumber, PatientNumber.pid == PatientRecord.pid)
        .where(and_(PatientNumber.numbertype == "NI", PatientNumber.patientid == ni))
    )


def select_patientrecords_related_to_message(message_obj: Message) -> Select:
    """Get a query of PatientRecords related to a particular message

    Args:
        message_obj (Message): UKRDC Message object

    Returns:
        Select: SQLAlchemy select
    """

    # If no NI exists on the message, return an empty query with the correct type
    if not message_obj.ni:
        return select(PatientRecord).where(sql_false())

    return select_patientrecords_related_to_ni(message_obj.ni).where(
        PatientRecord.sendingfacility == message_obj.facility
    )


def select_patientrecords_related_to_masterrecord(
    record: MasterRecord, jtrace: Session
) -> Select:
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
    stmt = select_masterrecords_related_to_masterrecord(record, jtrace).where(
        MasterRecord.nationalid_type == "UKRDC"
    )
    related_records = jtrace.scalars(stmt).all()

    # Strip whitespace. Needed until we fix the issue with fixed-length nationalid column
    related_ukrdcids = [record.nationalid.strip() for record in related_records]

    # Build queries for all records with matching UKRDC IDs
    return select(PatientRecord).where(PatientRecord.ukrdcid.in_(related_ukrdcids))
