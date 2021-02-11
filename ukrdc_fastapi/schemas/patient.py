import datetime
from typing import List

from .base import ORMModel


class NameSchema(ORMModel):
    given: str
    family: str


class NumberSchema(ORMModel):
    patientid: str
    organization: str
    numbertype: str


class AddressSchema(ORMModel):
    from_time: datetime.datetime
    to_time: datetime.datetime
    street: str
    town: str
    county: str
    postcode: str
    country_description: str


class PatientSchema(ORMModel):
    # names: List[NameSchema]
    numbers: List[NumberSchema]
    # addresses: List[AddressSchema]

    birth_time: datetime.date
    death_time: datetime.date
    gender: str
