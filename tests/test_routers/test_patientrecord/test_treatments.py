def test_record_treatments(client):
    response = client.get("/api/v1/patientrecords/PYTEST01:PV:00000000A/treatments")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "TREATMENT1",
            "pid": "PYTEST01:PV:00000000A",
            "fromTime": "2019-03-16",
            "toTime": None,
            "admitReasonCode": "1",
            "admissionSourceCodeStd": "CF_RR7_TREATMENT",
            "healthCareFacilityCode": "TEST_SENDING_FACILITY_1",
            "healthCareFacilityCodeStd": "ODS",
        },
        {
            "id": "TREATMENT2",
            "pid": "PYTEST01:PV:00000000A",
            "fromTime": "2019-03-16",
            "toTime": "9999-03-16",
            "admitReasonCode": "1",
            "admissionSourceCodeStd": "CF_RR7_TREATMENT",
            "healthCareFacilityCode": "TEST_SENDING_FACILITY_1",
            "healthCareFacilityCodeStd": "ODS",
        },
    ]
