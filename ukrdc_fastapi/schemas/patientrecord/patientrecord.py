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
    from_time: datetime.date | None = Field(None, description="Program start date")
    to_time: datetime.date | None = Field(None, description="Program end date")


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
    update_date: datetime.datetime | None = Field(
        ..., description="Database update date"
    )

    enteredon: datetime.datetime | None = Field(..., description="Entered date")
    updatedon: datetime.datetime | None = Field(..., description="Updated date")

    diagnosistype: str | None = Field(..., description="Diagnosis type")

    diagnosis_code: str | None = Field(None, description="Diagnosis code")
    diagnosis_code_std: str | None = Field(
        None, description="Diagnosis code standard"
    )
    diagnosis_desc: str | None = Field(None, description="Diagnosis description")

    comments: str | None = Field(None, description="Diagnosis comments")


class DiagnosisSchema(BaseDiagnosisSchema):
    """A diagnosis record."""

    id: str = Field(..., description="Diagnosis ID")

    identification_time: datetime.datetime | None = Field(
        None, description="Diagnosis identification timestamp"
    )
    onset_time: datetime.datetime | None = Field(
        None, description="Diagnosis onset timestamp"
    )


class RenalDiagnosisSchema(BaseDiagnosisSchema):
    """A renal diagnosis record."""

    identification_time: datetime.datetime | None = Field(
        None, description="Diagnosis identification timestamp"
    )
    onset_time: datetime.datetime | None = Field(
        None, description="Diagnosis onset timestamp"
    )


class CauseOfDeathSchema(BaseDiagnosisSchema):
    """A cause of death record."""

    pass


class DialysisSessionSchema(OrmModel):
    id: str = Field(..., description="Session ID")
    pid: str = Field(..., description="Patient ID")

    creation_date: datetime.datetime = Field(..., description="Database creation date")
    update_date: datetime.datetime | None = Field(
        ..., description="Database update date"
    )

    # idx: Currently unused
    externalid: str | None = Field(None, description="External session ID")

    proceduretime: datetime.datetime | None = Field(
        ..., description="Procedure datetime"
    )

    # Procedure type
    proceduretypecode: str | None = Field(None, description="Procedure code")
    proceduretypecodestd: str | None = Field(
        None, description="Procedure code standard"
    )
    proceduretypedesc: str | None = Field(None, description="Procedure description")

    # Clinician
    cliniciancode: str | None = Field(
        None, description="Clinicial code. Rarely used."
    )
    cliniciancodestd: str | None = Field(
        None, description="Clinicial code standard. Rarely used."
    )
    cliniciandesc: str | None = Field(None, description="Clinician description")

    # Data-entry user
    enteredbycode: str | None = Field(
        None, description="Data-entry user code. Usually a local username or ID."
    )
    enteredbycodestd: str | None = Field(
        None, description="Data-entry user code standard. Usually local."
    )
    enteredbydesc: str | None = Field(
        None, description="Data-entry user description"
    )

    # Data entry site/unit
    enteredatcode: str | None = Field(
        None,
        description="Site code at which the data was entered. Usually an RR1+ code.",
    )
    enteredatcodestd: str | None = Field(
        None, description="Site code standard at which the data was entered."
    )
    enteredatdesc: str | None = Field(
        None, description="Site description at which the data was entered."
    )

    # Session data
    qhd19: str | None = None
    qhd20: str | None = None
    qhd21: str | None = None
    qhd22: str | None = None
    qhd30: str | None = None
    qhd31: str | None = None
    qhd32: str | None = None
    qhd33: str | None = None

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
    documenttime: datetime.datetime | None = Field(
        None, description="Document created time"
    )
    documentname: str | None = Field(None, description="Document name")

    filetype: str | None = Field(None, description="Document file type")
    filename: str | None = Field(None, description="Document file name")

    enteredbydesc: str | None = Field(
        None, description="Document author description"
    )
    enteredatcode: str | None = Field(None, description="Document organisation code")


