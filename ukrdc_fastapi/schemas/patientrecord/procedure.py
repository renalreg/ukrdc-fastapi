import datetime
from typing import Optional

from pydantic import Field

from ukrdc_fastapi.schemas.base import OrmModel


class ProcedureSchema(OrmModel):
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

    # updatedon: Currently unused
    # actioncode: Currently unused


class DialysisSessionSchema(ProcedureSchema):
    # Session data
    qhd19: Optional[str]
    qhd20: Optional[str]
    qhd21: Optional[str]
    qhd22: Optional[str]
    qhd30: Optional[str]
    qhd31: Optional[str]
    qhd32: Optional[str]
    qhd33: Optional[str]


class TransplantSchema(ProcedureSchema):
    tra64: Optional[datetime.datetime]
    tra65: Optional[str]
    tra66: Optional[str]
    tra69: Optional[datetime.datetime]
    tra76: Optional[str]
    tra77: Optional[str]
    tra78: Optional[str]
    tra79: Optional[str]
    tra80: Optional[str]
    tra8a: Optional[str]
    tra81: Optional[str]
    tra82: Optional[str]
    tra83: Optional[str]
    tra84: Optional[str]
    tra85: Optional[str]
    tra86: Optional[str]
    tra87: Optional[str]
    tra88: Optional[str]
    tra89: Optional[str]
    tra90: Optional[str]
    tra91: Optional[str]
    tra92: Optional[str]
    tra93: Optional[str]
    tra94: Optional[str]
    tra95: Optional[str]
    tra96: Optional[str]
    tra97: Optional[str]
    tra98: Optional[str]
