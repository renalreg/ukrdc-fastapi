from typing import Optional

# Override Bandit warnings, since we use this to generate XML, not parse
from xml.etree.ElementTree import Element, SubElement, tostring  # nosec

from pydantic import BaseModel


class MirthMessageResponseSchema(BaseModel):
    """Response schema for Mirth message post views"""

    status: str
    message: str


def build_merge_message(superceding: str, superceeded: str) -> str:
    """Build rawData for two master records be merged.

    Args:
        superceding (str): MasterRecord.id of first item in merge
        superceeded (str): MasterRecord.id of second item in merge

    Returns:
        str: XML rawData for Mirth message
    """
    root = Element("request")

    superceding_element = SubElement(root, "superceding")
    superceding_element.text = str(superceding)

    superceeded_element = SubElement(root, "superceeded")
    superceeded_element.text = str(superceeded)

    return tostring(root, encoding="unicode")


def build_unlink_message(
    master_record: str,
    person_id: str,
    user: str,
    description: Optional[str] = None,
) -> str:
    """Build rawData for a Person record be unlinked from a MasterRecord

    Args:
        master_record (str): MasterRecord.id
        person_id (str): Person.id
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
    ub_element.text = str(user)

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
    ub_element.text = str(user)[:20]

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
    pid_element.text = str(pid)

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
    pid_element.text = str(pid)

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
    pid_element.text = str(pid)

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
    pid_element.text = str(pid)

    return tostring(root, encoding="unicode")
