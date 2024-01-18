import datetime
from typing import Optional

from pydantic import Field

from ..base import OrmModel


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
