import datetime
from typing import List, Optional

from pydantic.fields import Field
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.dependencies.audit import Resource

from .base import OrmModel


class AccessEventSchema(OrmModel):
    id: int = Field(alias="event")
    time: datetime.datetime

    uid: str = Field(alias="userId")
    cid: str = Field(alias="clientId")
    sub: str = Field(alias="userEmail")

    path: str
    method: str
    body: Optional[str]


class AuditEventSchema(OrmModel):
    id: int
    access_event: AccessEventSchema

    resource: Optional[str]
    resource_id: Optional[str]

    operation: str

    children: Optional[List["AuditEventSchema"]]

    identifiers: List[str] = []

    def populate_identifiers(self, jtrace: Session, ukrdc3: Session):
        if self.resource == Resource.PATIENT_RECORD.value:
            record = ukrdc3.query(PatientRecord).get(self.resource_id)
            first_mrn = next(
                number
                for number in record.patient.numbers
                if number.numbertype == "MRN"
            )
            if record:
                self.identifiers = [
                    f"{record.patient.name.given} {record.patient.name.family}",
                    first_mrn.organization,
                    first_mrn.patientid,
                ]
        elif self.resource == Resource.MASTER_RECORD.value:
            record = jtrace.query(MasterRecord).get(self.resource_id)
            if record:
                self.identifiers = [
                    f"{record.givenname} {record.surname}",
                    record.nationalid_type,
                    record.nationalid,
                ]


AuditEventSchema.update_forward_refs()
