def test_record_medications(client):
    response = client.get("/api/v1/patientrecords/PYTEST01:PV:00000000A/medications")
    assert response.status_code == 200
    assert response.json() == [
        {
            "fromTime": "2019-03-16T00:00:00",
            "toTime": None,
            "drugProductGeneric": "DRUG_PRODUCT_GENERIC",
            "comment": None,
            "enteringOrganizationCode": None,
            "enteringOrganizationDescription": None,
        },
        {
            "fromTime": "2019-03-16T00:00:00",
            "toTime": "9999-03-16T00:00:00",
            "drugProductGeneric": "DRUG_PRODUCT_GENERIC_2",
            "comment": None,
            "enteringOrganizationCode": None,
            "enteringOrganizationDescription": None,
        },
    ]
