import datetime
from typing import Literal, Optional

from pydantic import Field
from sqlalchemy.orm.session import Session
from ukrdc_sqla.empi import MasterRecord
from ukrdc_sqla.ukrdc import PatientRecord

from ukrdc_fastapi.schemas.base import OrmModel

from .diagnosis import CauseOfDeathSchema, DiagnosisSchema, RenalDiagnosisSchema
from .documents import DocumentSchema
from .encounter import EncounterSchema
from .laborder import ResultItemSchema
from .medication import MedicationSchema
from .observation import ObservationSchema
from .patient import PatientSchema
from .procedure import DialysisSessionSchema, ProcedureSchema, TransplantSchema
from .survey import SurveySchema
from .treatments import TreatmentSchema

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
    rrtstatus_desc: Optional[str] = Field(None, description="RRT status")

    tpstatus: Optional[str] = Field(None, description="Transplant status code")
    tpstatus_desc: Optional[str] = Field(None, description="Transplant status")

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

    # Diagnoses
    diagnoses: list[DiagnosisSchema] = Field(..., description="Diagnoses")
    renaldiagnoses: list[RenalDiagnosisSchema] = Field(
        ..., description="Renal diagnoses"
    )
    cause_of_death: list[CauseOfDeathSchema] = Field(
        ..., description="Cause of death diagnoses"
    )

    medications: list[MedicationSchema] = Field(..., description="Medications")

    # Procedures
    procedures: list[ProcedureSchema] = Field(..., description="Procedures")
    dialysis_sessions: list[DialysisSessionSchema] = Field(
        ..., description="Dialysis Sessions"
    )
    transplants: list[TransplantSchema] = Field(..., description="Transplants")

    # Treatments
    encounters: list[EncounterSchema] = Field(..., description="Encounters")
    treatments: list[TreatmentSchema] = Field(..., description="Treatments")

    documents: list[DocumentSchema] = Field(..., description="Documents")
    program_memberships: list[ProgramMembershipSchema] = Field(
        ..., description="Program memberships"
    )
    clinical_relationships: list[ClinicalRelationshipSchema] = Field(
        ..., description="Clinical relationships"
    )
    surveys: list[SurveySchema] = Field(..., description="Surveys")
    pvdelete: list[PVDeleteSchema] = Field(..., description="PV Deletes")

    patient: Optional[PatientSchema] = Field(None, description="Patient")
