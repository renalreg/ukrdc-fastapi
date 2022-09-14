import datetime
from typing import Literal, Optional

from pydantic import Field
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.schemas.medication import MedicationSchema
from ukrdc_fastapi.schemas.observation import ObservationSchema
from ukrdc_fastapi.schemas.patient import PatientSchema
from ukrdc_fastapi.schemas.survey import SurveySchema

from .base import OrmModel

SendingExtract = Literal["PV", "UKRDC", "UKRR", "RADAR", "SURVEY", "PVMIG", "HSMIG"]


class ProgramMembershipSchema(OrmModel):
    program_name: str = Field(..., description="Program name")
    from_time: Optional[datetime.date] = Field(None, description="Program start date")
    to_time: Optional[datetime.date] = Field(None, description="Program end date")


class SocialHistorySchema(OrmModel):
    id: str = Field(..., description="Social history ID")
    pid: str = Field(..., description="Patient ID")


class FamilyHistorySchema(OrmModel):
    id: str = Field(..., description="Family history ID")
    pid: str = Field(..., description="Patient ID")


class AllergySchema(OrmModel):
    id: str = Field(..., description="Allergy ID")
    pid: str = Field(..., description="Patient ID")


class DiagnosisSchema(OrmModel):
    id: str = Field(..., description="Diagnosis ID")
    pid: str = Field(..., description="Patient ID")

    diagnosis_code: Optional[str] = Field(None, description="Diagnosis code")
    diagnosis_code_std: Optional[str] = Field(
        None, description="Diagnosis code standard"
    )
    diagnosis_desc: Optional[str] = Field(None, description="Diagnosis description")

    identification_time: Optional[datetime.datetime] = Field(
        None, description="Diagnosis identification timestamp"
    )
    onset_time: Optional[datetime.datetime] = Field(
        None, description="Diagnosis onset timestamp"
    )

    comments: Optional[str] = Field(None, description="Diagnosis comments")


class RenalDiagnosisSchema(OrmModel):
    pid: str = Field(..., description="Patient ID")

    diagnosis_code: Optional[str] = Field(None, description="Diagnosis code")
    diagnosis_code_std: Optional[str] = Field(
        None, description="Diagnosis code standard"
    )
    diagnosis_desc: Optional[str] = Field(None, description="Diagnosis description")

    identification_time: Optional[datetime.datetime] = Field(
        None, description="Diagnosis identification timestamp"
    )

    comments: Optional[str] = Field(None, description="Diagnosis comments")


class ProcedureSchema(OrmModel):
    id: str = Field(..., description="Procedure ID")
    pid: str = Field(..., description="Patient ID")


class DocumentSummarySchema(OrmModel):
    id: str = Field(..., description="Document ID")
    pid: str = Field(..., description="Patient ID")
    documenttime: Optional[datetime.datetime] = Field(
        None, description="Document created time"
    )
    documentname: Optional[str] = Field(None, description="Document name")

    filetype: Optional[str] = Field(None, description="Document file type")
    filename: Optional[str] = Field(None, description="Document file name")

    enteredbydesc: Optional[str] = Field(
        None, description="Document author description"
    )
    enteredatcode: Optional[str] = Field(None, description="Document organisation code")