class DocumentSchema(DocumentSummarySchema):
    """A patient document."""

    idx: int | None = Field(None, description="Document index")

    notetext: str | None = Field(None, description="Document note text")
    documenttypecode: str | None = Field(None, description="Document type code")
    documenttypecodestd: str | None = Field(
        None, description="Document type code standard"
    )
    documenttypedesc: str | None = Field(
        None, description="Document type description"
    )

    cliniciancode: str | None = Field(
        None, description="Document author clinician code"
    )
    cliniciancodestd: str | None = Field(
        None, description="Document author clinician code standard"
    )
    cliniciandesc: str | None = Field(
        None, description="Document author clinician description"
    )

    statuscode: str | None = Field(None, description="Document status code")
    statuscodestd: str | None = Field(
        None, description="Document status code standard"
    )
    statusdesc: str | None = Field(None, description="Document status description")

    enteredbycode: str | None = Field(None, description="Document author code")
    enteredbycodestd: str | None = Field(
        None, description="Document author code standard"
    )

    enteredatcodestd: str | None = Field(
        None, description="Document organisation code standard"
    )
    enteredatdesc: str | None = Field(
        None, description="Document organisation description"
    )

    documenturl: str | None = Field(None, description="Document URL")
    updatedon: datetime.datetime | None = Field(
        None, description="Document updated timestamp"
    )
    actioncode: str | None = Field(None, description="Document action code")
    externalid: str | None = Field(None, description="Document external ID")

    update_date: datetime.datetime | None = Field(
        None, description="Document updated timestamp"
    )
    creation_date: datetime.datetime | None = Field(
        None, description="Document created timestamp"
    )

    repository_update_date: datetime.datetime | None = Field(
        None, description="Document repository updated timestamp"
    )


class EncounterSchema(OrmModel):
    """An encounter event."""

    id: str = Field(..., description="Encounter ID")
    pid: str = Field(..., description="Patient ID")
    from_time: datetime.datetime | None = Field(None, description="Encounter start")
    to_time: datetime.datetime | None = Field(None, description="Encounter end")


class ClinicalRelationshipSchema(OrmModel):
    """A clinical relationship record."""

    id: str = Field(..., description="Clinical relationship ID")
    pid: str = Field(..., description="Patient ID")


class PVDataSchema(OrmModel):
    """
    PV Data, including RRT status and blood group
    """

    creation_date: datetime.datetime = Field(..., description="Creation date")
    update_date: datetime.datetime | None = Field(None, description="Update date")

    rrtstatus: str | None = Field(None, description="RRT status code")
    tpstatus: str | None = Field(None, description="Transplant status")
    bloodgroup: str | None = Field(None, description="Blood group")

    diagnosisdate: datetime.datetime | None = Field(
        None, description="Diagnosis date"
    )


class PVDeleteSchema(OrmModel):
    """A PV delete record. These are only used internally for passing deletions to PatientView."""

    did: int = Field(..., description="Delete ID")
    pid: str = Field(..., description="Patient ID")
    observation_time: datetime.datetime | None = Field(
        None, description="Observation timestamp"
    )
    service_id: str | None = Field(None, description="Service ID")


class PatientRecordSummarySchema(OrmModel):
    """A patient record summary."""

    pid: str = Field(..., description="Patient ID")
    sendingfacility: str = Field(..., description="Sending facility")
    sendingextract: SendingExtract = Field(..., description="Sending extract")
    localpatientid: str = Field(..., description="Local patient ID")
    ukrdcid: str = Field(..., description="UKRDC ID")

    pvdata: PVDataSchema | None = Field(None, description="PV Data")

    program_memberships: list[ProgramMembershipSchema] = Field(
        [], description="Program memberships"
    )
    patient: PatientSchema | None = Field(None, description="Patient")

    repository_creation_date: datetime.datetime = Field(
        ..., description="Repository creation timestamp"
    )
    repository_update_date: datetime.datetime = Field(
        ..., description="Repository update timestamp"
    )


class PatientRecordSchema(PatientRecordSummarySchema):
    """A patient record."""

    master_id: int | None = Field(None, description="Master record ID")

    @classmethod
    def from_orm_with_master_record(
        cls, patient_record: PatientRecord, jtrace: Session
    ):
        """
        Find the PatientRecord's nearest matching UKRDC Master Record,
        and inject it's ID into the masterId field before returning
        a validated PatientRecordSchema object.
        """
        record_dict = cls.model_validate(patient_record).model_dump()  # type: ignore  # mypy bug, see https://github.com/pydantic/pydantic/issues/5187
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

    patient: PatientSchema | None = Field(None, description="Patient")
