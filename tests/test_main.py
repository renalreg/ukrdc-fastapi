def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}


def test_patient_records(client):
    response = client.get("/viewer/records?ni=999999999")
    assert response.status_code == 200
    assert response.json() == [
        {
            "localpatientid": "00000000A",
            "pid": "PYTEST01:PV:00000000A",
            "repository_creation_date": "2020-03-16T00:00:00",
            "repository_update_date": "2021-01-21T00:00:00",
            "sendingextract": "PV",
            "sendingfacility": "PATIENT_RECORD_SENDING_FACILITY_1",
            "ukrdcid": "000000000",
        }
    ]
