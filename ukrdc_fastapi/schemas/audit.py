import datetime
from typing import List, Optional

from pydantic.fields import Field
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.ukrdc import PatientRecord, PatientNumber

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

    children: List["AuditEventSchema"] = Field([], description="Child events")

    identifiers: List[str] = Field([], description="Additional resource identifiers")

    def populate_identifiers(
        self, jtrace: Optional[Session], ukrdc3: Optional[Session]
    ):
        """
        Use database sessions to populate an array of resource identifier strings.
        The identifiers will vary depending on resource type, but should be listed
        in descending priority.
        Identifiers include names, patient numbers, record types etc
        """
        # For PatientRecord items
        if self.resource == Resource.PATIENT_RECORD.value and ukrdc3:
            record = ukrdc3.get(PatientRecord, self.resource_id)
            if record:
                # Obtain the first known MRN for the patient
                first_mrn: Optional[PatientNumber] = None
                # Try to find the first PatientNumber of type MRN
                try:
                    first_mrn = next(
                        number
                        for number in record.patient.numbers
                        if number.numbertype == "MRN"
                    )
                # If no matching PatientNumber is found, skip this identifier
                except StopIteration:
                    pass
                # If the patient has a name, add it to the identifiers
                if record.patient.name:
                    self.identifiers.append(
                        f"{record.patient.name.given} {record.patient.name.family}"
                    )
                # If the patient has an MRN, add it to the identifiers
                if first_mrn:
                    if first_mrn.organization:
                        self.identifiers.append(first_mrn.organization)
                    if first_mrn.patientid:
                        self.identifiers.append(first_mrn.patientid)
        # For MasterRecord items
        elif self.resource == Resource.MASTER_RECORD.value and jtrace:
            master_record = jtrace.get(MasterRecord, self.resource_id)
            if master_record:
                self.identifiers = [
                    f"{master_record.givenname} {master_record.surname}",
                    master_record.nationalid_type,
                    master_record.nationalid.strip(),
                ]

        # Recursively populate children
        if self.children:
            for child in self.children:
                child.populate_identifiers(jtrace, ukrdc3)


AuditEventSchema.update_forward_refs()
