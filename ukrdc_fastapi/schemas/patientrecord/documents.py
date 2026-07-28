import datetime
from typing import Optional

from pydantic import Field

from ..base import OrmModel


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

    enteredbydesc: str | None = Field(None, description="Document author description")
    enteredatcode: str | None = Field(None, description="Document organisation code")


class DocumentSchema(DocumentSummarySchema):
    """A patient document."""

    idx: int | None = Field(None, description="Document index")

    notetext: str | None = Field(None, description="Document note text")

    documenttypecode: str | None = Field(None, description="Document type code")
    documenttypecodestd: str | None = Field(
        None, description="Document type code standard"
    )
    documenttypedesc: str | None = Field(None, description="Document type description")

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
    statuscodestd: str | None = Field(None, description="Document status code standard")
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