class DocumentSchema(DocumentSummarySchema):
    idx: Optional[int] = Field(None, description="Document index")

    notetext: Optional[str] = Field(None, description="Document note text")
    documenttypecode: Optional[str] = Field(None, description="Document type code")
    documenttypecodestd: Optional[str] = Field(
        None, description="Document type code standard"
    )
    documenttypedesc: Optional[str] = Field(
        None, description="Document type description"
    )

    cliniciancode: Optional[str] = Field(
        None, description="Document author clinician code"
    )
    cliniciancodestd: Optional[str] = Field(
        None, description="Document author clinician code standard"
    )
    cliniciandesc: Optional[str] = Field(
        None, description="Document author clinician description"
    )

    statuscode: Optional[str] = Field(None, description="Document status code")
    statuscodestd: Optional[str] = Field(
        None, description="Document status code standard"
    )
    statusdesc: Optional[str] = Field(None, description="Document status description")

    enteredbycode: Optional[str] = Field(None, description="Document author code")
    enteredbycodestd: Optional[str] = Field(
        None, description="Document author code standard"
    )

    enteredatcodestd: Optional[str] = Field(
        None, description="Document organisation code standard"
    )
    enteredatdesc: Optional[str] = Field(
        None, description="Document organisation description"
    )

    documenturl: Optional[str] = Field(None, description="Document URL")
    updatedon: Optional[datetime.datetime] = Field(
        None, description="Document updated timestamp"
    )
    actioncode: Optional[str] = Field(None, description="Document action code")
    externalid: Optional[str] = Field(None, description="Document external ID")

    update_date: Optional[datetime.datetime] = Field(
        None, description="Document updated timestamp"
    )
    creation_date: Optional[datetime.datetime] = Field(
        None, description="Document created timestamp"
    )

    repository_update_date: Optional[datetime.datetime] = Field(
        None, description="Document repository updated timestamp"
    )


class EncounterSchema(OrmModel):
    id: str = Field(..., description="Encounter ID")
    pid: str = Field(..., description="Patient ID")
    from_time: Optional[datetime.datetime] = Field(None, description="Encounter start")
    to_time: Optional[datetime.datetime] = Field(None, description="Encounter end")


class ClinicalRelationshipSchema(OrmModel):
    id: str = Field(..., description="Clinical relationship ID")
    pid: str = Field(..., description="Patient ID")


class PVDeleteSchema(OrmModel):
    did: int = Field(..., description="Delete ID")
    pid: str = Field(..., description="Patient ID")
    observation_time: Optional[datetime.datetime] = Field(
        None, description="Observation timestamp"
    )
    service_id: Optional[str] = Field(None, description="Service ID")


class PatientRecordSummarySchema(OrmModel):
    """Schema for lists of PatientRecords"""

    pid: str = Field(..., description="Patient ID")
    sendingfacility: str = Field(..., description="Sending facility")
    sendingextract: SendingExtract = Field(..., description="Sending extract")
    localpatientid: str = Field(..., description="Local patient ID")
    ukrdcid: str = Field(..., description="UKRDC ID")

    program_memberships: list[ProgramMembershipSchema] = Field(
        [], description="Program memberships"
    )
    patient: Optional[PatientSchema] = Field(None, description="Patient")

    repository_creation_date: datetime.datetime = Field(
        ..., description="Repository creation timestamp"
    )
    repository_update_date: datetime.datetime = Field(
        ..., description="Repository update timestamp"
    )


class PatientRecordSchema(PatientRecordSummarySchema):
    """Schema for PatientRecord resources"""

    master_id: Optional[int] = Field(None, description="Master record ID")

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

    social_histories: list[SocialHistorySchema] = Field(
        [], description="Social histories"
    )
    family_histories: list[FamilyHistorySchema] = Field(
        [], description="Family histories"
    )
    observations: list[ObservationSchema] = Field([], description="Observations")
    allergies: list[AllergySchema] = Field([], description="Allergies")
    diagnoses: list[DiagnosisSchema] = Field([], description="Diagnoses")
    renaldiagnoses: list[RenalDiagnosisSchema] = Field(
        [], description="Renal diagnoses"
    )
    medications: list[MedicationSchema] = Field([], description="Medications")
    procedures: list[ProcedureSchema] = Field([], description="Procedures")
    documents: list[DocumentSchema] = Field([], description="Documents")
    encounters: list[EncounterSchema] = Field([], description="Encounters")
    program_memberships: list[ProgramMembershipSchema] = Field(
        [], description="Program memberships"
    )
    clinical_relationships: list[ClinicalRelationshipSchema] = Field(
        [], description="Clinical relationships"
    )
    surveys: list[SurveySchema] = Field([], description="Surveys")
    pvdelete: list[PVDeleteSchema] = Field([], description="PV Deletes")

    patient: Optional[PatientSchema] = Field(None, description="Patient")
