import datetime

from ukrdc_fastapi.models.ukrdc import PatientRecord
from ukrdc_fastapi.schemas.patientrecord import PatientRecordSchema


def test_patient_record(ukrdc3_session):
    pid = "PYTEST01:PV:00000000A"
    record = ukrdc3_session.query(PatientRecord).filter(PatientRecord.pid == pid).first()

    model = PatientRecordSchema.from_orm(record)
    assert model.dict() == {
        "pid": "PYTEST01:PV:00000000A",
        "sendingfacility": "PATIENT_RECORD_SENDING_FACILITY_1",
        "sendingextract": "PV",
        "localpatientid": "00000000A",
        "ukrdcid": "000000000",
        "repository_creation_date": datetime.datetime(2020, 3, 16, 0, 0),
        "repository_update_date": datetime.datetime(2021, 1, 21, 0, 0),
        "program_memberships": [],
        "patient": {
            "names": [{"given": "Patrick", "family": "Star"}],
            "numbers": [{"patientid": "999999999", "organization": "NHS", "numbertype": "NI"}],
            "addresses": [
                {
                    "from_time": None,
                    "to_time": None,
                    "street": "120 Conch Street",
                    "town": "Bikini Bottom",
                    "county": "Bikini County",
                    "postcode": "XX0 1AA",
                    "country_description": "Pacific Ocean",
                },
                {
                    "from_time": None,
                    "to_time": None,
                    "street": "121 Conch Street",
                    "town": "Bikini Bottom",
                    "county": "Bikini County",
                    "postcode": "XX0 1AA",
                    "country_description": "Pacific Ocean",
                },
            ],
            "birth_time": datetime.date(1984, 3, 17),
            "death_time": None,
            "gender": "1",
        },
    }
