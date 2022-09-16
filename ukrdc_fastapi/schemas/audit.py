import datetime
from typing import List, Optional

from pydantic.fields import Field
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies.audit import Resource

from .base import OrmModel


class AccessEventSchema(OrmModel):
    """Event information for a single HTTP access event"""

    id: int = Field(alias="event", description="Access event ID")
    time: datetime.datetime = Field(..., description="Access event timestamp")

    uid: str = Field(alias="userId", description="User ID")
    cid: str = Field(alias="clientId", description="Client ID")
    sub: str = Field(alias="userEmail", description="User email address")

    path: str = Field(..., description="Access event path")
    method: str = Field(..., description="Access event HTTP method")
    body: Optional[str] = Field(None, description="Access event HTTP body")


class AuditEventSchema(OrmModel):
    """Event information for a single audit event"""

    id: int = Field(..., description="Audit event ID")
    access_event: AccessEventSchema = Field(..., description="Access event")

    resource: Optional[str] = Field(None, description="Resource accessed")
    resource_id: Optional[str] = Field(None, description="Resource ID")

    operation: str = Field(..., description="Audit event operation")

    children: Optional[List["AuditEventSchema"]] = Field(
        None, description="Child events"
    )

    identifiers: List[str] = Field(..., description="Additional resource identifiers")

    def populate_identifiers(self, jtrace: Session, ukrdc3: Session):
        """
        Use database sessions to populate an array of resource identifier strings.
        The identifiers will vary depending on resource type, but should be listed
        in descending priority.
        Identifiers include names, patient numbers, record types etc
        """
        if self.resource == Resource.PATIENT_RECORD.value:
            record = ukrdc3.query(PatientRecord).get(self.resource_id)
            if record:
                first_mrn = next(
                    number
                    for number in record.patient.numbers
                    if number.numbertype == "MRN"
                )
                if record.patient.name:
                    self.identifiers.append(
                        f"{record.patient.name.given} {record.patient.name.family}"
                    )
                self.identifiers.extend(
                    [
                        first_mrn.organization,
                        first_mrn.patientid,
                    ]
                )
        elif self.resource == Resource.MASTER_RECORD.value:
            master_record = jtrace.query(MasterRecord).get(self.resource_id)
            if master_record:
                self.identifiers = [
                    f"{master_record.givenname} {master_record.surname}",
                    master_record.nationalid_type,
                    master_record.nationalid.strip(),
                ]

        if self.children:
            for child in self.children:
                child.populate_identifiers(jtrace, ukrdc3)


AuditEventSchema.update_forward_refs()
