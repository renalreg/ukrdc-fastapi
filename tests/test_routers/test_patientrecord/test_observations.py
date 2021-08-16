def test_record_observations(client):
    response = client.get("/api/v1/patientrecords/PYTEST01:PV:00000000A/observations")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "enteredAt": None,
            "enteredAtDescription": None,
            "observationDesc": "OBSERVATION_SYS_1_DESC",
            "observationTime": "2020-03-16T11:35:00",
            "observationUnits": "OBSERVATION_SYS_1_UNITS",
            "observationValue": "OBSERVATION_SYS_1_VALUE",
            "prePost": None,
        },
        {
            "enteredAt": None,
            "enteredAtDescription": None,
            "observationDesc": "OBSERVATION_DIA_1_DESC",
            "observationTime": "2020-03-16T11:30:00",
            "observationUnits": "OBSERVATION_DIA_1_UNITS",
            "observationValue": "OBSERVATION_DIA_1_VALUE",
            "prePost": None,
        },
        {
            "enteredAt": None,
            "enteredAtDescription": None,
            "observationDesc": "OBSERVATION_DESC",
            "observationTime": "2020-03-16T00:00:00",
            "observationUnits": "OBSERVATION_UNITS",
            "observationValue": "OBSERVATION_VALUE",
            "prePost": None,
        },
    ]
