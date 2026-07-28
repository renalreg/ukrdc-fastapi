import datetime
from typing import Optional

from pydantic import Field

from ukrdc_fastapi.schemas.base import OrmModel


class ProcedureSchema(OrmModel):
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
    cliniciancode: str | None = Field(None, description="Clinicial code. Rarely used.")
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
    enteredbydesc: str | None = Field(None, description="Data-entry user description")

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

    # updatedon: Currently unused
    # actioncode: Currently unused


class DialysisSessionSchema(ProcedureSchema):
    # Session data
    qhd19: str | None = None
    qhd20: str | None = None
    qhd21: str | None = None
    qhd22: str | None = None
    qhd30: str | None = None
    qhd31: str | None = None
    qhd32: str | None = None
    qhd33: str | None = None


class TransplantSchema(ProcedureSchema):
    tra64: datetime.datetime | None = None
    tra65: str | None = None
    tra66: str | None = None
    tra69: datetime.datetime | None = None
    tra76: str | None = None
    tra77: str | None = None
    tra78: str | None = None
    tra79: str | None = None
    tra80: str | None = None
    tra8a: str | None = None
    tra81: str | None = None
    tra82: str | None = None
    tra83: str | None = None
    tra84: str | None = None
    tra85: str | None = None
    tra86: str | None = None
    tra87: str | None = None
    tra88: str | None = None
    tra89: str | None = None
    tra90: str | None = None
    tra91: str | None = None
    tra92: str | None = None
    tra93: str | None = None
    tra94: str | None = None
    tra95: str | None = None
    tra96: str | None = None
    tra97: str | None = None
    tra98: str | None = None
