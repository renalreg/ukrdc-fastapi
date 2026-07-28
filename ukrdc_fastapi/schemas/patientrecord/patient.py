import datetime
from typing import Literal, Optional

from pydantic import Field

from ..base import OrmModel

GenderType = Literal["1", "2", "9"]


class NameSchema(OrmModel):
    """Patient name"""

    given: str = Field(..., description="Given name")
    family: str = Field(..., description="Family name")
    nameuse: str | None = Field(None, description="Name use code")


class NumberSchema(OrmModel):
    """Patient identifier number, e.g. NHS number, or internal hospital number"""

    patientid: str = Field(..., description="Patient number")
    organization: str = Field(..., description="Patient number organization code")
    numbertype: str = Field(..., description="Patient number type code")


class AddressSchema(OrmModel):
    """Patient address"""

    from_time: datetime.date | None = Field(None, description="Address start date")
    to_time: datetime.date | None = Field(None, description="Address end date")
    street: str | None = Field(None, description="Street address")
    town: str | None = Field(None, description="Town")
    county: str | None = Field(None, description="County")
    postcode: str | None = Field(None, description="Postcode")

    country_code: str | None = Field(None, description="Country code")
    country_code_std: str | None = Field(None, description="Country code standard")
    country_description: str | None = Field(None, description="Country description")

    addressuse: str | None = Field(None, description="Address use code")


class ContactDetailSchema(OrmModel):
    """Patient contact detail"""

    use: str | None = Field(None, description="Contact detail use code")
    value: str | None = Field(None, description="Contact detail value")
    commenttext: str | None = Field(None, description="Contact detail comment")


class GPInfo(OrmModel):
    """Patient GP information"""

    code: str = Field(..., description="GP code")
    gpname: str | None = Field(None, description="GP name")
    street: str | None = Field(None, description="GP street address")
    postcode: str | None = Field(None, description="GP postcode")
    contactvalue: str | None = Field(None, description="GP contact value")
    type: str | None = Field(None, description="GP type code")


class FamilyDoctorSchema(OrmModel):
    """Patient family doctor information"""

    id: str = Field(..., description="Family doctor ID")
    gpname: str | None = Field(None, description="GP name")

    gpid: str | None = Field(None, description="GP code")
    gp_info: GPInfo | None = Field(None, description="GP information")

    gppracticeid: str | None = Field(None, description="GP practice code")
    gp_practice_info: GPInfo | None = Field(None, description="GP practice information")

    addressuse: str | None = Field(None, description="Address use code")
    fromtime: datetime.datetime | None = Field(None, description="Start date")
    totime: datetime.datetime | None = Field(None, description="End date")
    street: str | None = Field(None, description="Street address")
    town: str | None = Field(None, description="Town")
    county: str | None = Field(None, description="County")
    postcode: str | None = Field(None, description="Postcode")
    countrycode: str | None = Field(None, description="Country code")
    countrycodestd: str | None = Field(None, description="Country code standard")
    countrydesc: str | None = Field(None, description="Country description")
    contactuse: str | None = Field(None, description="Contact use code")
    contactvalue: str | None = Field(None, description="Contact value")
    email: str | None = Field(None, description="Email address")
    commenttext: str | None = Field(None, description="Comment")


class PatientSchema(OrmModel):
    """Patient information"""

    names: list[NameSchema] = Field(..., description="Patient names")
    numbers: list[NumberSchema] = Field(..., description="Patient numbers")
    addresses: list[AddressSchema] = Field(..., description="Patient addresses")
    contact_details: list[ContactDetailSchema] = Field(
        ..., description="Contact details"
    )

    familydoctor: FamilyDoctorSchema | None = Field(None, description="Family doctor")

    birth_time: datetime.datetime = Field(..., description="Patient birth date")
    death_time: datetime.datetime | None = Field(None, description="Patient death date")
    gender: GenderType = Field(..., description="Patient gender code")

    ethnic_group_code: str | None = Field(None, description="Patient ethnic group code")
    ethnic_group_description: str | None = Field(
        None, description="Patient ethnic group description"
    )
