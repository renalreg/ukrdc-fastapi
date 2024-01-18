import datetime
from typing import Optional

from pydantic import Field

from ..base import OrmModel


class EncounterSchema(OrmModel):
    """An encounter record"""

    id: str = Field(..., description="Treatment ID")
    pid: str = Field(..., description="Patient ID")

    creation_date: datetime.datetime = Field(..., description="Database creation date")
    update_date: Optional[datetime.datetime] = Field(
        ..., description="Database update date"
    )
    # idx: Currently unused
    externalid: Optional[str] = Field(None, description="External session ID")

    # Encounter time
    fromtime: Optional[datetime.date] = Field(None, description="Encounter start date")
    totime: Optional[datetime.date] = Field(None, description="Encounter end date")

    # Encounter information
    encounternumber: Optional[str] = Field(None, description="Encounter number")
    encountertype: Optional[str] = Field(None, description="Encounter type")

    # Clinician
    admittingcliniciancode: Optional[str] = Field(
        None, description="Clinicial code. Rarely used."
    )
    admittingcliniciancodestd: Optional[str] = Field(
        None, description="Clinicial code standard. Rarely used."
    )
    admittingcliniciandesc: Optional[str] = Field(
        None, description="Clinician description"
    )

    # Admit reason
    admitreasoncode: Optional[str] = Field(None, description="Admission reason code")
    admitreasoncodestd: Optional[str] = Field(
        None, description="Admission reason code standard"
    )
    admitreasondesc: Optional[str] = Field(
        None, description="Admission reason description"
    )

    # Admission source
    admissionsourcecode: Optional[str] = Field(
        None, description="Admission source code"
    )
    admissionsourcecodestd: Optional[str] = Field(
        None, description="Admission source code standard"
    )
    admissionsourcedesc: Optional[str] = Field(
        None, description="Admission source description"
    )

    # Discharge reason
    dischargereasoncode: Optional[str] = Field(
        None, description="Discharge reason code"
    )
    dischargereasoncodestd: Optional[str] = Field(
        None, description="Discharge reason code standard"
    )
    dischargereasondesc: Optional[str] = Field(
        None, description="Discharge reason description"
    )

    # Discharge location
    dischargelocationcode: Optional[str] = Field(
        None, description="Discharge location code"
    )
    dischargelocationcodestd: Optional[str] = Field(
        None, description="Discharge location code standard"
    )
    dischargelocationdesc: Optional[str] = Field(
        None, description="Discharge location description"
    )

    # Health care facility
    healthcarefacilitycode: Optional[str] = Field(
        None, description="Health care facility code"
    )
    healthcarefacilitycodestd: Optional[str] = Field(
        None, description="Health care facility code standard"
    )
    healthcarefacilitydesc: Optional[str] = Field(
        None, description="Health care facility description"
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

    visitdescription: Optional[str] = Field(None, description="Visit description")

    # updatedon: Currently unused
    # actioncode: Currently unused
