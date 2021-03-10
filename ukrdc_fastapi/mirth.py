from typing import Dict, Optional

# Override Bandit warnings, since we use this to generate XML, not parse
from xml.etree.ElementTree import Element, SubElement, tostring  # nosec

import requests
from fastapi import HTTPException
from pydantic import BaseModel
from requests.exceptions import RequestException


class MirthMessageResponseSchema(BaseModel):
    """Response schema for Mirth message post views"""

    status: str
    message: str


class _MirthEMPIConnection:
    """
    Class to handle requests being sent to our custom EMPI API channel
    """

    def __init__(self, parent: "MirthConnection") -> None:
        self.parent: "MirthConnection" = parent

    def merge(self, superceding: str, superceeded: str) -> MirthMessageResponseSchema:
        """Request two master records be merged.

        Args:
            superceding (str): MasterRecord.id of first item in merge
            superceeded (str): MasterRecord.id of second item in merge

        Returns:
            MirthMessageResponseSchema: Mirth response
        """
        root = Element("request")

        superceding_element = SubElement(root, "superceding")
        superceding_element.text = str(superceding)

        superceeded_element = SubElement(root, "superceeded")
        superceeded_element.text = str(superceeded)

        return self.parent.post(
            "/merge",
            tostring(root, encoding="unicode"),
            headers={"content-type": "application/xml"},
        )

    def unlink(
        self,
        master_record: str,
        person_id: str,
        user: str,
        description: Optional[str] = None,
    ) -> MirthMessageResponseSchema:
        """Request a Person record be unlinked from a MasterRecord

        Args:
            master_record (str): MasterRecord.id
            person_id (str): Person.id
            user (str): End user initiating the unlink
            description (Optional[str], optional): Unlink comments. Defaults to None.

        Returns:
            MirthMessageResponseSchema: Mirth response
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

        return self.parent.post(
            "/unlink",
            tostring(root, encoding="unicode"),
            headers={"content-type": "application/xml"},
        )

    def update_workitem(
        self, workitem_id: int, status: int, description: Optional[str], user: str
    ) -> MirthMessageResponseSchema:
        """Update a WorkItem record

        Args:
            workitem_id (int): WorkItem.id to update
            status (int): New WorkItem.status
            description (Optional[str]): Update comments
            user (str): End user initiating the update

        Returns:
            MirthMessageResponseSchema: Mirth response
        """
        root = Element("request")

        wi_element = SubElement(root, "workitem")
        wi_element.text = str(workitem_id)

        st_element = SubElement(root, "status")
        st_element.text = str(status)

        ud_element = SubElement(root, "updateDescription")
        ud_element.text = str(description or "")

        ub_element = SubElement(root, "updatedBy")
        ub_element.text = str(user)

        return self.parent.post(
            "/workitem-update",
            tostring(root, encoding="unicode"),
            headers={"content-type": "application/xml"},
        )

    def close_workitem(
        self, workitem_id: int, description: str, user: str
    ) -> MirthMessageResponseSchema:
        """Close a WorkItem without merging

        Args:
            workitem_id (int): WorkItem.id to close
            description (str): Comments on WorkItem close
            user (str): End user initiating the close

        Returns:
            MirthMessageResponseSchema: Mirth response
        """
        return self.update_workitem(workitem_id, 3, description, user)


class _MirthPVConnection:
    """
    Class to handle requests being sent to our custom PatientView API channel
    """

    def __init__(self, parent: "MirthConnection") -> None:
        self.parent: "MirthConnection" = parent

    def export_tests(self, pid: str) -> MirthMessageResponseSchema:
        """Export PatientRecord test results to PV

        Args:
            pid (str): PatientRecord.pid to export

        Returns:
            MirthMessageResponseSchema: Mirth response
        """
        root = Element("result")

        pid_element = SubElement(root, "pid")
        pid_element.text = str(pid)

        tst_element = SubElement(root, "tests")
        tst_element.text = "FULL"

        return self.parent.post(
            "/export-full-pv-data",
            tostring(root, encoding="unicode"),
            headers={"content-type": "application/xml"},
        )

    def export_docs(self, pid: str) -> MirthMessageResponseSchema:
        """Export PatientRecord documents to PV

        Args:
            pid (str): PatientRecord.pid to export

        Returns:
            MirthMessageResponseSchema: Mirth response
        """
        root = Element("result")

        pid_element = SubElement(root, "pid")
        pid_element.text = str(pid)

        doc_element = SubElement(root, "documents")
        doc_element.text = "FULL"

        return self.parent.post(
            "/export-full-pv-data",
            tostring(root, encoding="unicode"),
            headers={"content-type": "application/xml"},
        )

    def export_all(self, pid: str) -> MirthMessageResponseSchema:
        """Export PatientRecord test results and documents to PV

        Args:
            pid (str): PatientRecord.pid to export

        Returns:
            MirthMessageResponseSchema: Mirth response
        """
        root = Element("result")

        pid_element = SubElement(root, "pid")
        pid_element.text = str(pid)

        tst_element = SubElement(root, "tests")
        tst_element.text = "FULL"

        doc_element = SubElement(root, "documents")
        doc_element.text = "FULL"

        return self.parent.post(
            "/export-full-pv-data",
            tostring(root, encoding="unicode"),
            headers={"content-type": "application/xml"},
        )

    def export_radar(self, pid: str) -> MirthMessageResponseSchema:
        """Export PatientRecord to RaDaR

        Args:
            pid (str): PatientRecord.pid to export

        Returns:
            MirthMessageResponseSchema: Mirth response
        """
        root = Element("result")

        pid_element = SubElement(root, "pid")
        pid_element.text = str(pid)

        return self.parent.post(
            "/export-radar-data",
            tostring(root, encoding="unicode"),
            headers={"content-type": "application/xml"},
        )


class MirthConnection:
    """
    Class to handle requests being sent to our Mirth Connect instance
    """

    def __init__(self, mirth_url: str) -> None:
        self.url = mirth_url

        # Method namespaces
        self.empi = _MirthEMPIConnection(self)
        self.pv = _MirthPVConnection(self)  # pylint: disable=invalid-name

    def post(
        self, path: str, message: str, headers: Optional[Dict[str, str]] = None
    ) -> MirthMessageResponseSchema:
        """Post a message to the Mirth instance

        Args:
            path (str): Mirth channel URL path
            message (str): Encoded request body
            headers (Optional[Dict[str, str]], optional): Additional request headers. Defaults to None.

        Raises:
            HTTPException: Error in request to Mirth

        Returns:
            MirthMessageResponseSchema: Mirth response
        """
        path_clean = path.strip("/")

        url = f"{self.url}/{path_clean}/"
        headers = headers or {"content-type": "application/xml"}

        try:
            response: requests.Response = requests.post(
                url, data=message.strip(), headers=headers
            )
        except RequestException as e:
            raise HTTPException(502, detail="Error posting to Mirth") from e

        return MirthMessageResponseSchema(
            **{"status": "success", "message": response.text}
        )
