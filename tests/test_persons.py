from datetime import datetime

from ukrdc_sqla.empi import LinkRecord, MasterRecord

from ukrdc_fastapi.schemas.empi import MasterRecordSchema, PersonSchema


def test_persons_list(client):
    response = client.get("/api/empi/persons")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1, 2, 3, 4}


def test_persons_list_clpid_filter_single(client):
    response = client.get("/api/empi/persons?clpid=PYTEST01:PV:00000000A")
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1}


def test_persons_list_ukrdcid_filter_multiple(client):
    response = client.get(
        "/api/empi/persons?clpid=PYTEST01:PV:00000000A&clpid=987654321"
    )
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert returned_ids == {1, 2}


def test_person_detail(client):
    response = client.get("/api/empi/persons/1")
    assert response.status_code == 200
    person = PersonSchema(**response.json())
    assert person.id == 1


def test_person_detail_not_found(client):
    response = client.get("/api/empi/persons/9999")
    assert response.status_code == 404


def test_person_masterrecords(client, jtrace_session):
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

    response = client.get("/api/empi/persons/1/masterrecords")
    assert response.status_code == 200

    # Check MR3 is identified as related to MR1
    mrecs = [MasterRecordSchema(**item) for item in response.json()]
    returned_ids = {item.id for item in mrecs}
    assert returned_ids == {1, 3}
