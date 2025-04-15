from typing import Optional

# Override Bandit warnings, since we use this to generate XML, not parse
from xml.etree.ElementTree import Element, SubElement, tostring  # nosec


def build_merge_message(superseding: int, superseded: int) -> str:
    """Build rawData for two master records be merged.
    Note: Superseded and superseding are spelt wrong in the
    Mirth messages. This is known.

    Args:
        superseding (int): MasterRecord.id of first item in merge
        superseded (int): MasterRecord.id of second item in merge

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("request")

    superceding_element = SubElement(root, "superceding")
    superceding_element.text = str(superseding)

    superceeded_element = SubElement(root, "superceeded")
    superceeded_element.text = str(superseded)

    return tostring(root, encoding="unicode")


def build_unlink_message(
    master_record: int,
    person_id: int,
    user: str,
    description: Optional[str] = None,
) -> str:
    """Build rawData for a Person record be unlinked from a MasterRecord

    Args:
        master_record (int): MasterRecord.id
        person_id (int): Person.id
        user (str): End user initiating the unlink
        description (Optional[str], optional): Unlink comments. Defaults to None.

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("request")

    mr_element = SubElement(root, "masterRecord")
    mr_element.text = str(master_record)

    id_element = SubElement(root, "personId")
    id_element.text = str(person_id)

    ud_element = SubElement(root, "updateDescription")
    ud_element.text = str(description or "")

    ub_element = SubElement(root, "updatedBy")
    ub_element.text = user[:20]

    return tostring(root, encoding="unicode")


def build_update_workitem_message(
    workitem_id: int, status: int, description: Optional[str], user: str
) -> str:
    """Build rawData to update a WorkItem record

    Args:
        workitem_id (int): WorkItem.id to update
        status (int): New WorkItem.status
        description (Optional[str]): Update comments
        user (str): End user initiating the update

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("request")

    wi_element = SubElement(root, "workitem")
    wi_element.text = str(workitem_id)

    st_element = SubElement(root, "status")
    st_element.text = str(status)

    ud_element = SubElement(root, "updateDescription")
    ud_element.text = str(description or "")[:100]

    ub_element = SubElement(root, "updatedBy")
    ub_element.text = user[:20]

    return tostring(root, encoding="unicode")


def build_close_workitem_message(workitem_id: int, description: str, user: str) -> str:
    """Build rawData to close a WorkItem without merging

    Args:
        workitem_id (int): WorkItem.id to close
        description (str): Comments on WorkItem close
        user (str): End user initiating the close

    Returns:
        str: XML rawData for Mirth message
    """
    return build_update_workitem_message(workitem_id, 3, description, user)


def build_export_tests_message(pid: str) -> str:
    """Build rawData to export PatientRecord test results to PV

    Args:
        pid (str): PatientRecord.pid to export

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("result")

    pid_element = SubElement(root, "pid")
    pid_element.text = pid

    tst_element = SubElement(root, "tests")
    tst_element.text = "FULL"

    return tostring(root, encoding="unicode")


def build_export_docs_message(pid: str) -> str:
    """Build rawData to export PatientRecord documents to PV

    Args:
        pid (str): PatientRecord.pid to export

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("result")

    pid_element = SubElement(root, "pid")
    pid_element.text = pid

    doc_element = SubElement(root, "documents")
    doc_element.text = "FULL"

    return tostring(root, encoding="unicode")


def build_export_all_message(pid: str) -> str:
    """Buold rawData to export PatientRecord test results and documents to PV

    Args:
        pid (str): PatientRecord.pid to export

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("result")

    pid_element = SubElement(root, "pid")
    pid_element.text = pid

    tst_element = SubElement(root, "tests")
    tst_element.text = "FULL"

    doc_element = SubElement(root, "documents")
    doc_element.text = "FULL"

    return tostring(root, encoding="unicode")


def build_export_radar_message(pid: str) -> str:
    """Build rawData to export a PatientRecord to RaDaR

    Args:
        pid (str): PatientRecord.pid to export

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("result")

    pid_element = SubElement(root, "pid")
    pid_element.text = pid

    return tostring(root, encoding="unicode")


def build_create_partner_membership_message(ukrdcid: str, partner: str) -> str:
    """Build rawData to create a new partner membership for a given UKRDCID

    Args:
        ukrdcid (str): Patients UKRDC ID
        partner (str): Partner name

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("request")

    ukrdcid_element = SubElement(root, "ukrdcid")
    ukrdcid_element.text = ukrdcid

    partner_element = SubElement(root, "partner")
    partner_element.text = partner

    return tostring(root, encoding="unicode")
