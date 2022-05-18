import datetime
from typing import Optional

from fastapi_hypermodel import LinkSet, UrlFor
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.schemas.medication import MedicationSchema
from ukrdc_fastapi.schemas.observation import ObservationSchema
from ukrdc_fastapi.schemas.patient import PatientSchema
from ukrdc_fastapi.schemas.survey import SurveySchema

from .base import OrmModel


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


class DocumentSummarySchema(OrmModel):
    id: str
    pid: str
    documenttime: Optional[datetime.datetime]
    documentname: Optional[str]

    filetype: Optional[str]
    filename: Optional[str]

    enteredbydesc: Optional[str]
    enteredatcode: Optional[str]

    links = LinkSet(
        {
            "self": UrlFor("document_get", {"pid": "<pid>", "document_id": "<id>"}),
            "download": UrlFor(
                "document_download", {"pid": "<pid>", "document_id": "<id>"}
            ),
        }
    )


class DocumentSchema(DocumentSummarySchema):
    idx: Optional[int]

    notetext: Optional[str]
    documenttypecode: Optional[str]
    documenttypecodestd: Optional[str]
    documenttypedesc: Optional[str]

    cliniciancode: Optional[str]
    cliniciancodestd: Optional[str]
    cliniciandesc: Optional[str]

    statuscode: Optional[str]
    statuscodestd: Optional[str]
    statusdesc: Optional[str]
    enteredbycode: Optional[str]
    enteredbycodestd: Optional[str]

    enteredatcodestd: Optional[str]
    enteredatdesc: Optional[str]

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


class PatientRecordSummarySchema(OrmModel):
    """Schema for lists of PatientRecords"""

    pid: str
    sendingfacility: str
    sendingextract: str
    localpatientid: str
    ukrdcid: str

    program_memberships: list[ProgramMembershipSchema]
    patient: Optional[PatientSchema]

    repository_creation_date: datetime.datetime
    repository_update_date: datetime.datetime

    links = LinkSet(
        {
            # Self-resources
            "self": UrlFor("patient_get", {"pid": "<pid>"}),
            "related": UrlFor("patient_related", {"pid": "<pid>"}),
            "delete": UrlFor("patient_delete", {"pid": "<pid>"}),
            # Internal resources
            "medications": UrlFor("patient_medications", {"pid": "<pid>"}),
            "treatments": UrlFor("patient_treatments", {"pid": "<pid>"}),
            "surveys": UrlFor("patient_surveys", {"pid": "<pid>"}),
            "documents": UrlFor("patient_documents", {"pid": "<pid>"}),
            # Complex internal resources
            "observations": UrlFor("patient_observations", {"pid": "<pid>"}),
            "observationCodes": UrlFor("patient_observation_codes", {"pid": "<pid>"}),
            "results": UrlFor("patient_resultitems", {"pid": "<pid>"}),
            "resultServices": UrlFor("patient_result_services", {"pid": "<pid>"}),
            "laborders": UrlFor("patient_laborders", {"pid": "<pid>"}),
            # Exports
            "exportPV": UrlFor("patient_export_pv", {"pid": "<pid>"}),
            "exportPVTests": UrlFor("patient_export_pv_tests", {"pid": "<pid>"}),
            "exportPVDocs": UrlFor("patient_export_pv_docs", {"pid": "<pid>"}),
            "exportRADAR": UrlFor("patient_export_radar", {"pid": "<pid>"}),
            "exportPKB": UrlFor("patient_export_pkb", {"pid": "<pid>"}),
        }
    )


class PatientRecordSchema(PatientRecordSummarySchema):
    """Schema for PatientRecord resources"""

    master_id: Optional[int]

    @classmethod
    def from_orm_with_master_record(
        cls, patient_record: PatientRecord, jtrace: Session
    ):
        """
        Find the PatientRecord's nearest matching UKRDC Master Record,
        and inject it's ID into the masterId field before returning
        a validated PatientRecordSchema object.
        """
        record_dict = cls.from_orm(patient_record).dict()
        if not record_dict.get("masterId"):
            master_record = (
                jtrace.query(MasterRecord)
                .filter(
                    MasterRecord.nationalid_type == "UKRDC",
                    MasterRecord.nationalid == record_dict.get("ukrdcid"),
                )
                .first()
            )
            if master_record:
                record_dict["masterId"] = master_record.id
        return cls(**record_dict)


class PatientRecordFullSchema(PatientRecordSummarySchema):
    """Schema for hashing all PatientRecord data"""

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

    patient: Optional[PatientSchema]
