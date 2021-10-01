import datetime
from typing import Optional

from .base import OrmModel


class NameSchema(OrmModel):
    given: str
    family: str


class NumberSchema(OrmModel):
    patientid: str
    organization: str
    numbertype: str


class AddressSchema(OrmModel):
    from_time: Optional[datetime.datetime]
    to_time: Optional[datetime.datetime]
    street: Optional[str]
    town: Optional[str]
    county: Optional[str]
    postcode: Optional[str]
    country_description: Optional[str]


class ContactDetailSchema(OrmModel):
    use: Optional[str]
    value: Optional[str]
    commenttext: Optional[str]


class GPInfo(OrmModel):
    code: str
    gpname: Optional[str]
    street: Optional[str]
    postcode: Optional[str]
    contactvalue: Optional[str]
    type: Optional[str]


class FamilyDoctorSchema(OrmModel):
    id: str
    gpname: Optional[str]

    gpid: Optional[str]
    gp_info: Optional[GPInfo]

    gppracticeid: Optional[str]
    gp_practice_info: Optional[GPInfo]

    addressuse: Optional[str]
    fromtime: Optional[datetime.datetime]
    totime: Optional[datetime.datetime]
    street: Optional[str]
    town: Optional[str]
    county: Optional[str]
    postcode: Optional[str]
    countrycode: Optional[str]
    countrycodestd: Optional[str]
    countrydesc: Optional[str]
    contactuse: Optional[str]
    contactvalue: Optional[str]
    email: Optional[str]
    commenttext: Optional[str]


class PatientSchema(OrmModel):
    names: list[NameSchema]
    numbers: list[NumberSchema]
    addresses: list[AddressSchema]
    contact_details: list[ContactDetailSchema]

    familydoctor: Optional[FamilyDoctorSchema]

    birth_time: datetime.date
    death_time: Optional[datetime.date]
    gender: str

    ethnic_group_code: Optional[str]
    ethnic_group_description: Optional[str]
