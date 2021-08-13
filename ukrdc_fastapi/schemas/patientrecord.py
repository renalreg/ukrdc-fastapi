import datetime
from typing import Optional

from fastapi_hypermodel import LinkSet, UrlFor

from ukrdc_fastapi.schemas.medication import MedicationSchema
from ukrdc_fastapi.schemas.observation import ObservationSchema
from ukrdc_fastapi.schemas.patient import PatientSchema
from ukrdc_fastapi.schemas.survey import SurveySchema

from .base import OrmModel
from .patient import PatientFullSchema, PatientSchema


class ProgramMembershipSchema(OrmModel):
    program_name: str
    from_time: Optional[datetime.date]
    to_time: Optional[datetime.date]


class SocialHistorySchema(OrmModel):
    id: str
    pid: str


class FamilyHistorySchema(OrmModel):
    id: str
    pid: str


class AllergySchema(OrmModel):
    id: str
    pid: str


class DiagnosisSchema(OrmModel):
    id: str
    pid: str

    diagnosis_code: Optional[str]
    diagnosis_code_std: Optional[str]
    diagnosis_desc: Optional[str]

    identification_time: Optional[datetime.datetime]
    onset_time: Optional[datetime.datetime]

    comments: Optional[str]


class RenalDiagnosisSchema(OrmModel):
    pid: str

    diagnosis_code: Optional[str]
    diagnosis_code_std: Optional[str]
    diagnosis_desc: Optional[str]

    identification_time: Optional[datetime.datetime]

    comments: Optional[str]


class ProcedureSchema(OrmModel):
    id: str
    pid: str


class DocumentSchema(OrmModel):
    id: str
    pid: str
    idx: Optional[int]
    documenttime: Optional[datetime.datetime]
    notetext: Optional[str]
    documenttypecode: Optional[str]
    documenttypecodestd: Optional[str]
    documenttypedesc: Optional[str]

    cliniciancode: Optional[str]
    cliniciancodestd: Optional[str]
    cliniciandesc: Optional[str]
    documentname: Optional[str]
    statuscode: Optional[str]
    statuscodestd: Optional[str]
    statusdesc: Optional[str]
    enteredbycode: Optional[str]
    enteredbycodestd: Optional[str]
    enteredbydesc: Optional[str]
    enteredatcode: Optional[str]
    enteredatcodestd: Optional[str]
    enteredatdesc: Optional[str]
    filetype: Optional[str]
    filename: Optional[str]

    documenturl: Optional[str]
    updatedon: Optional[datetime.datetime]
    actioncode: Optional[str]
    externalid: Optional[str]

    update_date: Optional[datetime.datetime]
    creation_date: Optional[datetime.datetime]

    repository_update_date: Optional[datetime.datetime]


class EncounterSchema(OrmModel):
    id: str
    pid: str
    from_time: Optional[datetime.datetime]
    to_time: Optional[datetime.datetime]


class ClinicalRelationshipSchema(OrmModel):
    id: str
    pid: str


class PVDeleteSchema(OrmModel):
    did: int
    pid: str
    observation_time: Optional[datetime.datetime]
    service_id: Optional[str]


class PatientRecordSchema(OrmModel):
    pid: str
    sendingfacility: str
    sendingextract: str
    localpatientid: str
    ukrdcid: str
    repository_creation_date: datetime.datetime
    repository_update_date: datetime.datetime

    program_memberships: list[ProgramMembershipSchema]
    patient: Optional[PatientSchema]

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


class PatientRecordFullSchema(PatientRecordSchema):
    social_histories: list[SocialHistorySchema]
    family_histories: list[FamilyHistorySchema]
    observations: list[ObservationSchema]
    allergies: list[AllergySchema]
    diagnoses: list[DiagnosisSchema]
    renaldiagnoses: list[RenalDiagnosisSchema]
    medications: list[MedicationSchema]
    procedures: list[ProcedureSchema]
    documents: list[DocumentSchema]
    encounters: list[EncounterSchema]
    program_memberships: list[ProgramMembershipSchema]
    clinical_relationships: list[ClinicalRelationshipSchema]
    surveys: list[SurveySchema]
    pvdelete: list[PVDeleteSchema]

    patient: Optional[PatientFullSchema]
