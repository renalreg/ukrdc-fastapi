import datetime
from typing import List, Optional

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
    street: str
    town: str
    county: str
    postcode: str
    country_description: str


class PatientSchema(OrmModel):
    names: List[NameSchema]
    numbers: List[NumberSchema]
    addresses: List[AddressSchema]

    birth_time: datetime.date
    death_time: Optional[datetime.date]
    gender: str
