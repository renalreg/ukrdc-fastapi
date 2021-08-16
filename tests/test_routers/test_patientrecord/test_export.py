def test_record_export_data(client, httpx_session):
    response = client.post(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/export/pv/", json={}
    )
    assert response.json() == {
        "message": "<result><pid>PYTEST01:PV:00000000A</pid><tests>FULL</tests><documents>FULL</documents></result>",
        "status": "success",
    }


def test_record_export_tests(client, httpx_session):
    response = client.post(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/export/pv-tests/", json={}
    )
    assert response.json() == {
        "status": "success",
        "message": "<result><pid>PYTEST01:PV:00000000A</pid><tests>FULL</tests></result>",
    }


def test_record_export_docs(client, httpx_session):
    response = client.post(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/export/pv-docs/", json={}
    )
    assert response.json() == {
        "message": "<result><pid>PYTEST01:PV:00000000A</pid><documents>FULL</documents></result>",
        "status": "success",
    }


def test_record_export_radar(client, httpx_session):
    response = client.post(
        "/api/v1/patientrecords/PYTEST01:PV:00000000A/export/radar/", json={}
    )
    assert response.json() == {
        "message": "<result><pid>PYTEST01:PV:00000000A</pid></result>",
        "status": "success",
    }
