import datetime
from typing import List

from .base import ORMModel
from .patient import PatientSchema


class ProgramMembershipSchema(ORMModel):
    program_name: str
    from_time: datetime.datetime
    to_time: datetime.datetime


class PatientRecordShortSchema(ORMModel):
    pid: str
    sendingfacility: str
    sendingextract: str
    localpatientid: str
    ukrdcid: str
    repository_creation_date: datetime.datetime
    repository_update_date: datetime.datetime


class PatientRecordSchema(PatientRecordShortSchema):
    program_memberships: List[ProgramMembershipSchema]
    patient: PatientSchema
