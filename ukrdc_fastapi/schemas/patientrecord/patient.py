import datetime
from typing import Literal, Optional

from pydantic import Field

from ..base import OrmModel

GenderType = Literal["1", "2", "9"]


class NameSchema(OrmModel):
    """Patient name"""

    given: str = Field(..., description="Given name")
    family: str = Field(..., description="Family name")
    nameuse: Optional[str] = Field(None, description="Name use code")


class NumberSchema(OrmModel):
    """Patient identifier number, e.g. NHS number, or internal hospital number"""

    patientid: str = Field(..., description="Patient number")
    organization: str = Field(..., description="Patient number organization code")
    numbertype: str = Field(..., description="Patient number type code")


class AddressSchema(OrmModel):
    """Patient address"""

    from_time: Optional[datetime.date] = Field(None, description="Address start date")
    to_time: Optional[datetime.date] = Field(None, description="Address end date")
    street: Optional[str] = Field(None, description="Street address")
    town: Optional[str] = Field(None, description="Town")
    county: Optional[str] = Field(None, description="County")
    postcode: Optional[str] = Field(None, description="Postcode")

    country_code: Optional[str] = Field(None, description="Country code")
    country_code_std: Optional[str] = Field(None, description="Country code standard")
    country_description: Optional[str] = Field(None, description="Country description")

    addressuse: Optional[str] = Field(None, description="Address use code")


class ContactDetailSchema(OrmModel):
    """Patient contact detail"""

    use: Optional[str] = Field(None, description="Contact detail use code")
    value: Optional[str] = Field(None, description="Contact detail value")
    commenttext: Optional[str] = Field(None, description="Contact detail comment")


class GPInfo(OrmModel):
    """Patient GP information"""

    code: str = Field(..., description="GP code")
    gpname: Optional[str] = Field(None, description="GP name")
    street: Optional[str] = Field(None, description="GP street address")
    postcode: Optional[str] = Field(None, description="GP postcode")
    contactvalue: Optional[str] = Field(None, description="GP contact value")
    type: Optional[str] = Field(None, description="GP type code")


class FamilyDoctorSchema(OrmModel):
    """Patient family doctor information"""

    id: str = Field(..., description="Family doctor ID")
    gpname: Optional[str] = Field(None, description="GP name")

    gpid: Optional[str] = Field(None, description="GP code")
    gp_info: Optional[GPInfo] = Field(None, description="GP information")

    gppracticeid: Optional[str] = Field(None, description="GP practice code")
    gp_practice_info: Optional[GPInfo] = Field(
        None, description="GP practice information"
    )

    addressuse: Optional[str] = Field(None, description="Address use code")
    fromtime: Optional[datetime.datetime] = Field(None, description="Start date")
    totime: Optional[datetime.datetime] = Field(None, description="End date")
    street: Optional[str] = Field(None, description="Street address")
    town: Optional[str] = Field(None, description="Town")
    county: Optional[str] = Field(None, description="County")
    postcode: Optional[str] = Field(None, description="Postcode")
    countrycode: Optional[str] = Field(None, description="Country code")
    countrycodestd: Optional[str] = Field(None, description="Country code standard")
    countrydesc: Optional[str] = Field(None, description="Country description")
    contactuse: Optional[str] = Field(None, description="Contact use code")
    contactvalue: Optional[str] = Field(None, description="Contact value")
    email: Optional[str] = Field(None, description="Email address")
    commenttext: Optional[str] = Field(None, description="Comment")


class PatientSchema(OrmModel):
    """Patient information"""

    names: list[NameSchema] = Field(..., description="Patient names")
    numbers: list[NumberSchema] = Field(..., description="Patient numbers")
    addresses: list[AddressSchema] = Field(..., description="Patient addresses")
    contact_details: list[ContactDetailSchema] = Field(
        ..., description="Contact details"
    )

    familydoctor: Optional[FamilyDoctorSchema] = Field(
        None, description="Family doctor"
    )

    birth_time: datetime.datetime = Field(..., description="Patient birth date")
    death_time: Optional[datetime.datetime] = Field(
        None, description="Patient death date"
    )
    gender: GenderType = Field(..., description="Patient gender code")

    ethnic_group_code: Optional[str] = Field(
        None, description="Patient ethnic group code"
    )
    ethnic_group_description: Optional[str] = Field(
        None, description="Patient ethnic group description"
    )
