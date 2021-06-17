import datetime
from typing import Optional

from fastapi_hypermodel import LinkSet, UrlFor

from .base import OrmModel
from .patient import PatientSchema


class ProgramMembershipSchema(OrmModel):
    program_name: str
    from_time: Optional[datetime.date]
    to_time: Optional[datetime.date]


class PatientRecordSchema(OrmModel):
    pid: str
    sendingfacility: str
    sendingextract: str
    localpatientid: str
    ukrdcid: str
    repository_creation_date: datetime.datetime
    repository_update_date: datetime.datetime

    program_memberships: list[ProgramMembershipSchema]
    patient: PatientSchema

    links = LinkSet(
        {
            "self": UrlFor("patient_record", {"pid": "<pid>"}),
            "laborders": UrlFor("patient_laborders", {"pid": "<pid>"}),
            "results": UrlFor("patient_resultitems", {"pid": "<pid>"}),
            "observations": UrlFor("patient_observations", {"pid": "<pid>"}),
            "medications": UrlFor("patient_medications", {"pid": "<pid>"}),
            "surveys": UrlFor("patient_surveys", {"pid": "<pid>"}),
            "exportPV": UrlFor("patient_export_pv", {"pid": "<pid>"}),
            "exportPVTests": UrlFor("patient_export_pv_tests", {"pid": "<pid>"}),
            "exportPVDocs": UrlFor("patient_export_pv_docs", {"pid": "<pid>"}),
            "exportRADAR": UrlFor("patient_export_radar", {"pid": "<pid>"}),
        }
    )
