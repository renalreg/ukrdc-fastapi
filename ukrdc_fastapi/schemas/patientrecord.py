import datetime
from typing import List, Optional

from fastapi_hypermodel import LinkSet, UrlFor

from .base import OrmModel
from .patient import PatientSchema


class ProgramMembershipSchema(OrmModel):
    program_name: str
    from_time: Optional[datetime.date]
    to_time: Optional[datetime.date]


class PatientRecordShortSchema(OrmModel):
    pid: str
    sendingfacility: str
    sendingextract: str
    localpatientid: str
    ukrdcid: str
    repository_creation_date: datetime.datetime
    repository_update_date: datetime.datetime

    links = LinkSet(
        {
            "self": UrlFor("patient_record", {"pid": "<pid>"}),
            "laborders": UrlFor("patient_laborders", {"pid": "<pid>"}),
            "observations": UrlFor("patient_observations", {"pid": "<pid>"}),
            "medications": UrlFor("patient_medications", {"pid": "<pid>"}),
            "surveys": UrlFor("patient_surveys", {"pid": "<pid>"}),
            "export-data": UrlFor("patient_export", {"pid": "<pid>"}),
        }
    )


class PatientRecordSchema(PatientRecordShortSchema):
    program_memberships: List[ProgramMembershipSchema]
    patient: PatientSchema
