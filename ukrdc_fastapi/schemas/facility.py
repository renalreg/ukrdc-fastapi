import datetime

from pydantic import Field

from .base import OrmModel


class FacilitySchema(OrmModel):
    """Information about a single facility"""

    id: str = Field(..., description="Facility ID")
    description: str | None = Field(None, description="Facility description")


class FacilityExtractsSchema(OrmModel):
    """Extract counts for a facility"""

    ukrdc: int = Field(..., description="Number of UKRDC extract records")
    pv: int = Field(..., description="Number of PatientView extract records")
    radar: int = Field(..., description="Number of RADAR extract records")
    survey: int = Field(..., description="Number of Survey records")
    pvmig: int = Field(..., description="Number of PatientView migrated records")
    hsmig: int = Field(..., description="Number of HealthShare migrated records")
    ukrr: int = Field(..., description="Number of UKRR extract records")


class FacilityDataFlowSchema(OrmModel):
    """Data flow information for a facility"""

    pkb_in: bool = Field(..., description="PKB data is being received to the UKRDC")
    pkb_out: bool = Field(..., description="UKRDC data is being sent to PKB")
    pkb_message_exclusions: list[str] = Field(
        ..., description="List of message types excluded from PKB sending"
    )


class FacilityStatisticsSchema(OrmModel):
    """Patient count and message status statistics for a facility"""

    # Total number of patients we've ever had on record
    total_patients: int | None = Field(None, description="Total number of patients")

    # Total number of patients receiving messages,
    # whether erroring or not
    patients_receiving_messages: int | None = Field(
        None, description="Number of patients actively receiving messages"
    )

    # Number of patients receiving messages that
    # are most recently succeeding
    patients_receiving_message_success: int | None = Field(
        None,
        description="Number of patients receiving messages that are most recently succeeding",
    )

    # Number of patients receiving messages that
    # are most recently erroring
    patients_receiving_message_error: int | None = Field(
        None,
        description="Number of patients receiving messages that are most recently erroring",
    )


class FacilityDetailsSchema(FacilitySchema):
    """Detailed information about a facility"""

    last_message_received_at: datetime.datetime | None = Field(
        None, description="Timestamp of the last message received"
    )
    statistics: FacilityStatisticsSchema = Field(
        ..., description="Various statistics about the facility"
    )
    data_flow: FacilityDataFlowSchema = Field(
        ..., description="Data flow information about the facility"
    )
