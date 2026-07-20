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
    qhd19: Optional[str] = None
    qhd20: Optional[str] = None
    qhd21: Optional[str] = None
    qhd22: Optional[str] = None
    qhd30: Optional[str] = None
    qhd31: Optional[str] = None
    qhd32: Optional[str] = None
    qhd33: Optional[str] = None


class TransplantSchema(ProcedureSchema):
    tra64: Optional[datetime.datetime] = None
    tra65: Optional[str] = None
    tra66: Optional[str] = None
    tra69: Optional[datetime.datetime] = None
    tra76: Optional[str] = None
    tra77: Optional[str] = None
    tra78: Optional[str] = None
    tra79: Optional[str] = None
    tra80: Optional[str] = None
    tra8a: Optional[str] = None
    tra81: Optional[str] = None
    tra82: Optional[str] = None
    tra83: Optional[str] = None
    tra84: Optional[str] = None
    tra85: Optional[str] = None
    tra86: Optional[str] = None
    tra87: Optional[str] = None
    tra88: Optional[str] = None
    tra89: Optional[str] = None
    tra90: Optional[str] = None
    tra91: Optional[str] = None
    tra92: Optional[str] = None
    tra93: Optional[str] = None
    tra94: Optional[str] = None
    tra95: Optional[str] = None
    tra96: Optional[str] = None
    tra97: Optional[str] = None
    tra98: Optional[str] = None
