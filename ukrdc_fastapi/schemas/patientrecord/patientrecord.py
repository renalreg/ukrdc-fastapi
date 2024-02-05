import datetime
from typing import Literal, Optional

from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.schemas.base import OrmModel
from ukrdc_fastapi.schemas.patientrecord.laborder import ResultItemSchema
from ukrdc_fastapi.schemas.patientrecord.medication import MedicationSchema
from ukrdc_fastapi.schemas.patientrecord.observation import ObservationSchema
from ukrdc_fastapi.schemas.patientrecord.patient import PatientSchema
from ukrdc_fastapi.schemas.patientrecord.survey import SurveySchema

SendingExtract = Literal["PV", "UKRDC", "UKRR", "RADAR", "SURVEY", "PVMIG", "HSMIG"]


class ProgramMembershipSchema(OrmModel):
    """A program membership record."""

    program_name: str = Field(..., description="Program name")
    from_time: Optional[datetime.date] = Field(None, description="Program start date")
    to_time: Optional[datetime.date] = Field(None, description="Program end date")


class SocialHistorySchema(OrmModel):
    """A social history record."""

    id: str = Field(..., description="Social history ID")
    pid: str = Field(..., description="Patient ID")


class FamilyHistorySchema(OrmModel):
    """A family history record."""

    id: str = Field(..., description="Family history ID")
    pid: str = Field(..., description="Patient ID")


class AllergySchema(OrmModel):
    """An allergy record."""

    id: str = Field(..., description="Allergy ID")
    pid: str = Field(..., description="Patient ID")


class BaseDiagnosisSchema(OrmModel):
    """Base class for Diagnosis, RenalDiagnosis, and CauseOfDeath"""

    pid: str = Field(..., description="Patient ID")

    creation_date: datetime.datetime = Field(..., description="Database creation date")
    update_date: Optional[datetime.datetime] = Field(
        ..., description="Database update date"
    )

    enteredon: Optional[datetime.datetime] = Field(..., description="Entered date")
    updatedon: Optional[datetime.datetime] = Field(..., description="Updated date")

    diagnosistype: Optional[str] = Field(..., description="Diagnosis type")

    diagnosis_code: Optional[str] = Field(None, description="Diagnosis code")
    diagnosis_code_std: Optional[str] = Field(
        None, description="Diagnosis code standard"
    )
    diagnosis_desc: Optional[str] = Field(None, description="Diagnosis description")

    comments: Optional[str] = Field(None, description="Diagnosis comments")


class DiagnosisSchema(BaseDiagnosisSchema):
    """A diagnosis record."""

    id: str = Field(..., description="Diagnosis ID")

    identification_time: Optional[datetime.datetime] = Field(
        None, description="Diagnosis identification timestamp"
    )
    onset_time: Optional[datetime.datetime] = Field(
        None, description="Diagnosis onset timestamp"
    )


class RenalDiagnosisSchema(BaseDiagnosisSchema):
    """A renal diagnosis record."""

    identification_time: Optional[datetime.datetime] = Field(
        None, description="Diagnosis identification timestamp"
    )
    onset_time: Optional[datetime.datetime] = Field(
        None, description="Diagnosis onset timestamp"
    )


class CauseOfDeathSchema(BaseDiagnosisSchema):
    """A cause of death record."""

    pass


class DialysisSessionSchema(OrmModel):
    id: str = Field(..., description="Session ID")
    pid: str = Field(..., description="Patient ID")

    creation_date: datetime.datetime = Field(..., description="Database creation date")
    update_date: Optional[datetime.datetime] = Field(
        ..., description="Database update date"
    )

    # idx: Currently unused
    externalid: Optional[str] = Field(None, description="External session ID")

    proceduretime: Optional[datetime.datetime] = Field(
        ..., description="Procedure datetime"
    )

    # Procedure type
    proceduretypecode: Optional[str] = Field(None, description="Procedure code")
    proceduretypecodestd: Optional[str] = Field(
        None, description="Procedure code standard"
    )
    proceduretypedesc: Optional[str] = Field(None, description="Procedure description")

    # Clinician
    cliniciancode: Optional[str] = Field(
        None, description="Clinicial code. Rarely used."
    )
    cliniciancodestd: Optional[str] = Field(
        None, description="Clinicial code standard. Rarely used."
    )
    cliniciandesc: Optional[str] = Field(None, description="Clinician description")

    # Data-entry user
    enteredbycode: Optional[str] = Field(
        None, description="Data-entry user code. Usually a local username or ID."
    )
    enteredbycodestd: Optional[str] = Field(
        None, description="Data-entry user code standard. Usually local."
    )
    enteredbydesc: Optional[str] = Field(
        None, description="Data-entry user description"
    )

    # Data entry site/unit
    enteredatcode: Optional[str] = Field(
        None,
        description="Site code at which the data was entered. Usually an RR1+ code.",
    )
    enteredatcodestd: Optional[str] = Field(
        None, description="Site code standard at which the data was entered."
    )
    enteredatdesc: Optional[str] = Field(
        None, description="Site description at which the data was entered."
    )

    # Session data
    qhd19: Optional[str]
    qhd20: Optional[str]
    qhd21: Optional[str]
    qhd22: Optional[str]
    qhd30: Optional[str]
    qhd31: Optional[str]
    qhd32: Optional[str]
    qhd33: Optional[str]

    # updatedon: Currently unused
    # actioncode: Currently unused


