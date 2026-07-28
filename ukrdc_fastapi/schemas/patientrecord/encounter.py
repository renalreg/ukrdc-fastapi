import datetime
from typing import Optional

from pydantic import Field

from ..base import OrmModel


class EncounterSchema(OrmModel):
    """An encounter record"""

    id: str = Field(..., description="Treatment ID")
    pid: str = Field(..., description="Patient ID")

    creation_date: datetime.datetime = Field(..., description="Database creation date")
    update_date: datetime.datetime | None = Field(
        ..., description="Database update date"
    )
    # idx: Currently unused
    externalid: str | None = Field(None, description="External session ID")

    # Encounter time
    fromtime: datetime.date | None = Field(None, description="Encounter start date")
    totime: datetime.date | None = Field(None, description="Encounter end date")

    # Encounter information
    encounternumber: str | None = Field(None, description="Encounter number")
    encountertype: str | None = Field(None, description="Encounter type")

    # Clinician
    admittingcliniciancode: str | None = Field(
        None, description="Clinicial code. Rarely used."
    )
    admittingcliniciancodestd: str | None = Field(
        None, description="Clinicial code standard. Rarely used."
    )
    admittingcliniciandesc: str | None = Field(
        None, description="Clinician description"
    )

    # Admit reason
    admitreasoncode: str | None = Field(None, description="Admission reason code")
    admitreasoncodestd: str | None = Field(
        None, description="Admission reason code standard"
    )
    admitreasondesc: str | None = Field(
        None, description="Admission reason description"
    )

    # Admission source
    admissionsourcecode: str | None = Field(
        None, description="Admission source code"
    )
    admissionsourcecodestd: str | None = Field(
        None, description="Admission source code standard"
    )
    admissionsourcedesc: str | None = Field(
        None, description="Admission source description"
    )

    # Discharge reason
    dischargereasoncode: str | None = Field(
        None, description="Discharge reason code"
    )
    dischargereasoncodestd: str | None = Field(
        None, description="Discharge reason code standard"
    )
    dischargereasondesc: str | None = Field(
        None, description="Discharge reason description"
    )

    # Discharge location
    dischargelocationcode: str | None = Field(
        None, description="Discharge location code"
    )
    dischargelocationcodestd: str | None = Field(
        None, description="Discharge location code standard"
    )
    dischargelocationdesc: str | None = Field(
        None, description="Discharge location description"
    )

    # Health care facility
    healthcarefacilitycode: str | None = Field(
        None, description="Health care facility code"
    )
    healthcarefacilitycodestd: str | None = Field(
        None, description="Health care facility code standard"
    )
    healthcarefacilitydesc: str | None = Field(
        None, description="Health care facility description"
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

    visitdescription: str | None = Field(None, description="Visit description")

    # updatedon: Currently unused
    # actioncode: Currently unused
