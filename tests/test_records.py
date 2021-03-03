def test_record(client):
    response = client.get("/patientrecords/PYTEST01:PV:00000000A")
    assert response.status_code == 200
    assert response.json() == {
        "pid": "PYTEST01:PV:00000000A",
        "sendingfacility": "PATIENT_RECORD_SENDING_FACILITY_1",
        "sendingextract": "PV",
        "localpatientid": "00000000A",
        "ukrdcid": "000000000",
        "repositoryCreationDate": "2020-03-16T00:00:00",
        "repositoryUpdateDate": "2021-01-21T00:00:00",
        "links": {
            "self": "/patientrecords/PYTEST01:PV:00000000A",
            "laborders": "/patientrecords/PYTEST01:PV:00000000A/laborders",
            "observations": "/patientrecords/PYTEST01:PV:00000000A/observations",
            "medications": "/patientrecords/PYTEST01:PV:00000000A/medications",
            "surveys": "/patientrecords/PYTEST01:PV:00000000A/surveys",
            "export-data": "/patientrecords/PYTEST01:PV:00000000A/export-data",
        },
        "programMemberships": [],
        "patient": {
            "names": [{"given": "Patrick", "family": "Star"}],
            "numbers": [
                {"patientid": "999999999", "organization": "NHS", "numbertype": "NI"}
            ],
            "addresses": [
                {
                    "fromTime": None,
                    "toTime": None,
                    "street": "120 Conch Street",
                    "town": "Bikini Bottom",
                    "county": "Bikini County",
                    "postcode": "XX0 1AA",
                    "countryDescription": "Pacific Ocean",
                },
                {
                    "fromTime": None,
                    "toTime": None,
                    "street": "121 Conch Street",
                    "town": "Bikini Bottom",
                    "county": "Bikini County",
                    "postcode": "XX0 1AA",
                    "countryDescription": "Pacific Ocean",
                },
            ],
            "birthTime": "1984-03-17",
            "deathTime": None,
            "gender": "1",
        },
    }


def test_record_missing(client):
    response = client.get("/patientrecords/MISSING_PID")
    assert response.status_code == 404
    assert response.json() == {"detail": "Record not found"}


def test_records(client):
    response = client.get("/patientrecords?ni=999999999")
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "localpatientid": "00000000A",
            "pid": "PYTEST01:PV:00000000A",
            "links": {
                "self": "/patientrecords/PYTEST01:PV:00000000A",
                "laborders": "/patientrecords/PYTEST01:PV:00000000A/laborders",
                "observations": "/patientrecords/PYTEST01:PV:00000000A/observations",
                "medications": "/patientrecords/PYTEST01:PV:00000000A/medications",
                "surveys": "/patientrecords/PYTEST01:PV:00000000A/surveys",
                "export-data": "/patientrecords/PYTEST01:PV:00000000A/export-data",
            },
            "repositoryCreationDate": "2020-03-16T00:00:00",
            "repositoryUpdateDate": "2021-01-21T00:00:00",
            "sendingextract": "PV",
            "sendingfacility": "PATIENT_RECORD_SENDING_FACILITY_1",
            "ukrdcid": "000000000",
        }
    ]


def test_records_no_ni(client):
    response = client.get("/patientrecords")
    assert response.status_code == 200


def test_records_missing_ni(client):
    response = client.get("/patientrecords?ni=111111111")
    assert response.json()["items"] == []


# Record lab orders


def test_record_laborders(client):
    response = client.get("/patientrecords/PYTEST01:PV:00000000A/laborders")
    assert response.status_code == 200
    assert response.json() == [
        {
            "enteredAt": None,
            "enteredAtDescription": None,
            "id": "LABORDER1",
            "links": {"self": "/laborders/LABORDER1"},
            "specimenCollectedTime": "2020-03-16T00:00:00",
        }
    ]


def test_record_laborders_missing(client):
    response = client.get("/patientrecords/MISSING_PID/laborders")
    assert response.json() == []


# Record observations


def test_record_observations(client):
    response = client.get("/patientrecords/PYTEST01:PV:00000000A/observations")
    assert response.status_code == 200
    assert response.json() == [
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


def test_record_observations_missing(client):
    response = client.get("/patientrecords/MISSING_PID/observations")
    assert response.json() == []


# Record medications


def test_record_medications(client):
    response = client.get("/patientrecords/PYTEST01:PV:00000000A/medications")
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


def test_record_medications_missing(client):
    response = client.get("/patientrecords/MISSING_PID/medications")
    assert response.json() == []


# Record surveys


def test_record_surveys(client):
    response = client.get("/patientrecords/PYTEST01:PV:00000000A/surveys")
    assert response.status_code == 200
    assert response.json() == [
        {
            "questions": [
                {
                    "id": "QUESTION1",
                    "questiontypecode": "TYPECODE1",
                    "response": "RESPONSE1",
                },
                {
                    "id": "QUESTION2",
                    "questiontypecode": "TYPECODE2",
                    "response": "RESPONSE2",
                },
            ],
            "scores": [
                {"id": "SCORE1", "value": "SCORE_VALUE", "scoretypecode": "TYPECODE"}
            ],
            "levels": [
                {"id": "LEVEL1", "value": "LEVEL_VALUE", "leveltypecode": "TYPECODE"}
            ],
            "id": "SURVEY1",
            "pid": "PYTEST01:PV:00000000A",
            "surveytime": "2020-03-16T18:00:00",
            "surveytypecode": "TYPECODE",
            "enteredbycode": "ENTEREDBYCODE",
            "enteredatcode": "ENTEREDATCODE",
        }
    ]


def test_record_surveys_missing(client):
    response = client.get("/patientrecords/MISSING_PID/surveys")
    assert response.json() == []


# Record export-data


def test_record_export_data(client):
    response = client.post(
        "/patientrecords/PYTEST01:PV:00000000A/export-data",
        json={"data": "FULL_PV_TESTS_EXTRACT_TEMPLATE", "path": "/", "mirth": False},
    )
    assert response.json() == {
        "message": "<result><pid>PYTEST01:PV:00000000A</pid><tests>FULL</tests></result>",
        "status": "ignored",
    }


def test_record_export_data_invalid_template(client):
    response = client.post(
        "/patientrecords/PYTEST01:PV:00000000A/export-data",
        json={"data": "INVALID", "path": "/", "mirth": True},
    )
    assert response.status_code == 400
