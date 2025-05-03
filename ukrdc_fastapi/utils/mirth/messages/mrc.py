from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Facility, PatientRecord

from xml.etree.ElementTree import Element, SubElement, tostring  # nosec

from ukrdc_fastapi.exceptions import (
    NoActiveMembershipError,
    ResourceNotFoundError,
    MRCOutboundDisabledError,
)
from ukrdc_fastapi.query.memberships import record_has_active_membership

EXCLUDED_EXTRACTS = ["RADAR", "SURVEY", "HSMIG"]


def build_mrc_sync_message(record: PatientRecord, ukrdc3: Session) -> list[str]:
    """
    Build rawData messages to sync a PatientRecord with MRC
    Each message type and resource ID generates a separate message,
    and each should be sent to Mirth in turn to effectively sync the
    entire record

    Args:
        record (PatientRecord): Patient record to sync
        ukrdc3 (Session): UKRDC3 session

    Returns:
        list[str]: XML rawData for Mirth messages
    """
    # Check memberships

    if not record_has_active_membership(ukrdc3, record, "MRC"):
        raise NoActiveMembershipError(
            f"Patient {record.pid} has no active MRC membership"
        )

    # Check facility-level overrides

    facility = ukrdc3.get(Facility, record.sendingfacility)

    if not facility:
        raise ResourceNotFoundError(record.sendingfacility or "None")

    # TODO: Add facility-level override for MRC outbound sending
    # if not facility.mrc_out:
    #     raise MRCOutboundDisabledError(
    #         f"MRC outbound sending disabled for {facility.code}"
    #     )

    # Check for excluded sending extracts

    if record.sendingextract in EXCLUDED_EXTRACTS:
        raise MRCOutboundDisabledError(
            f"MRC outbound sending disabled for {record.sendingextract}"
        )

    return build_rda_sync_message(record.pid)


def build_rda_sync_message(pid: str) -> str:
    """Send a PID to Mirth for MRC sync

    Args:
        pid (str): PatientRecord.pid to export

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("result")

    pid_element = SubElement(root, "pid")
    pid_element.text = pid

    return tostring(root, encoding="unicode")
