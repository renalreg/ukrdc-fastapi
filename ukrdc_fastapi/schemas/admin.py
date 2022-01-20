import datetime

from .base import OrmModel
from .empi import MasterRecordSchema


class AdminCountsSchema(OrmModel):
    open_workitems: int
    UKRDC_records: int
    patients_receiving_errors: int


class MultipleUKRDCIDGroupItem(OrmModel):
    last_updated: datetime.datetime
    master_record: MasterRecordSchema


class MultipleUKRDCIDGroup(OrmModel):
    group_id: int
    records: list[MultipleUKRDCIDGroupItem]


class LastRunTime(OrmModel):
    last_run_time: datetime.datetime


class LastRunTimeFacility(LastRunTime):
    facility: str
