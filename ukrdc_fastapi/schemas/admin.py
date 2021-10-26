from .base import OrmModel


class AdminCountsSchema(OrmModel):
    open_workitems: int
    ukrdc_records: int
    patients_receiving_errors: int
