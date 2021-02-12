def test_record(client):
    response = client.get("/viewer/record/PYTEST01:PV:00000000A")
    assert response.status_code == 200
    assert response.json() == {
        "pid": "PYTEST01:PV:00000000A",
        "sendingfacility": "PATIENT_RECORD_SENDING_FACILITY_1",
        "sendingextract": "PV",
        "localpatientid": "00000000A",
        "ukrdcid": "000000000",
        "repository_creation_date": "2020-03-16T00:00:00",
        "repository_update_date": "2021-01-21T00:00:00",
        "program_memberships": [],
        "patient": {
            "names": [{"given": "Patrick", "family": "Star"}],
            "numbers": [
                {"patientid": "999999999", "organization": "NHS", "numbertype": "NI"}
            ],
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
            "birth_time": "1984-03-17",
            "death_time": None,
            "gender": "1",
        },
    }


def test_record_no_pid(client):
    response = client.get("/viewer/record/")
    assert response.status_code == 404


def test_record_missing(client):
    response = client.get("/viewer/record/MISSING_PID")
    assert response.status_code == 404
    assert response.json() == {"detail": "Record not found"}
