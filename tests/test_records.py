import re

from ukrdc_fastapi.schemas.errors import MessageSchema as ErrorMessageSchema
from ukrdc_fastapi.schemas.laborder import LabOrderSchema, ResultItemSchema
from ukrdc_fastapi.schemas.patientrecord import (
    PatientRecordSchema,
    PatientRecordShortSchema,
)


def test_records(client):
    response = client.get("/api/patientrecords")
    assert response.status_code == 200
    records = [PatientRecordShortSchema(**item) for item in response.json()["items"]]
    record_ids = {record.pid for record in records}
    assert record_ids == {"PYTEST01:PV:00000000A"}


def test_record(client):
    response = client.get("/api/patientrecords/PYTEST01:PV:00000000A")
    assert response.status_code == 200
    record = PatientRecordSchema(**response.json())
    assert record.pid == "PYTEST01:PV:00000000A"


# Record errors

"""
def test_record_errors(client):
    response = client.get("/api/patientrecords/PYTEST01:PV:00000000A/errors")
    assert response.status_code == 200
    errors = [ErrorMessageSchema(**item) for item in response.json()]
    assert len(errors) == 1
    assert errors[0].id == 1
"""

# Record lab orders


def test_record_laborders(client):
    response = client.get("/api/patientrecords/PYTEST01:PV:00000000A/laborders")
    assert response.status_code == 200
    orders = [LabOrderSchema(**item) for item in response.json()]
    assert len(orders) == 1
    assert orders[0].id == "LABORDER1"


# Record result items


def test_record_resultitems(client):
    response = client.get("/api/patientrecords/PYTEST01:PV:00000000A/resultitems")
    assert response.status_code == 200
    results = [ResultItemSchema(**item) for item in response.json()["items"]]
    assert len(results) == 1
    assert results[0].id == "RESULTITEM1"


# Record observations


def test_record_observations(client):
    response = client.get("/api/patientrecords/PYTEST01:PV:00000000A/observations")
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


def test_record_observations_missing(client):
    response = client.get("/api/patientrecords/MISSING_PID/observations")
    assert response.json()["items"] == []


# Record medications


def test_record_medications(client):
    response = client.get("/api/patientrecords/PYTEST01:PV:00000000A/medications")
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
    response = client.get("/api/patientrecords/MISSING_PID/medications")
    assert response.json() == []


# Record surveys


def test_record_surveys(client):
    response = client.get("/api/patientrecords/PYTEST01:PV:00000000A/surveys")
    assert response.status_code == 200
    assert response.json() == [
        {
            "questions": [
                {
                    "id": "QUESTION1",
                    "questiontypecode": "TYPECODE1",
                    "response": "RESPONSE1",
                    "questionGroup": None,
                    "questionType": None,
                    "responseText": None,
                },
                {
                    "id": "QUESTION2",
                    "questiontypecode": "TYPECODE2",
                    "response": "RESPONSE2",
                    "questionGroup": None,
                    "questionType": None,
                    "responseText": None,
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
    response = client.get("/api/patientrecords/MISSING_PID/surveys")
    assert response.json() == []


# Record export-data


def test_record_export_data(client, httpx_session):
    response = client.post(
        "/api/patientrecords/PYTEST01:PV:00000000A/export/pv/", json={}
    )
    assert response.json() == {
        "message": "<result><pid>PYTEST01:PV:00000000A</pid><tests>FULL</tests><documents>FULL</documents></result>",
        "status": "success",
    }


def test_record_export_tests(client, httpx_session):
    response = client.post(
        "/api/patientrecords/PYTEST01:PV:00000000A/export/pv-tests/", json={}
    )
    assert response.json() == {
        "status": "success",
        "message": "<result><pid>PYTEST01:PV:00000000A</pid><tests>FULL</tests></result>",
    }


def test_record_export_docs(client, httpx_session):
    response = client.post(
        "/api/patientrecords/PYTEST01:PV:00000000A/export/pv-docs/", json={}
    )
    assert response.json() == {
        "message": "<result><pid>PYTEST01:PV:00000000A</pid><documents>FULL</documents></result>",
        "status": "success",
    }


def test_record_export_radar(client, httpx_session):
    response = client.post(
        "/api/patientrecords/PYTEST01:PV:00000000A/export/radar/", json={}
    )
    assert response.json() == {
        "message": "<result><pid>PYTEST01:PV:00000000A</pid></result>",
        "status": "success",
    }