class ProcedureSchema(OrmModel):
    """A procedure record."""

    id: str = Field(..., description="Procedure ID")
    pid: str = Field(..., description="Patient ID")


class DocumentSummarySchema(OrmModel):
    """Summary of a patient document."""

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
    """A patient document."""

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
    """An encounter event."""

    id: str = Field(..., description="Encounter ID")
    pid: str = Field(..., description="Patient ID")
    from_time: Optional[datetime.datetime] = Field(None, description="Encounter start")
    to_time: Optional[datetime.datetime] = Field(None, description="Encounter end")


class ClinicalRelationshipSchema(OrmModel):
    """A clinical relationship record."""

    id: str = Field(..., description="Clinical relationship ID")
    pid: str = Field(..., description="Patient ID")


class PVDataSchema(OrmModel):
    """
    PV Data, including RRT status and blood group
    """

    creation_date: datetime.datetime = Field(..., description="Creation date")
    update_date: Optional[datetime.datetime] = Field(None, description="Update date")

    rrtstatus: Optional[str] = Field(None, description="RRT status code")
    tpstatus: Optional[str] = Field(None, description="Transplant status")
    bloodgroup: Optional[str] = Field(None, description="Blood group")

    diagnosisdate: Optional[datetime.datetime] = Field(
        None, description="Diagnosis date"
    )


class PVDeleteSchema(OrmModel):
    """A PV delete record. These are only used internally for passing deletions to PatientView."""

    did: int = Field(..., description="Delete ID")
    pid: str = Field(..., description="Patient ID")
    observation_time: Optional[datetime.datetime] = Field(
        None, description="Observation timestamp"
    )
    service_id: Optional[str] = Field(None, description="Service ID")


class PatientRecordSummarySchema(OrmModel):
    """A patient record summary."""

    pid: str = Field(..., description="Patient ID")
    sendingfacility: str = Field(..., description="Sending facility")
    sendingextract: SendingExtract = Field(..., description="Sending extract")
    localpatientid: str = Field(..., description="Local patient ID")
    ukrdcid: str = Field(..., description="UKRDC ID")

    pvdata: Optional[PVDataSchema] = Field(None, description="PV Data")

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
    """A patient record."""

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
        record_dict = cls.from_orm(patient_record).dict()  # type: ignore  # mypy bug, see https://github.com/pydantic/pydantic/issues/5187
        if not record_dict.get("masterId"):
            stmt_master_record = select(MasterRecord).where(
                MasterRecord.nationalid_type == "UKRDC",
                MasterRecord.nationalid == record_dict.get("ukrdcid"),
            )
            master_record = jtrace.scalars(stmt_master_record).first()

            if master_record:
                record_dict["masterId"] = master_record.id
        return cls(**record_dict)


class PatientRecordFullSchema(PatientRecordSummarySchema):
    """A patient record with all related data."""

    social_histories: list[SocialHistorySchema] = Field(
        [], description="Social histories"
    )
    family_histories: list[FamilyHistorySchema] = Field(
        [], description="Family histories"
    )
    observations: list[ObservationSchema] = Field(..., description="Observations")
    result_items: list[ResultItemSchema] = Field(..., description="Result Items")
    allergies: list[AllergySchema] = Field(..., description="Allergies")
    diagnoses: list[DiagnosisSchema] = Field(..., description="Diagnoses")
    renaldiagnoses: list[RenalDiagnosisSchema] = Field(
        ..., description="Renal diagnoses"
    )
    medications: list[MedicationSchema] = Field(..., description="Medications")
    procedures: list[ProcedureSchema] = Field(..., description="Procedures")
    documents: list[DocumentSchema] = Field(..., description="Documents")
    encounters: list[EncounterSchema] = Field(..., description="Encounters")
    program_memberships: list[ProgramMembershipSchema] = Field(
        ..., description="Program memberships"
    )
    clinical_relationships: list[ClinicalRelationshipSchema] = Field(
        ..., description="Clinical relationships"
    )
    surveys: list[SurveySchema] = Field(..., description="Surveys")
    pvdelete: list[PVDeleteSchema] = Field(..., description="PV Deletes")

    patient: Optional[PatientSchema] = Field(None, description="Patient")
