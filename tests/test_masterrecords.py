from datetime import datetime

from ukrdc_sqla.empi import LinkRecord, MasterRecord

from ukrdc_fastapi.schemas.empi import (
    MasterRecordSchema,
    PersonSchema,
    WorkItemShortSchema,
)
from ukrdc_fastapi.schemas.patientrecord import PatientRecordShortSchema


def test_masterrecords_list(client):
    response = client.get("/api/empi/masterrecords")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1, 2}


def test_masterrecord_detail(client):
    response = client.get("/api/empi/masterrecords/1")
    assert response.status_code == 200
    mr = MasterRecordSchema(**response.json())
    assert mr.id == 1


def test_masterrecord_detail_not_found(client):
    response = client.get("/api/empi/masterrecords/9999")
    assert response.status_code == 404


def test_masterrecord_related(client, jtrace_session):
    # Create a new master record
    master_record_3 = MasterRecord(
        id=3,
        status=0,
        last_updated=datetime(2021, 1, 1),
        date_of_birth=datetime(1980, 12, 12),
        nationalid="119999999",
        nationalid_type="UKRDC",
        effective_date=datetime(2021, 1, 1),
    )

    # Link the new master record to an existing person
    link_record_3 = LinkRecord(
        id=3,
        person_id=1,
        master_id=3,
        link_type=0,
        link_code=0,
        last_updated=datetime(2020, 3, 16),
    )

    # Person 3 now has 2 master records we want to merge
    jtrace_session.add(master_record_3)
    jtrace_session.add(link_record_3)
    jtrace_session.commit()

    response = client.get("/api/empi/masterrecords/1/related")
    assert response.status_code == 200

    # Check MR3 is identified as related to MR1
    mrecs = [MasterRecordSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in mrecs}
    assert returned_ids == {3}


def test_masterrecord_workitems(client):
    response = client.get("/api/empi/masterrecords/1/workitems")
    assert response.status_code == 200

    witems = [WorkItemShortSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in witems}
    assert returned_ids == {1, 2}


def test_masterrecord_persons(client):
    response = client.get("/api/empi/masterrecords/1/persons")
    assert response.status_code == 200

    persons = [PersonSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in persons}
    assert returned_ids == {1, 2}


def test_masterrecord_patientrecords(client):
    response = client.get("/api/empi/masterrecords/1/patientrecords")
    assert response.status_code == 200

    records = [PatientRecordShortSchema(**item) for item in response.json()]
    assert len(records) == 1
    assert records[0].pid == "PYTEST01:PV:00000000A"
