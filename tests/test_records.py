def test_record(client):
    response = client.get("/records/PYTEST01:PV:00000000A")
    assert response.status_code == 200
    assert response.json() == {
        "pid": "PYTEST01:PV:00000000A",
        "href": "http://testserver/records/PYTEST01:PV:00000000A",
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


def test_record_missing(client):
    response = client.get("/records/MISSING_PID")
    assert response.status_code == 404
    assert response.json() == {"detail": "Record not found"}


def test_records(client):
    response = client.get("/records?ni=999999999")
    assert response.status_code == 200
    assert response.json() == [
        {
            "localpatientid": "00000000A",
            "pid": "PYTEST01:PV:00000000A",
            "href": "http://testserver/records/PYTEST01:PV:00000000A",
            "repository_creation_date": "2020-03-16T00:00:00",
            "repository_update_date": "2021-01-21T00:00:00",
            "sendingextract": "PV",
            "sendingfacility": "PATIENT_RECORD_SENDING_FACILITY_1",
            "ukrdcid": "000000000",
        }
    ]


def test_records_no_ni(client):
    response = client.get("/records")
    assert response.status_code == 422


def test_records_missing_ni(client):
    response = client.get("/records?ni=111111111")
    assert response.json() == []


# Record lab orders


def test_record_laborders(client):
    response = client.get("/records/PYTEST01:PV:00000000A/laborders")
    assert response.status_code == 200
    assert response.json() == [
        {
            "entered_at": None,
            "entered_at_description": None,
            "id": "LABORDER1",
            "specimen_collected_time": "2020-03-16T00:00:00",
            "href": "http://testserver/laborders/LABORDER1",
        }
    ]


def test_record_laborders_missing(client):
    response = client.get("/records/MISSING_PID/laborders")
    assert response.json() == []


# Record observations


def test_record_observations(client):
    response = client.get("/records/PYTEST01:PV:00000000A/observations")
    assert response.status_code == 200
    assert response.json() == [
        {
            "entered_at": None,
            "entered_at_description": None,
            "observation_desc": "OBSERVATION_SYS_1_DESC",
            "observation_time": "2020-03-16T11:35:00",
            "observation_units": "OBSERVATION_SYS_1_UNITS",
            "observation_value": "OBSERVATION_SYS_1_VALUE",
            "pre_post": None,
        },
        {
            "entered_at": None,
            "entered_at_description": None,
            "observation_desc": "OBSERVATION_DIA_1_DESC",
            "observation_time": "2020-03-16T11:30:00",
            "observation_units": "OBSERVATION_DIA_1_UNITS",
            "observation_value": "OBSERVATION_DIA_1_VALUE",
            "pre_post": None,
        },
        {
            "entered_at": None,
            "entered_at_description": None,
            "observation_desc": "OBSERVATION_DESC",
            "observation_time": "2020-03-16T00:00:00",
            "observation_units": "OBSERVATION_UNITS",
            "observation_value": "OBSERVATION_VALUE",
            "pre_post": None,
        },
    ]


def test_record_observations_missing(client):
    response = client.get("/records/MISSING_PID/observations")
    assert response.json() == []


# Record medications


def test_record_medications(client):
    response = client.get("/records/PYTEST01:PV:00000000A/medications")
    assert response.status_code == 200
    assert response.json() == [
        {
            "from_time": "2019-03-16T00:00:00",
            "to_time": None,
            "drug_product_generic": "DRUG_PRODUCT_GENERIC",
            "comment": None,
            "entering_organization_code": None,
            "entering_organization_description": None,
        },
        {
            "from_time": "2019-03-16T00:00:00",
            "to_time": "9999-03-16T00:00:00",
            "drug_product_generic": "DRUG_PRODUCT_GENERIC_2",
            "comment": None,
            "entering_organization_code": None,
            "entering_organization_description": None,
        },
    ]


def test_record_medications_missing(client):
    response = client.get("/records/MISSING_PID/medications")
    assert response.json() == []


# Record surveys


def test_record_surveys(client):
    response = client.get("/records/PYTEST01:PV:00000000A/surveys")
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
    response = client.get("/records/MISSING_PID/surveys")
    assert response.json() == []


# Record export-data


def test_record_export_data(client):
    response = client.post(
        "/records/PYTEST01:PV:00000000A/export-data",
        json={"data": "FULL_PV_TESTS_EXTRACT_TEMPLATE", "path": "/", "mirth": False},
    )
    assert response.json() == {
        "message": "<result><pid>PYTEST01:PV:00000000A</pid><tests>FULL</tests></result>",
        "status": "ignored",
    }


def test_record_export_data_error(client):
    response = client.post(
        "/records/PYTEST01:PV:00000000A/export-data",
        json={"data": "FULL_PV_TESTS_EXTRACT_TEMPLATE", "path": "/", "mirth": True},
    )
    assert response.status_code == 502


def test_record_export_data_invalid_template(client):
    response = client.post(
        "/records/PYTEST01:PV:00000000A/export-data",
        json={"data": "INVALID", "path": "/", "mirth": True},
    )
    assert response.status_code == 400
