from typing import Literal, Optional, get_args

# Override Bandit warnings, since we use this to generate XML, not parse
from xml.etree.ElementTree import Element, SubElement, tostring  # nosec

from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import Facility, PatientRecord

from ukrdc_fastapi.exceptions import (
    NoActiveMembershipError,
    PKBOutboundDisabledError,
    ResourceNotFoundError,
)
from ukrdc_fastapi.query.memberships import record_has_active_membership

MessageType = Literal[
    "ADT_A28", "MDM_T02_CP", "MDM_T02_DOC", "ORU_R01_LAB", "ORU_R01_OBS"
]

ALL_MSG_TYPES: list[MessageType] = list(get_args(MessageType))

EXCLUDED_EXTRACTS = ["RADAR", "SURVEY", "HSMIG"]

# PKB Memberships


def build_pkb_membership_message(ukrdcid: str) -> str:
    """Build rawData to add a PKB membership to a given UKRDCID

    Args:
        ukrdcid (str): Patients UKRDC ID

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("result")

    ukrdcid_element = SubElement(root, "ukrdcid")
    ukrdcid_element.text = ukrdcid

    return tostring(root, encoding="unicode")


# PKB record data


def _get_facility_exclusions(facility: Facility) -> list[str]:
    """
    Fetch a list of PKB HL7 message types that should be excluded for
    a given sending facility

    Args:
        facility (Facility): Sending facility

    Returns:
        [type]: [description]
    """
    excl: Optional[list[str]] = (
        list(facility.pkb_msg_exclusions) if facility.pkb_msg_exclusions else None
    )
    return excl or []


def _build_pkb_sync_base_xml(record: PatientRecord, msg_type: MessageType) -> Element:
    """
    Build base XML node for PKB sync messages

    Args:
        record (PatientRecord): Patient record to sync
        msg_type (MessageType): Message type to sync

    Returns:
        Element: Base XML node
    """
    root = Element("result")

    msg_type_element = SubElement(root, "msg_type")
    msg_type_element.text = msg_type

    pid_element = SubElement(root, "pid")
    pid_element.text = str(record.pid)

    return root


def _build_pkb_sync_messages_mdm_t02_doc(record: PatientRecord) -> list[str]:
    """
    Build rawData messages to sync a PatientRecord with PKB for
    MDM_T02_DOC messages

    Args:
        record (PatientRecord): Patient record to sync

    Returns:
        list[str]: XML rawData for Mirth messages
    """
    messages = []

    for document in record.documents:
        root = _build_pkb_sync_base_xml(record, "MDM_T02_DOC")
        id_element = SubElement(root, "id")
        id_element.text = str(document.id)

        messages.append(tostring(root, encoding="unicode"))

    return messages


def _build_pkb_sync_messages_oru_r01_lab(record: PatientRecord) -> list[str]:
    """
    Build rawData messages to sync a PatientRecord with PKB for
    ORU_R01_LAB messages

    Args:
        record (PatientRecord): Patient record to sync

    Returns:
        list[str]: XML rawData for Mirth messages
    """
    messages = []

    for order in record.lab_orders:
        root = _build_pkb_sync_base_xml(record, "ORU_R01_LAB")
        id_element = SubElement(root, "id")
        id_element.text = str(order.id)

        messages.append(tostring(root, encoding="unicode"))

    return messages


def _build_pkb_sync_messages_oru_r01_obs(record: PatientRecord) -> list[str]:
    """
    Build rawData messages to sync a PatientRecord with PKB for
    ORU_R01_OBS messages

    Args:
        record (PatientRecord): Patient record to sync

    Returns:
        list[str]: XML rawData for Mirth messages
    """
    messages = []

    for observation in record.observations:
        root = _build_pkb_sync_base_xml(record, "ORU_R01_OBS")
        id_element = SubElement(root, "id")
        id_element.text = str(observation.id)

        messages.append(tostring(root, encoding="unicode"))

    return messages


def _build_pkb_sync_messages_generic(
    record: PatientRecord, msg_type: MessageType
) -> str:
    """
    Build rawData messages to sync a PatientRecord with PKB for
    generic message types

    Args:
        record (PatientRecord): Patient record to sync
        msg_type (MessageType): Message type to sync

    Returns:
        str: XML rawData for Mirth message
    """
    return tostring(_build_pkb_sync_base_xml(record, msg_type), encoding="unicode")


def build_pkb_sync_messages(record: PatientRecord, ukrdc3: Session) -> list[str]:
    """
    Build rawData messages to sync a PatientRecord with PKB
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

    if not record_has_active_membership(ukrdc3, record, "PKB"):
        raise NoActiveMembershipError(
            f"Patient {record.pid} has no active PKB membership"
        )

    # Check facility-level overrides

    facility = ukrdc3.get(Facility, record.sendingfacility)

    if not facility:
        raise ResourceNotFoundError(record.sendingfacility or "None")

    if not facility.pkb_out:
        raise PKBOutboundDisabledError(
            f"PKB outbound sending disabled for {facility.code}"
        )

    msg_type_exclusions = _get_facility_exclusions(facility)
    includes_message_types: list[str] = [
        t for t in ALL_MSG_TYPES if t not in msg_type_exclusions
    ]

    # Check for excluded sending extracts

    if record.sendingextract in EXCLUDED_EXTRACTS:
        raise PKBOutboundDisabledError(
            f"PKB outbound sending disabled for {record.sendingextract}"
        )

    # Start generating messages

    messages: list[str] = []

    if "ADT_A28" in includes_message_types:
        messages.append(_build_pkb_sync_messages_generic(record, "ADT_A28"))
    if "MDM_T02_CP" in includes_message_types:
        messages.append(_build_pkb_sync_messages_generic(record, "MDM_T02_CP"))

    if "MDM_T02_DOC" in includes_message_types:
        messages.extend(_build_pkb_sync_messages_mdm_t02_doc(record))
    if "ORU_R01_LAB" in includes_message_types:
        messages.extend(_build_pkb_sync_messages_oru_r01_lab(record))
    if "ORU_R01_OBS" in includes_message_types:
        messages.extend(_build_pkb_sync_messages_oru_r01_obs(record))

    return messages
