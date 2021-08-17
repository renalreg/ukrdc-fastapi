def test_record_treatments(client):
    response = client.get("/api/v1/patientrecords/PYTEST01:PV:00000000A/treatments")
    assert response.status_code == 200
    print(response.json())
    assert response.json() == [
        {
            "id": "TREATMENT1",
            "fromTime": "2019-03-16",
            "toTime": None,
            "admitReasonCode": "1",
            "admitReasonCodeStd": None,
            "admitReasonDesc": None,
            "dischargeReasonCode": None,
            "dischargeReasonCodeStd": None,
            "dischargeReasonDesc": None,
            "healthCareFacilityCode": "TEST_SENDING_FACILITY_1",
        },
        {
            "id": "TREATMENT2",
            "fromTime": "2019-03-16",
            "toTime": "9999-03-16",
            "admitReasonCode": "1",
            "admitReasonCodeStd": None,
            "admitReasonDesc": None,
            "dischargeReasonCode": None,
            "dischargeReasonCodeStd": None,
            "dischargeReasonDesc": None,
            "healthCareFacilityCode": "TEST_SENDING_FACILITY_1",
        },
    ]
